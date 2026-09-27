"""
Unit test untuk app/dct.py (memakai unittest bawaan Python).

Mencakup (sesuai yang diminta):
1. DCT -> IDCT reconstruction (identitas, dalam toleransi floating point)
2. Block splitting -> reconstruction (identitas)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


class TestDct2Idct2(unittest.TestCase):
    def test_reconstruction_random_block(self):
        rng = np.random.default_rng(42)
        block = rng.uniform(0, 255, size=(BLOCK_SIZE, BLOCK_SIZE))
        reconstructed = idct2(dct2(block))
        self.assertEqual(reconstructed.shape, block.shape)
        np.testing.assert_allclose(reconstructed, block, atol=1e-8)

    def test_reconstruction_multiple_random_blocks(self):
        rng = np.random.default_rng(123)
        for _ in range(20):
            block = rng.uniform(0, 255, size=(BLOCK_SIZE, BLOCK_SIZE))
            reconstructed = idct2(dct2(block))
            np.testing.assert_allclose(reconstructed, block, atol=1e-8)

    def test_dct2_rejects_non_2d_input(self):
        with self.assertRaises(ValueError):
            dct2(np.zeros((8, 8, 3)))

    def test_idct2_rejects_non_2d_input(self):
        with self.assertRaises(ValueError):
            idct2(np.zeros((8,)))


class TestCropToMultipleOfBlock(unittest.TestCase):
    def test_exact_multiple(self):
        image = np.zeros((64, 32))
        cropped, used_shape = crop_to_multiple_of_block(image)
        self.assertEqual(used_shape, (64, 32))
        self.assertEqual(cropped.shape, (64, 32))

    def test_non_multiple_matches_spec_example(self):
        # contoh dari spesifikasi user: 1010 x 777 -> 1008 x 776
        image = np.zeros((777, 1010))  # (H, W)
        cropped, used_shape = crop_to_multiple_of_block(image)
        self.assertEqual(used_shape, (776, 1008))
        self.assertEqual(cropped.shape, (776, 1008))

    def test_too_small_raises(self):
        image = np.zeros((5, 100))
        with self.assertRaises(ValueError):
            crop_to_multiple_of_block(image)


class TestSplitAndReconstruct(unittest.TestCase):
    def test_split_and_reconstruct_is_identity(self):
        rng = np.random.default_rng(7)
        image = rng.uniform(0, 255, size=(32, 24))  # kelipatan 8

        blocks = split_into_blocks(image)
        self.assertEqual(len(blocks), num_blocks(image.shape))
        for b in blocks:
            self.assertEqual(b.shape, (BLOCK_SIZE, BLOCK_SIZE))

        reconstructed = reconstruct_from_blocks(blocks, image.shape)
        np.testing.assert_allclose(reconstructed, image, atol=1e-12)

    def test_split_into_blocks_rejects_non_multiple_shape(self):
        image = np.zeros((10, 10))
        with self.assertRaises(ValueError):
            split_into_blocks(image)

    def test_reconstruct_rejects_wrong_block_count(self):
        image = np.zeros((16, 16))
        blocks = split_into_blocks(image)
        with self.assertRaises(ValueError):
            reconstruct_from_blocks(blocks[:-1], image.shape)

    def test_num_blocks_calculation(self):
        self.assertEqual(num_blocks((64, 32)), (64 // 8) * (32 // 8))
        self.assertEqual(num_blocks((776, 1008)), (776 // 8) * (1008 // 8))


class TestFullDctRoundtripIntegration(unittest.TestCase):
    def test_full_pipeline_dct_domain_roundtrip_on_real_sized_image(self):
        """Integrasi kecil: crop -> split -> dct2 tiap blok -> idct2 tiap
        blok -> reconstruct -> harus sama dengan gambar hasil crop awal."""
        rng = np.random.default_rng(99)
        raw_image = rng.uniform(0, 255, size=(101, 130))  # sengaja bukan kelipatan 8

        cropped, used_shape = crop_to_multiple_of_block(raw_image)
        blocks = split_into_blocks(cropped)

        transformed_blocks = [idct2(dct2(b)) for b in blocks]
        reconstructed = reconstruct_from_blocks(transformed_blocks, used_shape)

        np.testing.assert_allclose(reconstructed, cropped, atol=1e-8)


if __name__ == "__main__":
    unittest.main()
