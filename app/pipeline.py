"""
pipeline.py
-----------
Orkestrasi modul-modul yang SUDAH ADA (app.dct, app.key, app.watermark,
app.metrics) menjadi tiga alur end-to-end:

1. Embedding : original image (file) -> preprocessing -> embed_watermark()
               -> watermarked image (file) + metadata (file)
2. Extraction: watermarked image (file) + metadata (file) + secret key
               -> extract_watermark() -> extracted watermark (array/file)
3. Evaluation: original image + watermarked image + original watermark
               + extracted watermark -> PSNR, SSIM, NCC, BER

Modul ini TIDAK mengimplementasikan ulang DCT/IDCT, PRNG, embedding,
extraction, atau formula metrics manapun -- semua logika inti tetap di
app.dct / app.key / app.watermark / app.metrics. Yang ditambahkan di
sini hanya:
- Image I/O (baca/tulis file .png/.jpg dari disk) memakai OpenCV.
- Error handling yang jelas untuk kasus operasional (file hilang,
  metadata rusak, dll).
- Fungsi orkestrasi tingkat tinggi (run_embedding_pipeline dkk).

Prinsip yang dijaga ketat:
- run_extraction_pipeline() TIDAK menerima parameter original image
  sama sekali (bukan hanya "tidak dipakai" -- memang tidak ada di
  signature), supaya secara struktural mustahil original image
  dipakai saat extraction.
- Secret key TIDAK PERNAH ditulis ke metadata (delegasi penuh ke
  app.watermark.save_metadata() yang sudah menolak field key).
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

import cv2
import numpy as np

from app.dct import BLOCK_SIZE
from app.watermark import (
    DEFAULT_BINARIZE_THRESHOLD,
    CapacityError,
    binarize_watermark,
    embed_watermark,
    extract_watermark,
    load_metadata,
    save_metadata,
)
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr, calculate_ssim


# ---------------------------------------------------------------------------
# Error taxonomy khusus pipeline (di atas error yang sudah dilempar oleh
# app.watermark / app.key, seperti CapacityError -- yang TIDAK dibungkus
# ulang di sini, hanya diteruskan apa adanya).
# ---------------------------------------------------------------------------

class PipelineError(Exception):
    """Base class untuk error operasional pipeline (I/O, metadata, validasi)."""


class ImageLoadError(PipelineError):
    """File image tidak ditemukan atau gagal dibaca sebagai image."""


class MetadataError(PipelineError):
    """Metadata tidak ditemukan, tidak valid, atau tidak lengkap."""


# ---------------------------------------------------------------------------
# Validasi input & image I/O
# ---------------------------------------------------------------------------

def _validate_key(key: str) -> None:
    if not isinstance(key, str) or len(key.strip()) == 0:
        raise ValueError("secret key tidak boleh kosong")


REQUIRED_METADATA_FIELDS = {
    "watermark_shape",
    "block_size",
    "coeff_positions",
    "processed_image_size",
    "n_bits",
}


def load_grayscale_image(path: str) -> np.ndarray:
    """Membaca file image dari disk sebagai grayscale (float64, domain 0-255).

    Melempar ImageLoadError yang jelas jika file tidak ada atau gagal
    dibaca sebagai image (bukan membiarkan None lolos ke pemrosesan
    berikutnya).
    """
    if not os.path.isfile(path):
        raise ImageLoadError(f"File image tidak ditemukan: {path}")

    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ImageLoadError(
            f"File ditemukan tetapi gagal dibaca sebagai image (format tidak didukung/corrupt): {path}"
        )
    return image.astype(np.float64)


def save_grayscale_image(path: str, image_array: np.ndarray) -> None:
    """Menulis array grayscale (float, domain 0-255) sebagai file image
    8-bit ke disk. Nilai di luar [0,255] di-clip (bukan wrap-around)."""
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    clipped = np.clip(image_array, 0, 255).astype(np.uint8)
    success = cv2.imwrite(path, clipped)
    if not success:
        raise PipelineError(f"Gagal menulis image ke: {path}")


# ---------------------------------------------------------------------------
# Fase 2 addition (opsional): mode warna asli.
#
# Algoritma inti (embed_watermark/extract_watermark di app.watermark) TETAP
# HANYA memproses grayscale 2D -- tidak diubah sama sekali. Yang ditambahkan
# di sini murni pemisahan/penggabungan channel warna di LEVEL PIPELINE:
# citra warna dikonversi ke YCrCb, watermark ditanam HANYA di channel
# luminance (Y) memakai embed_watermark() apa adanya, lalu channel warna
# (Cr, Cb) ASLI (tidak diubah) digabung kembali. Mata manusia jauh lebih
# sensitif terhadap perubahan luminance daripada krominan, jadi ini juga
# teknik standar di literatur watermarking citra berwarna -- bukan
# workaround, dan tidak mengubah satupun mekanisme di algoritma.md.
# ---------------------------------------------------------------------------

def load_color_image(path: str) -> np.ndarray:
    """Membaca file image dari disk sebagai warna (BGR, uint8) -- dipakai
    HANYA oleh mode preserve_color, sejajar dengan load_grayscale_image()."""
    if not os.path.isfile(path):
        raise ImageLoadError(f"File image tidak ditemukan: {path}")

    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(
            f"File ditemukan tetapi gagal dibaca sebagai image (format tidak didukung/corrupt): {path}"
        )
    return image


def save_color_image(path: str, image_bgr_uint8: np.ndarray) -> None:
    """Menulis array warna (BGR, uint8) sebagai file image ke disk."""
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    success = cv2.imwrite(path, image_bgr_uint8)
    if not success:
        raise PipelineError(f"Gagal menulis image ke: {path}")


def split_luma_chroma(image_bgr: np.ndarray) -> "tuple[np.ndarray, np.ndarray, np.ndarray]":
    """BGR (uint8) -> (Y float64, Cr uint8, Cb uint8). Y inilah yang
    diperlakukan persis seperti "grayscale image" di embed_watermark()."""
    ycrcb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YCrCb)
    y = ycrcb[:, :, 0].astype(np.float64)
    cr = ycrcb[:, :, 1]
    cb = ycrcb[:, :, 2]
    return y, cr, cb


def merge_luma_chroma(y: np.ndarray, cr: np.ndarray, cb: np.ndarray) -> np.ndarray:
    """(Y float64, Cr uint8, Cb uint8) -> BGR uint8. Kebalikan split_luma_chroma()."""
    y_uint8 = np.clip(y, 0, 255).astype(np.uint8)
    ycrcb = np.dstack([y_uint8, cr, cb])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def save_binary_watermark_image(path: str, binary_watermark: np.ndarray) -> None:
    """Menulis watermark biner {0,1} sebagai file image (0/255) supaya
    bisa dibuka seperti image biasa untuk keperluan visual/laporan."""
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    image_0_255 = (binary_watermark.astype(np.uint8) * 255)
    success = cv2.imwrite(path, image_0_255)
    if not success:
        raise PipelineError(f"Gagal menulis watermark image ke: {path}")


def load_binary_watermark_image(path: str, threshold: int = DEFAULT_BINARIZE_THRESHOLD) -> np.ndarray:
    """Helper untuk membaca kembali watermark image (mis. hasil
    save_binary_watermark_image) sebagai array biner {0,1}, memakai
    threshold yang sama supaya konsisten dengan binarize_watermark()."""
    gray = load_grayscale_image(path)
    return binarize_watermark(gray, threshold=threshold)


# ---------------------------------------------------------------------------
# 1. Embedding pipeline
# ---------------------------------------------------------------------------

def run_embedding_pipeline(
    original_image_path: str,
    watermark_image_path: str,
    key: str,
    alpha: float,
    output_watermarked_path: str,
    output_metadata_path: str,
    block_size: int = BLOCK_SIZE,
    binarize_threshold: int = DEFAULT_BINARIZE_THRESHOLD,
    redundancy: int = 1,
    preserve_color: bool = False,
) -> Dict:
    """Alur: original image (file) -> preprocessing -> embed_watermark()
    -> watermarked image (file) + metadata (file).

    Tidak mengimplementasikan ulang embedding -- memanggil
    app.watermark.embed_watermark() apa adanya. CapacityError dari sana
    DITERUSKAN tanpa dibungkus ulang.

    preserve_color: Fase 2 addition (opsional, default False = perilaku
        Fase 1 -- image dibaca sebagai grayscale seperti biasa). Jika True,
        original_image_path dibaca sebagai WARNA; watermark ditanam hanya
        di channel Y (luminance), channel warna asli (Cr, Cb) dipertahankan
        utuh lalu digabung kembali sehingga watermarked image tetap
        berwarna. Lihat split_luma_chroma()/merge_luma_chroma().
    """
    _validate_key(key)

    watermark_gray = load_grayscale_image(watermark_image_path)
    watermark_binary = binarize_watermark(watermark_gray, threshold=binarize_threshold)
    if watermark_binary.size == 0:
        raise ValueError(f"Watermark shape tidak valid (kosong): {watermark_image_path}")

    if preserve_color:
        original_color = load_color_image(original_image_path)
        y_channel, cr_channel, cb_channel = split_luma_chroma(original_color)

        # CapacityError (dari embed_watermark -> check_capacity) sengaja
        # TIDAK ditangkap di sini -- diteruskan apa adanya ke pemanggil.
        watermarked_y, metadata = embed_watermark(
            y_channel,
            watermark_binary,
            key,
            alpha,
            block_size=block_size,
            binarize_threshold=binarize_threshold,
            redundancy=redundancy,
        )

        used_h, used_w = metadata["processed_image_size"]
        cr_cropped = cr_channel[:used_h, :used_w]
        cb_cropped = cb_channel[:used_h, :used_w]
        watermarked_image = merge_luma_chroma(watermarked_y, cr_cropped, cb_cropped)

        # Ditandai di metadata supaya run_extraction_pipeline() tahu harus
        # membaca file ini sebagai warna (ambil channel Y-nya lagi), bukan
        # grayscale langsung -- tanpa perlu user mengingat flag lagi saat
        # extract.
        metadata["color_mode"] = "ycrcb_luma_only"

        save_color_image(output_watermarked_path, watermarked_image)
        save_metadata(output_metadata_path, metadata)

        return {
            "watermarked_image": watermarked_image,
            "metadata": metadata,
            "watermarked_image_path": output_watermarked_path,
            "metadata_path": output_metadata_path,
            "original_image": original_color,
            "watermark_binary": watermark_binary,
        }

    original_image = load_grayscale_image(original_image_path)

    # CapacityError (dari embed_watermark -> check_capacity) sengaja TIDAK
    # ditangkap di sini -- diteruskan apa adanya ke pemanggil.
    watermarked_image, metadata = embed_watermark(
        original_image,
        watermark_binary,
        key,
        alpha,
        block_size=block_size,
        binarize_threshold=binarize_threshold,
        redundancy=redundancy,
    )

    save_grayscale_image(output_watermarked_path, watermarked_image)
    save_metadata(output_metadata_path, metadata)

    return {
        "watermarked_image": watermarked_image,
        "metadata": metadata,
        "watermarked_image_path": output_watermarked_path,
        "metadata_path": output_metadata_path,
        # Dikembalikan untuk kemudahan pemanggil menjalankan evaluation
        # setelah embedding (mis. di main.py) -- BUKAN dipakai/dibutuhkan
        # oleh run_extraction_pipeline().
        "original_image": original_image,
        "watermark_binary": watermark_binary,
    }


# ---------------------------------------------------------------------------
# 2. Extraction pipeline (BLIND -- tidak ada original image di signature)
# ---------------------------------------------------------------------------

def run_extraction_pipeline(
    watermarked_image_path: str,
    key: str,
    metadata_path: str,
    output_extracted_watermark_path: Optional[str] = None,
    on_size_mismatch: str = "raise",
) -> Dict:
    """Alur: watermarked image (file) + metadata (file) + secret key
    -> extract_watermark() -> extracted watermark.

    CATATAN STRUKTURAL: fungsi ini SENGAJA tidak memiliki parameter
    original image sama sekali, supaya secara struktural mustahil
    original image ikut dipakai saat extraction (bukan cuma "tidak
    dipakai di dalam", tapi memang tidak bisa diberikan).
    """
    _validate_key(key)

    if not os.path.isfile(metadata_path):
        raise MetadataError(f"File metadata tidak ditemukan: {metadata_path}")

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            raw = f.read()
        metadata = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        raise MetadataError(f"File metadata tidak valid/tidak dapat dibaca: {metadata_path}") from exc

    missing_fields = REQUIRED_METADATA_FIELDS - set(metadata.keys())
    if missing_fields:
        raise MetadataError(
            f"Metadata tidak lengkap, field wajib hilang: {sorted(missing_fields)} (file: {metadata_path})"
        )

    # color_mode ditulis oleh run_embedding_pipeline(..., preserve_color=True)
    # -- kalau ada, file ini WARNA dan yang diekstrak adalah channel Y-nya.
    # Metadata lama (Fase 1, tanpa field ini) otomatis jatuh ke .get() ->
    # None -> path grayscale seperti biasa, tidak berubah sama sekali.
    if metadata.get("color_mode") == "ycrcb_luma_only":
        watermarked_color = load_color_image(watermarked_image_path)
        watermarked_image, _cr, _cb = split_luma_chroma(watermarked_color)
    else:
        watermarked_image = load_grayscale_image(watermarked_image_path)

    # extract_watermark() sendiri yang memvalidasi kecocokan ukuran image
    # terhadap metadata["processed_image_size"]; on_size_mismatch diteruskan
    # apa adanya (default "raise" == perilaku Fase 1, tidak berubah).
    extracted_watermark = extract_watermark(
        watermarked_image, key, metadata, on_size_mismatch=on_size_mismatch
    )

    if output_extracted_watermark_path:
        save_binary_watermark_image(output_extracted_watermark_path, extracted_watermark)

    return {
        "extracted_watermark": extracted_watermark,
        "metadata": metadata,
        "extracted_watermark_path": output_extracted_watermark_path,
    }


# ---------------------------------------------------------------------------
# 3. Evaluation pipeline
# ---------------------------------------------------------------------------

def run_evaluation_pipeline(
    original_image: np.ndarray,
    watermarked_image: np.ndarray,
    original_watermark: np.ndarray,
    extracted_watermark: np.ndarray,
) -> Dict[str, float]:
    """Alur: original image + watermarked image + original watermark +
    extracted watermark -> PSNR + SSIM + NCC + BER.

    Menerima array (bukan path) supaya bisa langsung dipakai baik hasil
    run_embedding_pipeline()/run_extraction_pipeline() (di memory) maupun
    hasil load_grayscale_image()/load_binary_watermark_image() (dari
    disk) -- pemanggil yang menentukan sumbernya, pipeline.py tidak
    memaksa I/O di fungsi ini.

    Pasangan input dijaga ketat sesuai kesepakatan:
    - PSNR, SSIM  -> original_image vs watermarked_image
    - NCC, BER    -> original_watermark vs extracted_watermark
    """
    psnr = calculate_psnr(original_image, watermarked_image)
    ssim = calculate_ssim(original_image, watermarked_image)
    ncc = calculate_ncc(original_watermark, extracted_watermark)
    ber = calculate_ber(original_watermark, extracted_watermark)

    return {
        "psnr": psnr,
        "ssim": ssim,
        "ncc": ncc,
        "ber": ber,
    }
