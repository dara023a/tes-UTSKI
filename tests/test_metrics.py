"""
Unit test untuk app/metrics.py (memakai unittest bawaan Python).

Mencakup (sesuai yang diminta):
1. PSNR dua image identik -> inf
2. PSNR image berbeda -> finite & masuk akal
3. SSIM dua image identik -> 1 (atau sangat dekat)
4. SSIM image berbeda -> lebih rendah
5. NCC watermark identik -> 1
6. NCC watermark berbeda -> nilai sesuai implementasi
7. BER watermark identik -> 0
8. BER dengan bit tertentu berbeda -> nilai benar secara manual
9. Shape tidak kompatibel -> ditolak dengan error jelas
10. Tidak ada division-by-zero/NaN yang tidak ditangani pada edge case
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from app.metrics import (
    calculate_psnr,
    calculate_ssim,
    calculate_ncc,
    calculate_ber,
)


class TestPsnr(unittest.TestCase):
    def test_identical_images_gives_infinity(self):
        rng = np.random.default_rng(1)
        image = rng.uniform(0, 255, size=(32, 32))
        psnr = calculate_psnr(image, image.copy())
        self.assertEqual(psnr, math.inf)

    def test_different_images_gives_finite_reasonable_value(self):
        rng = np.random.default_rng(2)
        original = rng.uniform(0, 255, size=(64, 64))
        # tambahkan noise kecil supaya "berbeda tapi mirip" (representasi watermarked image nyata)
        noisy = original + rng.normal(0, 2.0, size=original.shape)
        psnr = calculate_psnr(original, noisy)
        self.assertTrue(math.isfinite(psnr))
        # noise kecil (std=2) pada rentang 0-255 harus menghasilkan PSNR tinggi (>30dB), masuk akal
        self.assertGreater(psnr, 30.0)

    def test_very_different_images_gives_lower_psnr_than_slightly_different(self):
        rng = np.random.default_rng(3)
        original = rng.uniform(0, 255, size=(64, 64))
        slightly_different = original + rng.normal(0, 2.0, size=original.shape)
        very_different = rng.uniform(0, 255, size=(64, 64))  # sama sekali acak lain

        psnr_slight = calculate_psnr(original, slightly_different)
        psnr_very = calculate_psnr(original, very_different)
        self.assertGreater(psnr_slight, psnr_very)

    def test_shape_mismatch_raises(self):
        a = np.zeros((10, 10))
        b = np.zeros((8, 8))
        with self.assertRaises(ValueError):
            calculate_psnr(a, b)


class TestSsim(unittest.TestCase):
    def test_identical_images_gives_one(self):
        rng = np.random.default_rng(4)
        image = rng.uniform(0, 255, size=(32, 32))
        ssim = calculate_ssim(image, image.copy())
        self.assertAlmostEqual(ssim, 1.0, places=6)

    def test_different_images_gives_lower_score(self):
        rng = np.random.default_rng(5)
        original = rng.uniform(0, 255, size=(64, 64))
        slightly_different = original + rng.normal(0, 5.0, size=original.shape)
        very_different = rng.uniform(0, 255, size=(64, 64))

        ssim_slight = calculate_ssim(original, slightly_different)
        ssim_very = calculate_ssim(original, very_different)

        self.assertLess(ssim_slight, 1.0)
        self.assertLess(ssim_very, ssim_slight)

    def test_shape_mismatch_raises(self):
        a = np.zeros((10, 10))
        b = np.zeros((8, 8))
        with self.assertRaises(ValueError):
            calculate_ssim(a, b)

    def test_rejects_non_2d_input(self):
        a = np.zeros((10, 10, 3))
        b = np.zeros((10, 10, 3))
        with self.assertRaises(ValueError):
            calculate_ssim(a, b)


class TestNcc(unittest.TestCase):
    def test_identical_watermark_gives_one(self):
        wm = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8)
        ncc = calculate_ncc(wm, wm.copy())
        self.assertAlmostEqual(ncc, 1.0, places=9)

    def test_completely_inverted_watermark_gives_zero(self):
        # Formula NC = sum(A*B) / sqrt(sum(A^2)*sum(B^2)) tanpa mean-centering
        # (sesuai algoritma.md 3.3.4). Untuk watermark biner {0,1}, posisi
        # yang bernilai 1 di A selalu 0 di kebalikannya (dan sebaliknya),
        # sehingga sum(A*B) == 0 -> NC = 0.0 (bukan -1.0 seperti Pearson).
        wm = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8)
        inverted = 1 - wm
        ncc = calculate_ncc(wm, inverted)
        self.assertAlmostEqual(ncc, 0.0, places=9)

    def test_random_different_watermark_within_valid_range(self):
        # Untuk watermark biner {0,1}, rumus NC non-centered (sum(A*B)>=0)
        # secara praktis selalu menghasilkan nilai di [0, 1], subset dari
        # batas umum Cauchy-Schwarz [-1, 1].
        rng = np.random.default_rng(6)
        original = (rng.uniform(size=(8, 8)) > 0.5).astype(np.uint8)
        different = (rng.uniform(size=(8, 8)) > 0.5).astype(np.uint8)
        ncc = calculate_ncc(original, different)
        self.assertGreaterEqual(ncc, 0.0)
        self.assertLessEqual(ncc, 1.0)

    def test_both_constant_and_identical_gives_one(self):
        a = np.ones((4, 4), dtype=np.uint8)
        b = np.ones((4, 4), dtype=np.uint8)
        ncc = calculate_ncc(a, b)
        self.assertEqual(ncc, 1.0)

    def test_both_constant_but_different_gives_zero(self):
        a = np.zeros((4, 4), dtype=np.uint8)
        b = np.ones((4, 4), dtype=np.uint8)
        ncc = calculate_ncc(a, b)
        self.assertEqual(ncc, 0.0)

    def test_one_constant_one_not_gives_zero_no_nan(self):
        a = np.zeros((4, 4), dtype=np.uint8)  # variance nol
        b = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8)
        ncc = calculate_ncc(a, b)
        self.assertFalse(math.isnan(ncc))
        self.assertEqual(ncc, 0.0)

    def test_shape_mismatch_raises(self):
        a = np.zeros((4, 4), dtype=np.uint8)
        b = np.zeros((2, 2), dtype=np.uint8)
        with self.assertRaises(ValueError):
            calculate_ncc(a, b)

    def test_empty_watermark_raises(self):
        a = np.zeros((0, 0), dtype=np.uint8)
        b = np.zeros((0, 0), dtype=np.uint8)
        with self.assertRaises(ValueError):
            calculate_ncc(a, b)


class TestBer(unittest.TestCase):
    def test_identical_watermark_gives_zero(self):
        wm = np.array([[1, 0, 1], [0, 1, 0]], dtype=np.uint8)
        ber = calculate_ber(wm, wm.copy())
        self.assertEqual(ber, 0.0)

    def test_specific_bit_differences_manual_calculation(self):
        original = np.array([1, 0, 1, 0, 1, 0, 1, 0], dtype=np.uint8)
        extracted = np.array([1, 0, 1, 0, 1, 0, 0, 1], dtype=np.uint8)  # 2 bit terakhir beda
        ber = calculate_ber(original, extracted)
        self.assertAlmostEqual(ber, 2 / 8, places=9)

    def test_all_bits_different_gives_one(self):
        original = np.array([1, 0, 1, 0], dtype=np.uint8)
        extracted = np.array([0, 1, 0, 1], dtype=np.uint8)
        ber = calculate_ber(original, extracted)
        self.assertEqual(ber, 1.0)

    def test_result_within_zero_one_range(self):
        rng = np.random.default_rng(7)
        original = (rng.uniform(size=(16, 16)) > 0.5).astype(np.uint8)
        extracted = (rng.uniform(size=(16, 16)) > 0.5).astype(np.uint8)
        ber = calculate_ber(original, extracted)
        self.assertGreaterEqual(ber, 0.0)
        self.assertLessEqual(ber, 1.0)

    def test_shape_mismatch_raises(self):
        a = np.zeros((4, 4), dtype=np.uint8)
        b = np.zeros((2, 2), dtype=np.uint8)
        with self.assertRaises(ValueError):
            calculate_ber(a, b)

    def test_empty_watermark_raises(self):
        a = np.zeros((0,), dtype=np.uint8)
        b = np.zeros((0,), dtype=np.uint8)
        with self.assertRaises(ValueError):
            calculate_ber(a, b)


class TestMetricsDoNotMixInputPairs(unittest.TestCase):
    """Uji tambahan: memastikan tidak ada silent success ketika pasangan
    metrik/parameter yang dipakai jelas tidak relevan (image besar vs
    watermark kecil) -- shape mismatch harus tetap ditolak, bukan
    dipaksa broadcast oleh NumPy."""

    def test_image_vs_watermark_shape_mismatch_rejected_for_psnr(self):
        image = np.zeros((64, 64))
        watermark = np.zeros((4, 4))
        with self.assertRaises(ValueError):
            calculate_psnr(image, watermark)

    def test_image_vs_watermark_shape_mismatch_rejected_for_ncc(self):
        image = np.zeros((64, 64))
        watermark = np.zeros((4, 4))
        with self.assertRaises(ValueError):
            calculate_ncc(image, watermark)


if __name__ == "__main__":
    unittest.main()
