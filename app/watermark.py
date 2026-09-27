"""
watermark.py
------------
Modul inti watermarking: preprocessing watermark biner, capacity check,
enforce_margin(), embed_watermark(), extract_watermark(), dan
penyimpanan/pembacaan metadata JSON.

Modul ini TIDAK melakukan image I/O (baca/tulis file .png dari disk) --
itu tanggung jawab pipeline.py/main.py nanti. Di sini semua fungsi
bekerja langsung pada numpy array grayscale (nilai float, domain 0-255)
supaya mudah diuji tanpa dependency pada library baca gambar.

Keputusan teknis yang dikunci bersama user:
- Coefficient pair: coeffs[4, 5] (C1) dan coeffs[5, 4] (C2), zero-based,
  didefinisikan sebagai konstanta di sini (COEFF_1_POS, COEFF_2_POS),
  bukan magic number yang tersebar.
- enforce_margin(): metode symmetric midpoint. mid = (C1+C2)/2.
    bit 1 -> C1_new = mid + alpha/2, C2_new = mid - alpha/2
    bit 0 -> C1_new = mid - alpha/2, C2_new = mid + alpha/2
  Ini menjaga C1_new + C2_new == C1 + C2 dan menghasilkan selisih
  |C1_new - C2_new| == alpha (>= alpha terpenuhi).
- Extraction tie-break: C1 >= C2 -> bit 1, selain itu bit 0.
- Block selection memakai app.key.generate_unique_block_sequence
  (TIDAK membuat ulang mekanisme PRNG di modul ini).
- Metadata (non-secret) disimpan sebagai JSON: watermark_shape,
  block_size, coeff_positions, processed_image_size, alpha, n_bits.
  Secret key TIDAK PERNAH disimpan di metadata.
- Preprocessing watermark: grayscale -> threshold tetap (default 127)
  -> biner {0,1}. Ini ASUMSI implementasi karena spesifikasi belum
  mengunci metode binarisasi; threshold bisa diganti user melalui
  parameter, didokumentasikan di sini secara eksplisit (bukan
  keputusan diam-diam).
- Untuk Fase 1 (tanpa attack), extraction memvalidasi bahwa ukuran
  gambar yang diterima PERSIS sama dengan processed_image_size di
  metadata. Sinkronisasi ukuran untuk attack geometris (resize/crop)
  sengaja belum ditangani -- itu akan direview ulang di fase attack.
"""

from __future__ import annotations

import json
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from app.dct import (
    BLOCK_SIZE,
    dct2,
    idct2,
    crop_to_multiple_of_block,
    split_into_blocks,
    reconstruct_from_blocks,
    num_blocks,
)
from app.key import generate_unique_block_sequence, generate_redundant_block_sequence

# Posisi koefisien medium-frequency yang disepakati (zero-based).
# Didefinisikan SEKALI di sini, dipakai di embed & extract -- tidak
# boleh disebar sebagai magic number di tempat lain.
COEFF_1_POS: Tuple[int, int] = (4, 5)
COEFF_2_POS: Tuple[int, int] = (5, 4)

DEFAULT_BINARIZE_THRESHOLD = 127


# ---------------------------------------------------------------------------
# Fase 2 addition (opsional): resync ukuran sebelum extraction.
#
# TIDAK mengubah algoritma DCT/embedding/extraction yang dikunci di
# algoritma.md -- ini murni operasi array (bukan bagian dari "algoritma
# watermarking" itu sendiri), sama seperti scipy.fftpack dipakai sebagai
# operasi dasar di app.dct. Fungsi-fungsi ini TIDAK dipanggil sama sekali
# kecuali extract_watermark() dipanggil secara eksplisit dengan
# on_size_mismatch != "raise" -- default lama (raise) tetap identik
# dengan Fase 1.
# ---------------------------------------------------------------------------

