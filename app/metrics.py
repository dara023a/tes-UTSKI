"""
metrics.py
----------
Empat metrik evaluasi proyek, dengan pasangan input yang TIDAK BOLEH
tertukar:

- calculate_psnr(original_image, watermarked_image) -> image vs image
- calculate_ssim(original_image, watermarked_image) -> image vs image
- calculate_ncc(original_watermark, extracted_watermark) -> watermark vs watermark
- calculate_ber(original_watermark, extracted_watermark) -> watermark bits vs watermark bits

Setiap fungsi memvalidasi shape input agar tidak mungkin salah pasang
(mis. membandingkan image dengan watermark, atau original image dengan
extracted watermark).

## Formula & keputusan yang dipakai

### PSNR
    MSE  = mean((original - watermarked) ** 2)
    PSNR = 10 * log10(MAX_PIXEL^2 / MSE)   , MAX_PIXEL = 255.0 (default)

Kasus MSE == 0 (dua gambar identik secara eksak): PSNR seharusnya
tak hingga. Python/NumPy tidak punya representasi "infinity" yang bisa
dibandingkan numerik dengan mudah kalau dipaksa float biasa, jadi
fungsi ini mengembalikan `math.inf` secara eksplisit untuk kasus ini,
bukan melempar error atau mengembalikan angka besar arbitrer.

### SSIM
Memakai `skimage.metrics.structural_similarity` (bukan
reimplementasi manual) dengan `data_range` sesuai rentang nilai pixel
yang sebenarnya dipakai di proyek ini (default 255.0 untuk grayscale
8-bit). SSIM dua gambar identik = 1.0 (dijamin oleh definisi metrik
itu sendiri, bukan dihitung manual di sini).

### NCC / NC (Normalized Cross-Correlation)
Mengikuti definisi resmi pada dokumen algoritma proyek (3.3.4), formula
yang dipakai adalah normalized correlation TANPA pengurangan mean
(bukan Pearson correlation):

    NC = sum(A * B) / sqrt( sum(A^2) * sum(B^2) )

di mana A = original watermark (flatten, {0,1}), B = extracted
watermark (flatten, {0,1}). Ini adalah formula NC klasik ala Cox et al.
yang umum dipakai di literatur watermarking untuk mengukur kemiripan
watermark hasil ekstraksi terhadap watermark asli.

Konsekuensi memakai formula ini pada data biner {0,1} (bukan bipolar
{-1,+1}): karena A dan B tidak pernah negatif, sum(A*B) tidak pernah
negatif, sehingga NC untuk watermark biner secara praktis berada di
rentang [0, 1] -- bukan [-1, 1] seperti Pearson. Watermark yang benar
sama persis (extraction sempurna) -> NC = 1.0. Watermark yang salah
total (mis. karena key salah, hasil menyerupai bit acak) -> NC
mendekati nilai kecil (bukan -1), termasuk watermark yang merupakan
kebalikan sempurna (inverted) dari aslinya -- itu juga menghasilkan
NC = 0.0, karena tidak ada posisi bit "1" yang tumpang tindih. Ini
konsisten dengan definisi rumus di algoritma.md, walau tidak bisa
membedakan "acak" dari "terbalik sempurna" seperti halnya Pearson.

**Edge case sum(A^2) atau sum(B^2) == 0**: terjadi kalau salah satu
(atau keduanya) watermark seluruhnya bernilai 0 (konstan nol), yang
membuat pembagi (atau bahkan pembilang) di formula NC bernilai nol dan
matematis tidak terdefinisi (0/0). Fungsi ini menangani secara eksplisit:

- Jika A dan B SAMA-SAMA seluruhnya nol (sum(A^2) == 0 dan
  sum(B^2) == 0) -> kembalikan NC = 1.0 (didefinisikan sebagai
  kecocokan sempurna, konsisten dengan interpretasi "watermark
  identik" -- keduanya watermark kosong yang sama).
- Jika HANYA SALAH SATU yang seluruhnya nol (mis. A semua 0, B tidak)
  -> pembilang sum(A*B) otomatis ikut nol sehingga rumus NC menjadi
  0/0, secara matematis tidak terdefinisi -> kembalikan NC = 0.0 dan
  didokumentasikan sebagai "tidak ada kecocokan terdeteksi", BUKAN
  NaN atau error, supaya nilai tetap bisa dipakai/ditabelkan di
  evaluasi tanpa penanganan khusus tambahan di pemanggil.

Tidak pernah mengembalikan NaN atau membiarkan
`ZeroDivisionError`/`RuntimeWarning: invalid value` bocor ke pemanggil.

### BER (Bit Error Rate)
    BER = (jumlah bit yang berbeda) / (total jumlah bit)

Dibandingkan pada representasi bit watermark yang sama (setelah
di-flatten), hasil selalu di rentang [0, 1]. Jika total bit == 0
(array kosong), fungsi melempar ValueError yang jelas -- bukan
membiarkan division-by-zero silent.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from skimage.metrics import structural_similarity as skimage_ssim

DEFAULT_MAX_PIXEL_VALUE = 255.0
DEFAULT_SSIM_DATA_RANGE = 255.0


def _assert_same_shape(a: np.ndarray, b: np.ndarray, context: str) -> None:
    if a.shape != b.shape:
        raise ValueError(
            f"{context}: shape tidak cocok, {a.shape} vs {b.shape}. "
            "Kedua input harus memiliki dimensi yang sama."
        )


# ---------------------------------------------------------------------------
# 1. PSNR -- original image vs watermarked image
# ---------------------------------------------------------------------------

def calculate_psnr(
    original_image: np.ndarray,
    watermarked_image: np.ndarray,
    max_pixel_value: float = DEFAULT_MAX_PIXEL_VALUE,
) -> float:
    """PSNR antara original image dan watermarked image.

    Mengembalikan math.inf jika MSE == 0 (kedua gambar identik
    secara eksak).
    """
    _assert_same_shape(original_image, watermarked_image, "calculate_psnr")

    original = original_image.astype(np.float64)
    watermarked = watermarked_image.astype(np.float64)

    mse = np.mean((original - watermarked) ** 2)

    if mse == 0:
        return math.inf

    psnr = 10.0 * math.log10((max_pixel_value ** 2) / mse)
    return psnr


# ---------------------------------------------------------------------------
# 2. SSIM -- original image vs watermarked image
# ---------------------------------------------------------------------------

def calculate_ssim(
    original_image: np.ndarray,
    watermarked_image: np.ndarray,
    data_range: float = DEFAULT_SSIM_DATA_RANGE,
) -> float:
    """SSIM antara original image dan watermarked image, memakai
    scikit-image (bukan reimplementasi manual)."""
    _assert_same_shape(original_image, watermarked_image, "calculate_ssim")

    if original_image.ndim != 2:
        raise ValueError(
            f"calculate_ssim() untuk Fase 1 mengasumsikan grayscale 2D, dapat shape {original_image.shape}"
        )

    original = original_image.astype(np.float64)
    watermarked = watermarked_image.astype(np.float64)

    score = skimage_ssim(original, watermarked, data_range=data_range)
    return float(score)


# ---------------------------------------------------------------------------
# 3. NCC / NC -- original watermark vs extracted watermark
# ---------------------------------------------------------------------------

def calculate_ncc(original_watermark: np.ndarray, extracted_watermark: np.ndarray) -> float:
    """Normalized Cross-Correlation (NC) antara original watermark dan
    extracted watermark, sesuai definisi 3.3.4 di algoritma.md:

        NC = sum(A * B) / sqrt(sum(A^2) * sum(B^2))

    TANPA pengurangan mean (bukan Pearson correlation).

    Lihat docstring modul untuk penjelasan formula lengkap dan
    penanganan edge case pembagi nol.
    """
    _assert_same_shape(original_watermark, extracted_watermark, "calculate_ncc")

    a = original_watermark.astype(np.float64).flatten()
    b = extracted_watermark.astype(np.float64).flatten()

    if a.size == 0:
        raise ValueError("calculate_ncc(): watermark tidak boleh kosong")

    sum_a2 = np.sum(a ** 2)
    sum_b2 = np.sum(b ** 2)

    a_is_zero = np.isclose(sum_a2, 0.0)
    b_is_zero = np.isclose(sum_b2, 0.0)

    if a_is_zero and b_is_zero:
        # Kedua watermark seluruhnya nol -> didefinisikan identik -> 1.0.
        return 1.0

    if a_is_zero or b_is_zero:
        # Hanya salah satu seluruhnya nol -> numerator ikut nol -> 0/0.
        # Didefinisikan sebagai "tidak ada kecocokan", bukan NaN.
        return 0.0

    numerator = np.sum(a * b)
    denominator = math.sqrt(sum_a2 * sum_b2)

    ncc = numerator / denominator

    # Guard tambahan: floating point kadang menghasilkan sedikit di luar
    # batas Cauchy-Schwarz [-1, 1] untuk kasus identik/hampir identik.
    ncc = max(-1.0, min(1.0, ncc))
    return float(ncc)


# ---------------------------------------------------------------------------
# 4. BER -- original watermark bits vs extracted watermark bits
# ---------------------------------------------------------------------------

def calculate_ber(original_watermark: np.ndarray, extracted_watermark: np.ndarray) -> float:
    """Bit Error Rate antara original watermark bits dan extracted
    watermark bits. Hasil selalu di rentang [0, 1].
    """
    _assert_same_shape(original_watermark, extracted_watermark, "calculate_ber")

    a = original_watermark.astype(np.uint8).flatten()
    b = extracted_watermark.astype(np.uint8).flatten()

    total_bits = a.size
    if total_bits == 0:
        raise ValueError("calculate_ber(): watermark tidak boleh kosong (total bit = 0)")

    n_diff = int(np.sum(a != b))
    ber = n_diff / total_bits
    return ber
