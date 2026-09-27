"""
Unit test untuk app/watermark.py (memakai unittest bawaan Python).

Mencakup (sesuai yang diminta):
1. enforce_margin() bit 0
2. enforce_margin() bit 1
3. sum C1+C2 tetap
4. margin >= alpha
5. embedding/extraction tanpa attack
6. extraction menggunakan key yang sama
7. key berbeda menghasilkan sequence berbeda (-> extraction gagal cocok)
8. capacity error
9. metadata dapat disimpan dan dibaca kembali
"""

import sys
import os
import json
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from app.watermark import (
    binarize_watermark,
    watermark_to_bits,
    bits_to_watermark,
    check_capacity,
    enforce_margin,
    embed_watermark,
    extract_watermark,
    save_metadata,
    load_metadata,
    CapacityError,
    COEFF_1_POS,
    COEFF_2_POS,
)


class TestBinarizeAndBitConversion(unittest.TestCase):
    def test_binarize_watermark_basic(self):
        gray = np.array([[0, 200], [130, 50]], dtype=np.float64)
        binary = binarize_watermark(gray, threshold=127)
        np.testing.assert_array_equal(binary, np.array([[0, 1], [1, 0]], dtype=np.uint8))

    def test_watermark_to_bits_and_back_roundtrip(self):
        binary = np.array([[1, 0, 1], [0, 1, 0]], dtype=np.uint8)
        bits, shape = watermark_to_bits(binary)
        self.assertEqual(shape, (2, 3))
        np.testing.assert_array_equal(bits, np.array([1, 0, 1, 0, 1, 0], dtype=np.uint8))

        reconstructed = bits_to_watermark(bits, shape)
        np.testing.assert_array_equal(reconstructed, binary)

    def test_bits_to_watermark_rejects_wrong_size(self):
        with self.assertRaises(ValueError):
            bits_to_watermark(np.array([1, 0, 1]), (2, 2))


class TestCapacityCheck(unittest.TestCase):
    def test_check_capacity_ok(self):
        # tidak boleh raise
        check_capacity(n_bits=10, n_blocks_available=10)
        check_capacity(n_bits=5, n_blocks_available=10)

    def test_check_capacity_raises_when_exceeded(self):
        with self.assertRaises(CapacityError):
            check_capacity(n_bits=11, n_blocks_available=10)


class TestEnforceMargin(unittest.TestCase):
    def test_bit_1_c1_greater_than_c2(self):
        c1, c2 = 10.0, 30.0
        c1_new, c2_new = enforce_margin(c1, c2, bit=1, alpha=8.0)
        self.assertGreater(c1_new, c2_new)

    def test_bit_0_c1_less_than_c2(self):
        c1, c2 = 10.0, 30.0
        c1_new, c2_new = enforce_margin(c1, c2, bit=0, alpha=8.0)
        self.assertLess(c1_new, c2_new)

    def test_sum_preserved(self):
        for (c1, c2, bit, alpha) in [(10.0, 30.0, 1, 8.0), (5.0, 5.0, 0, 12.0), (-20.0, 40.0, 1, 6.0)]:
            c1_new, c2_new = enforce_margin(c1, c2, bit, alpha)
            self.assertAlmostEqual(c1_new + c2_new, c1 + c2, places=10)

    def test_margin_at_least_alpha(self):
        for alpha in (2.0, 5.0, 10.0, 20.0):
            c1_new, c2_new = enforce_margin(10.0, 10.0, bit=1, alpha=alpha)
            self.assertGreaterEqual(abs(c1_new - c2_new), alpha - 1e-9)
            c1_new0, c2_new0 = enforce_margin(10.0, 10.0, bit=0, alpha=alpha)
            self.assertGreaterEqual(abs(c1_new0 - c2_new0), alpha - 1e-9)

    def test_rejects_invalid_bit(self):
        with self.assertRaises(ValueError):
            enforce_margin(1.0, 2.0, bit=2, alpha=5.0)

    def test_rejects_non_positive_alpha(self):
        with self.assertRaises(ValueError):
            enforce_margin(1.0, 2.0, bit=1, alpha=0)
        with self.assertRaises(ValueError):
            enforce_margin(1.0, 2.0, bit=1, alpha=-5.0)