def resize_to_shape(image: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
    """Resize sebuah grayscale image (array, BUKAN file) ke target_shape
    (H, W) memakai interpolasi bicubic. Dipakai untuk resync grid blok
    ketika gambar yang diterima sudah mengalami resize attack (ukuran
    berubah tapi seluruh konten citra masih ada, hanya diskalakan)."""
    target_h, target_w = target_shape
    # cv2.resize menerima dsize sebagai (width, height), kebalikan dari
    # urutan shape numpy (height, width).
    resized = cv2.resize(
        image.astype(np.float64), (target_w, target_h), interpolation=cv2.INTER_CUBIC
    )
    return resized


def _reconstruct_centered_crop_canvas(
    received_image: np.ndarray, target_shape: Tuple[int, int]
) -> Tuple[np.ndarray, int, int]:
    """Menempatkan `received_image` (hasil crop, TIDAK di-resize balik) ke
    tengah kanvas berukuran target_shape, dengan area yang hilang akibat
    crop diisi NaN sebagai penanda "tidak diketahui".

    ASUMSI (didokumentasikan secara eksplisit, bukan diam-diam): crop
    terjadi SIMETRIS dari tengah (mis. auto-crop media sosial yang umum
    memotong rata dari sisi kiri/kanan/atas/bawah). Tanpa asumsi ini,
    watermarking blind secara matematis tidak bisa tahu di offset mana
    crop terjadi.
    """
    target_h, target_w = target_shape
    recv_h, recv_w = received_image.shape

    if recv_h > target_h or recv_w > target_w:
        raise ValueError(
            f"on_size_mismatch='centered_crop' mengasumsikan gambar yang diterima "
            f"lebih kecil atau sama dengan processed_image_size {target_shape}, "
            f"tetapi diterima {received_image.shape}. Gunakan on_size_mismatch='resize' "
            "untuk kasus resize attack."
        )

    offset_h = (target_h - recv_h) // 2
    offset_w = (target_w - recv_w) // 2

    canvas = np.full((target_h, target_w), np.nan, dtype=np.float64)
    canvas[offset_h : offset_h + recv_h, offset_w : offset_w + recv_w] = received_image
    return canvas, offset_h, offset_w


class CapacityError(Exception):
    """Dilempar ketika jumlah bit watermark melebihi kapasitas blok
    yang tersedia pada gambar (setelah preprocessing/crop)."""


# ---------------------------------------------------------------------------
# 1. Preprocessing watermark
# ---------------------------------------------------------------------------

def binarize_watermark(watermark_gray: np.ndarray, threshold: int = DEFAULT_BINARIZE_THRESHOLD) -> np.ndarray:
    """Mengubah watermark grayscale (2D, nilai 0-255) menjadi matriks
    biner {0, 1} memakai threshold tetap.

    ASUMSI implementasi (belum dikunci di spesifikasi): threshold default
    127 dipakai sebagai batas sederhana (>= threshold -> 1). Nilai ini
    dapat diganti lewat parameter `threshold` bila user ingin metode lain.

    Tidak melakukan resize apapun -- dimensi watermark_gray dipertahankan
    apa adanya sebagai watermark_shape.
    """
    if watermark_gray.ndim != 2:
        raise ValueError(f"binarize_watermark() membutuhkan array 2D, dapat shape {watermark_gray.shape}")

    binary = (watermark_gray >= threshold).astype(np.uint8)
    return binary


def watermark_to_bits(binary_watermark: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Flatten watermark biner (2D, {0,1}) menjadi urutan bit 1D
    (row-major), sekaligus mengembalikan shape asli yang WAJIB disimpan
    untuk reconstruction saat extraction."""
    if binary_watermark.ndim != 2:
        raise ValueError(f"watermark_to_bits() membutuhkan array 2D, dapat shape {binary_watermark.shape}")
    shape = binary_watermark.shape
    bits = binary_watermark.flatten().astype(np.uint8)
    return bits, shape


def bits_to_watermark(bits: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    """Kebalikan dari watermark_to_bits(): reshape urutan bit menjadi
    matriks biner {0,1} dengan shape yang diberikan."""
    expected = shape[0] * shape[1]
    if bits.size != expected:
        raise ValueError(
            f"Jumlah bit ({bits.size}) tidak cocok dengan shape {shape} (butuh {expected})"
        )
    return bits.reshape(shape).astype(np.uint8)


# ---------------------------------------------------------------------------
# 2. Capacity check
# ---------------------------------------------------------------------------

def check_capacity(n_bits: int, n_blocks_available: int) -> None:
    """Memvalidasi bahwa jumlah bit watermark tidak melebihi jumlah
    blok yang tersedia. Melempar CapacityError dengan pesan jelas jika
    tidak memenuhi -- TIDAK melakukan auto-resize watermark."""
    if n_bits > n_blocks_available:
        raise CapacityError(
            f"Watermark membutuhkan {n_bits} bit, tetapi gambar hanya menyediakan "
            f"{n_blocks_available} blok {BLOCK_SIZE}x{BLOCK_SIZE} yang tersedia untuk embedding. "
            "Perkecil watermark atau gunakan gambar yang lebih besar -- "
            "sistem tidak melakukan resize watermark secara otomatis."
        )


# ---------------------------------------------------------------------------
# 3. enforce_margin()
# ---------------------------------------------------------------------------

def enforce_margin(c1: float, c2: float, bit: int, alpha: float) -> Tuple[float, float]:
    """Memodifikasi (C1, C2) secara simetris terhadap titik tengahnya
    supaya merepresentasikan `bit` dengan margin minimal `alpha`.

    mid = (C1 + C2) / 2
    bit 1: C1_new = mid + alpha/2, C2_new = mid - alpha/2  (C1_new > C2_new)
    bit 0: C1_new = mid - alpha/2, C2_new = mid + alpha/2  (C1_new < C2_new)

    Properti yang dijamin (dan diuji di unit test):
    - C1_new + C2_new == C1 + C2 (energi total blok pada dua koefisien
      ini dipertahankan -- distorsi minimal).
    - |C1_new - C2_new| == alpha (memenuhi syarat >= alpha).
    """
    if bit not in (0, 1):
        raise ValueError(f"bit harus 0 atau 1, dapat {bit!r}")
    if alpha <= 0:
        raise ValueError(f"alpha harus > 0, dapat {alpha!r}")

    mid = (c1 + c2) / 2.0
    half = alpha / 2.0

    if bit == 1:
        c1_new = mid + half
        c2_new = mid - half
    else:
        c1_new = mid - half
        c2_new = mid + half

    return c1_new, c2_new


# ---------------------------------------------------------------------------
# 4 & 5. Embedding & Extraction
# ---------------------------------------------------------------------------

def embed_watermark(
    image_gray: np.ndarray,
    watermark_binary: np.ndarray,
    key: str,
    alpha: float,
    block_size: int = BLOCK_SIZE,
    binarize_threshold: int = DEFAULT_BINARIZE_THRESHOLD,
    redundancy: int = 1,
) -> Tuple[np.ndarray, Dict]:
    """Menyisipkan watermark biner ke dalam image grayscale.

    Parameters
    ----------
    image_gray: array 2D grayscale (nilai float/uint, domain 0-255).
    watermark_binary: array 2D biner {0,1} (hasil binarize_watermark()).
    key: secret key (string), sumber deterministic block sequence.
    alpha: embedding margin (dipakai oleh enforce_margin()).
    block_size: ukuran blok DCT (default 8).
    binarize_threshold: nilai threshold yang dipakai saat binarize_watermark()
        di luar fungsi ini (dikunci = 127, pixel >= 127 -> 1). Parameter ini
        TIDAK mengubah watermark_binary yang sudah diterima -- hanya
        dicatat apa adanya ke metadata untuk dokumentasi/reproduksibilitas,
        supaya nilainya tidak menjadi magic number tersembunyi.
    redundancy: Fase 2 addition (opsional). Jumlah salinan blok per bit
        watermark. Default 1 == PERSIS perilaku Fase 1 (satu blok per bit,
        generate_unique_block_sequence() dipakai apa adanya). redundancy > 1
        menanam bit yang sama di beberapa blok berbeda (lihat
        app.key.generate_redundant_block_sequence()) supaya extraction bisa
        majority-vote saat sebagian blok hilang akibat cropping murni.
        Meningkatkan redundancy MENGURANGI kapasitas efektif gambar
        (butuh redundancy x n_bits blok) dan sedikit menambah distorsi
        (PSNR turun) karena lebih banyak blok yang diubah.

    Returns
    -------
    (watermarked_image, metadata)
    metadata adalah dict non-secret yang WAJIB disimpan untuk extraction
    (lihat save_metadata()).
    """
    cropped, used_shape = crop_to_multiple_of_block(image_gray, block_size)
    n_blocks = num_blocks(used_shape, block_size)

    bits, wm_shape = watermark_to_bits(watermark_binary)
    n_bits = bits.size

    check_capacity(n_bits * redundancy, n_blocks)

    if redundancy == 1:
        # Identik dengan Fase 1 -- tidak ada perubahan mekanisme sama sekali.
        block_sequence = generate_unique_block_sequence(key, n_blocks, n_bits).reshape(n_bits, 1)
    else:
        block_sequence = generate_redundant_block_sequence(key, n_blocks, n_bits, redundancy)

    blocks = split_into_blocks(cropped, block_size)

    for seq_idx in range(n_bits):
        bit = int(bits[seq_idx])
        for copy_idx in range(redundancy):
            block_idx = int(block_sequence[seq_idx, copy_idx])
            block = blocks[block_idx]

            coeffs = dct2(block)
            c1 = coeffs[COEFF_1_POS]
            c2 = coeffs[COEFF_2_POS]

            c1_new, c2_new = enforce_margin(c1, c2, bit, alpha)
            coeffs[COEFF_1_POS] = c1_new
            coeffs[COEFF_2_POS] = c2_new

            blocks[block_idx] = idct2(coeffs)

    watermarked_image = reconstruct_from_blocks(blocks, used_shape, block_size)

    n_rows = used_shape[0] // block_size
    n_cols = used_shape[1] // block_size

    metadata = {
        "watermark_shape": list(wm_shape),
        "block_size": block_size,
        "coeff_positions": [list(COEFF_1_POS), list(COEFF_2_POS)],
        "processed_image_size": list(used_shape),
        "block_grid_shape": [n_rows, n_cols],
        "alpha": alpha,
        "n_bits": int(n_bits),
        "redundancy": redundancy,
        "binarize_threshold": binarize_threshold,
    }

    return watermarked_image, metadata


def extract_watermark(
    watermarked_image_gray: np.ndarray,
    key: str,
    metadata: Dict,
    on_size_mismatch: str = "raise",
) -> np.ndarray:
    """Mengekstraksi watermark dari gambar watermarked, secara BLIND
    (tidak membutuhkan original image).

    Parameters
    ----------
    watermarked_image_gray: array 2D grayscale dari gambar yang akan
        diekstrak.
    key: secret key yang SAMA dengan yang dipakai saat embedding.
    metadata: dict metadata non-secret (lihat embed_watermark()/load_metadata()).
    on_size_mismatch: Fase 2 addition (opsional). Menentukan apa yang
        dilakukan ketika ukuran watermarked_image_gray TIDAK PERSIS sama
        dengan metadata["processed_image_size"]:
        - "raise" (DEFAULT -- PERSIS perilaku Fase 1, tidak berubah sama
          sekali): melempar ValueError, seperti sebelumnya.
        - "resize": meresize watermarked_image_gray kembali ke
          processed_image_size (bicubic) sebelum diproses. Cocok untuk
          serangan RESIZE murni (gambar diskalakan, tidak dipotong).
        - "centered_crop": memperlakukan watermarked_image_gray sebagai
          hasil crop SIMETRIS dari tengah (bukan resize), menempatkannya
          kembali ke kanvas seukuran processed_image_size, lalu hanya
          men-decode blok yang seluruh isinya masih ada. Jika
          metadata["redundancy"] > 1, bit dengan sebagian salinan hilang
          tetap bisa didekode lewat majority vote dari salinan yang
          selamat; bit yang SEMUA salinannya hilang akan default ke 0
          (keterbatasan yang didokumentasikan, akan tampak sebagai error
          di BER).

    Returns
    -------
    extracted watermark, array 2D biner {0,1} dengan shape sesuai
    metadata["watermark_shape"].
    """
    if on_size_mismatch not in ("raise", "resize", "centered_crop"):
        raise ValueError(
            f"on_size_mismatch harus 'raise', 'resize', atau 'centered_crop', dapat {on_size_mismatch!r}"
        )

    block_size = metadata["block_size"]
    wm_shape = tuple(metadata["watermark_shape"])
    processed_size = tuple(metadata["processed_image_size"])
    coeff1_pos = tuple(metadata["coeff_positions"][0])
    coeff2_pos = tuple(metadata["coeff_positions"][1])
    n_bits = metadata["n_bits"]
    redundancy = int(metadata.get("redundancy", 1))

    default_grid = (processed_size[0] // block_size, processed_size[1] // block_size)
    n_rows, n_cols = tuple(metadata.get("block_grid_shape", list(default_grid)))

    if watermarked_image_gray.ndim != 2:
        raise ValueError(
            f"extract_watermark() membutuhkan grayscale 2D, dapat shape {watermarked_image_gray.shape}"
        )

    received_shape = tuple(watermarked_image_gray.shape)
    availability_mask: Optional[np.ndarray] = None  # None == semua blok tersedia

    if received_shape == processed_size:
        image_for_blocks = watermarked_image_gray
    elif on_size_mismatch == "raise":
        raise ValueError(
            f"Ukuran gambar yang diberikan {watermarked_image_gray.shape} tidak sama dengan "
            f"processed_image_size di metadata {processed_size}. Panggil dengan "
            "on_size_mismatch='resize' (untuk resize attack) atau 'centered_crop' "
            "(untuk crop murni tanpa resize balik) bila ini memang hasil attack."
        )
    elif on_size_mismatch == "resize":
        image_for_blocks = resize_to_shape(watermarked_image_gray, processed_size)
    else:  # "centered_crop"
        canvas, offset_h, offset_w = _reconstruct_centered_crop_canvas(
            watermarked_image_gray, processed_size
        )
        image_for_blocks = canvas
        recv_h, recv_w = received_shape
        availability_mask = np.zeros((n_rows, n_cols), dtype=bool)
        for r in range(n_rows):
            top, bottom = r * block_size, (r + 1) * block_size
            if top < offset_h or bottom > offset_h + recv_h:
                continue
            for c in range(n_cols):
                left, right = c * block_size, (c + 1) * block_size
                if left >= offset_w and right <= offset_w + recv_w:
                    availability_mask[r, c] = True

    n_blocks = num_blocks(processed_size, block_size)
    if redundancy == 1:
        block_sequence = generate_unique_block_sequence(key, n_blocks, n_bits).reshape(n_bits, 1)
    else:
        block_sequence = generate_redundant_block_sequence(key, n_blocks, n_bits, redundancy)

    blocks = split_into_blocks(image_for_blocks, block_size)

    bits = np.zeros(n_bits, dtype=np.uint8)
    for seq_idx in range(n_bits):
        votes = []
        for copy_idx in range(redundancy):
            block_idx = int(block_sequence[seq_idx, copy_idx])
            if availability_mask is not None:
                r, c = block_idx // n_cols, block_idx % n_cols
                if not availability_mask[r, c]:
                    continue  # blok ini hilang akibat crop -- dilewati, bukan dipaksa dibaca dari NaN
            coeffs = dct2(blocks[block_idx])
            c1 = coeffs[coeff1_pos]
            c2 = coeffs[coeff2_pos]
            votes.append(1 if c1 >= c2 else 0)

        if votes:
            ones = sum(votes)
            bits[seq_idx] = 1 if ones * 2 >= len(votes) else 0  # majority vote, seri -> 1
        else:
            # SEMUA salinan bit ini hilang akibat crop -- tidak ada cara
            # blind untuk merekonstruksinya. Default ke 0 (keterbatasan
            # yang didokumentasikan, bukan bug tersembunyi).
            bits[seq_idx] = 0

    return bits_to_watermark(bits, wm_shape)


# ---------------------------------------------------------------------------
# 6. Metadata JSON
# ---------------------------------------------------------------------------

def save_metadata(path: str, metadata: Dict) -> None:
    """Menyimpan metadata non-secret ke file JSON.

    Metadata TIDAK BOLEH pernah berisi secret key -- fungsi ini sengaja
    tidak menerima parameter key sama sekali, untuk mencegah kebocoran
    tidak sengaja.
    """
    if "key" in metadata or "secret_key" in metadata:
        raise ValueError("metadata tidak boleh berisi secret key dalam bentuk apapun")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def load_metadata(path: str) -> Dict:
    """Membaca kembali metadata dari file JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
