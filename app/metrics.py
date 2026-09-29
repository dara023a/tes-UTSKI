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

### NCC / NC (Normalized Cross-Correlation — Zero-Mean / Pearson)
Mengikuti definisi Pearson normalized correlation:

    NC = sum((A-mean(A)) * (B-mean(B))) / sqrt( sum((A-mean(A))^2) * sum((B-mean(B))^2) )

di mana A = original watermark (flatten, float), B = extracted watermark
(flatten, float). Formula ini MENGURANGI mean sebelum perkalian (zero-mean),
sehingga hasil NC tidak bergantung pada komposisi bit watermark (logo
timpang ~5% bit-1 vs checkerboard 50:50 keduanya menghasilkan baseline NC
≈ 0 untuk output acak).

Rentang NC adalah [-1, 1]:
- NC ≈ 1.0 : watermark terekstrak sempurna (identik dengan asli)
- NC ≈ 0.0 : tidak ada korelasi (output acak / key salah)
- NC < 0   : korelasi negatif (extracted adalah inversi dari asli)

**Edge case std == 0**: terjadi kalau salah satu array konstan (semua
bernilai sama, mis. seluruhnya 0 atau seluruhnya 1), sehingga
std-deviasi = 0 dan pembagi menjadi nol:

- Jika KEDUANYA konstan DAN sama nilainya -> NC = 1.0 (identik).
- Jika KEDUANYA konstan tapi BERBEDA nilainya -> NC = 0.0 (tidak ada
  korelasi yang bisa dihitung).
- Jika HANYA SALAH SATU konstan -> NC = 0.0.

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
    """Zero-mean Normalized Cross-Correlation (NC/Pearson) antara original
    watermark dan extracted watermark:

        NC = sum((A-mean(A)) * (B-mean(B))) / sqrt(
                 sum((A-mean(A))^2) * sum((B-mean(B))^2) )

    Formula ini tidak bergantung pada komposisi bit (logo timpang ~5% bit-1
    maupun checkerboard 50:50 sama-sama menghasilkan NC ≈ 0 untuk output
    acak). Rentang output: [-1, 1].

    Lihat docstring modul untuk penjelasan edge case.
    """
    _assert_same_shape(original_watermark, extracted_watermark, "calculate_ncc")

    a = original_watermark.astype(np.float64).flatten()
    b = extracted_watermark.astype(np.float64).flatten()

    if a.size == 0:
        raise ValueError("calculate_ncc(): watermark tidak boleh kosong")

    a_centered = a - a.mean()
    b_centered = b - b.mean()

    std_a = math.sqrt(np.sum(a_centered ** 2))
    std_b = math.sqrt(np.sum(b_centered ** 2))

    # Edge case: salah satu atau keduanya konstan (std == 0)
    a_const = math.isclose(std_a, 0.0)
    b_const = math.isclose(std_b, 0.0)

    if a_const and b_const:
        # Keduanya konstan -- identik jika nilai mean sama, berbeda jika tidak
        return 1.0 if math.isclose(a.mean(), b.mean()) else 0.0

    if a_const or b_const:
        # Salah satu konstan -- tidak ada pola yang bisa dikorelasikan
        return 0.0

    numerator = float(np.sum(a_centered * b_centered))
    denominator = std_a * std_b

    ncc = numerator / denominator

    # Guard floating-point agar selalu dalam [-1, 1]
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