class TestEmbedExtractRoundtrip(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(2024)
        # Gambar 64x64 -> 8x8 = 64 blok tersedia
        self.image = rng.uniform(0, 255, size=(64, 64))
        # Watermark 4x4 = 16 bit, jauh di bawah kapasitas 64 blok
        wm_gray = rng.uniform(0, 255, size=(4, 4))
        self.watermark_binary = binarize_watermark(wm_gray, threshold=127)
        self.key = "correct-secret-key"
        self.alpha = 10.0

    def test_embed_produces_correct_shapes_and_metadata(self):
        watermarked, metadata = embed_watermark(self.image, self.watermark_binary, self.key, self.alpha)
        self.assertEqual(watermarked.shape, self.image.shape)
        self.assertEqual(tuple(metadata["watermark_shape"]), self.watermark_binary.shape)
        self.assertEqual(metadata["block_size"], 8)
        self.assertEqual(metadata["coeff_positions"], [list(COEFF_1_POS), list(COEFF_2_POS)])
        self.assertEqual(metadata["alpha"], self.alpha)
        self.assertEqual(metadata["n_bits"], 16)

    def test_extraction_without_attack_recovers_watermark_exactly(self):
        watermarked, metadata = embed_watermark(self.image, self.watermark_binary, self.key, self.alpha)
        extracted = extract_watermark(watermarked, self.key, metadata)

        self.assertEqual(extracted.shape, self.watermark_binary.shape)
        np.testing.assert_array_equal(extracted, self.watermark_binary)

    def test_extraction_with_same_key_is_consistent(self):
        watermarked, metadata = embed_watermark(self.image, self.watermark_binary, self.key, self.alpha)
        extracted1 = extract_watermark(watermarked, self.key, metadata)
        extracted2 = extract_watermark(watermarked, self.key, metadata)
        np.testing.assert_array_equal(extracted1, extracted2)
        np.testing.assert_array_equal(extracted1, self.watermark_binary)

    def test_wrong_key_produces_different_extraction(self):
        watermarked, metadata = embed_watermark(self.image, self.watermark_binary, self.key, self.alpha)
        extracted_wrong = extract_watermark(watermarked, "a-completely-different-key", metadata)

        # Key salah -> block sequence berbeda -> hasil ekstraksi TIDAK
        # boleh identik dengan watermark asli (secara normal).
        self.assertFalse(np.array_equal(extracted_wrong, self.watermark_binary))

    def test_capacity_error_raised_when_watermark_too_large(self):
        rng = np.random.default_rng(1)
        small_image = rng.uniform(0, 255, size=(16, 16))  # hanya 4 blok (2x2)
        big_watermark = np.ones((4, 4), dtype=np.uint8)   # butuh 16 bit

        with self.assertRaises(CapacityError):
            embed_watermark(small_image, big_watermark, self.key, self.alpha)

    def test_extraction_rejects_mismatched_image_size(self):
        watermarked, metadata = embed_watermark(self.image, self.watermark_binary, self.key, self.alpha)
        wrong_size_image = watermarked[:32, :32]  # ukuran beda dari metadata
        with self.assertRaises(ValueError):
            extract_watermark(wrong_size_image, self.key, metadata)


class TestMetadataPersistence(unittest.TestCase):
    def test_save_and_load_metadata_roundtrip(self):
        metadata = {
            "watermark_shape": [4, 4],
            "block_size": 8,
            "coeff_positions": [[4, 5], [5, 4]],
            "processed_image_size": [64, 64],
            "alpha": 10.0,
            "n_bits": 16,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "metadata.json")
            save_metadata(path, metadata)
            self.assertTrue(os.path.exists(path))

            loaded = load_metadata(path)
            self.assertEqual(loaded, metadata)

    def test_save_metadata_rejects_secret_key_field(self):
        metadata_with_key = {"watermark_shape": [4, 4], "key": "should-not-be-here"}
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "metadata.json")
            with self.assertRaises(ValueError):
                save_metadata(path, metadata_with_key)

    def test_saved_metadata_file_contains_no_key_field(self):
        metadata = {
            "watermark_shape": [4, 4],
            "block_size": 8,
            "coeff_positions": [[4, 5], [5, 4]],
            "processed_image_size": [64, 64],
            "alpha": 10.0,
            "n_bits": 16,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "metadata.json")
            save_metadata(path, metadata)
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            self.assertNotIn("key", json.loads(raw).keys())


if __name__ == "__main__":
    unittest.main()
