"""
Integration test untuk app/pipeline.py (memakai unittest bawaan Python +
file image sungguhan di disk, bukan hanya array in-memory).

Mencakup (sesuai yang diminta):
1. End-to-end embed -> extract tanpa attack
2. Extract menggunakan key yang benar
3. Extract dengan key berbeda -> watermark berbeda/tidak cocok
4. Evaluation menghasilkan PSNR, SSIM, NCC, BER
5. Metadata digunakan dengan benar
6. Original image tidak diperlukan pada extraction (struktural)
7. Error handling untuk file/metadata yang tidak valid
8. Capacity error diteruskan dengan benar
9. Output image dan extracted watermark benar-benar dapat dibaca kembali
"""

import sys
import os
import json
import shutil
import tempfile
import unittest
import inspect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import cv2
import numpy as np

from app.pipeline import (
    run_embedding_pipeline,
    run_extraction_pipeline,
    run_evaluation_pipeline,
    load_grayscale_image,
    load_binary_watermark_image,
    ImageLoadError,
    MetadataError,
)
from app.watermark import CapacityError


class PipelineTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

        rng = np.random.default_rng(2025)

        # Original image 64x64 grayscale -> 64 blok 8x8 tersedia.
        self.original_image_path = os.path.join(self.tmp_dir, "original.png")
        original = rng.uniform(0, 255, size=(64, 64)).astype(np.uint8)
        cv2.imwrite(self.original_image_path, original)

        # Watermark 4x4 -> 16 bit, jauh di bawah kapasitas 64 blok.
        self.watermark_image_path = os.path.join(self.tmp_dir, "watermark.png")
        wm_gray = np.array(
            [
                [0, 255, 0, 255],
                [255, 0, 255, 0],
                [0, 0, 255, 255],
                [255, 255, 0, 0],
            ],
            dtype=np.uint8,
        )
        cv2.imwrite(self.watermark_image_path, wm_gray)

        self.key = "pipeline-test-key"
        self.alpha = 10.0
        self.watermarked_image_path = os.path.join(self.tmp_dir, "watermarked.png")
        self.metadata_path = os.path.join(self.tmp_dir, "metadata.json")
        self.extracted_watermark_path = os.path.join(self.tmp_dir, "extracted.png")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class TestEndToEndEmbedExtract(PipelineTestBase):
    def test_embed_then_extract_without_attack_recovers_watermark(self):
        embed_result = run_embedding_pipeline(
            self.original_image_path,
            self.watermark_image_path,
            self.key,
            self.alpha,
            self.watermarked_image_path,
            self.metadata_path,
        )

        self.assertTrue(os.path.isfile(self.watermarked_image_path))
        self.assertTrue(os.path.isfile(self.metadata_path))

        extract_result = run_extraction_pipeline(
            self.watermarked_image_path,
            self.key,
            self.metadata_path,
            self.extracted_watermark_path,
        )

        extracted = extract_result["extracted_watermark"]
        original_watermark = embed_result["watermark_binary"]

        np.testing.assert_array_equal(extracted, original_watermark)

    def test_extraction_with_correct_key_matches(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        result1 = run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)
        result2 = run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)
        np.testing.assert_array_equal(result1["extracted_watermark"], result2["extracted_watermark"])

    def test_extraction_with_wrong_key_gives_different_result(self):
        embed_result = run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        wrong_result = run_extraction_pipeline(
            self.watermarked_image_path, "totally-different-key", self.metadata_path
        )
        self.assertFalse(
            np.array_equal(wrong_result["extracted_watermark"], embed_result["watermark_binary"])
        )


class TestEvaluationPipeline(PipelineTestBase):
    def test_evaluation_produces_all_four_metrics(self):
        embed_result = run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        extract_result = run_extraction_pipeline(
            self.watermarked_image_path, self.key, self.metadata_path, self.extracted_watermark_path
        )

        metrics = run_evaluation_pipeline(
            embed_result["original_image"],
            embed_result["watermarked_image"],
            embed_result["watermark_binary"],
            extract_result["extracted_watermark"],
        )

        for name in ("psnr", "ssim", "ncc", "ber"):
            self.assertIn(name, metrics)

        # tanpa attack, watermark harusnya identik -> NCC=1, BER=0
        self.assertAlmostEqual(metrics["ncc"], 1.0, places=6)
        self.assertEqual(metrics["ber"], 0.0)
        self.assertGreater(metrics["psnr"], 0.0)
        self.assertGreaterEqual(metrics["ssim"], -1.0)
        self.assertLessEqual(metrics["ssim"], 1.0)


class TestMetadataUsage(PipelineTestBase):
    def test_metadata_file_contains_expected_fields_and_no_key(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        for field in ("watermark_shape", "block_size", "coeff_positions", "processed_image_size", "alpha", "n_bits", "binarize_threshold"):
            self.assertIn(field, metadata)

        self.assertNotIn("key", metadata)
        self.assertNotIn("secret_key", metadata)
        self.assertEqual(metadata["binarize_threshold"], 127)

    def test_extraction_actually_uses_metadata_watermark_shape(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        result = run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)
        self.assertEqual(result["extracted_watermark"].shape, (4, 4))


class TestOriginalImageNotNeededForExtraction(PipelineTestBase):
    def test_extraction_function_signature_has_no_original_image_param(self):
        sig = inspect.signature(run_extraction_pipeline)
        param_names = set(sig.parameters.keys())
        self.assertNotIn("original_image", param_names)
        self.assertNotIn("original_image_path", param_names)

    def test_extraction_works_even_if_original_image_file_deleted(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        os.remove(self.original_image_path)  # original image sengaja dihapus
        result = run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)
        self.assertEqual(result["extracted_watermark"].shape, (4, 4))


class TestErrorHandling(PipelineTestBase):
    def test_embedding_raises_when_original_image_missing(self):
        with self.assertRaises(ImageLoadError):
            run_embedding_pipeline(
                os.path.join(self.tmp_dir, "does-not-exist.png"),
                self.watermark_image_path, self.key, self.alpha,
                self.watermarked_image_path, self.metadata_path,
            )

    def test_embedding_raises_when_watermark_image_missing(self):
        with self.assertRaises(ImageLoadError):
            run_embedding_pipeline(
                self.original_image_path,
                os.path.join(self.tmp_dir, "no-watermark-here.png"),
                self.key, self.alpha,
                self.watermarked_image_path, self.metadata_path,
            )

    def test_extraction_raises_when_metadata_missing(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        os.remove(self.metadata_path)
        with self.assertRaises(MetadataError):
            run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)

    def test_extraction_raises_when_metadata_is_invalid_json(self):
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            f.write("{ ini bukan json yang valid ][")
        with self.assertRaises(MetadataError):
            run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)

    def test_extraction_raises_when_metadata_missing_required_fields(self):
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump({"watermark_shape": [4, 4]}, f)  # sengaja tidak lengkap
        with self.assertRaises(MetadataError):
            run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)

    def test_extraction_raises_when_watermarked_image_missing(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        os.remove(self.watermarked_image_path)
        with self.assertRaises(ImageLoadError):
            run_extraction_pipeline(self.watermarked_image_path, self.key, self.metadata_path)

    def test_empty_key_rejected_on_embedding(self):
        with self.assertRaises(ValueError):
            run_embedding_pipeline(
                self.original_image_path, self.watermark_image_path, "   ", self.alpha,
                self.watermarked_image_path, self.metadata_path,
            )

    def test_empty_key_rejected_on_extraction(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        with self.assertRaises(ValueError):
            run_extraction_pipeline(self.watermarked_image_path, "", self.metadata_path)


class TestCapacityErrorPropagation(PipelineTestBase):
    def test_capacity_error_propagates_from_embedding(self):
        # Gambar kecil 16x16 -> hanya 4 blok (2x2), tapi watermark 4x4 = 16 bit.
        small_image_path = os.path.join(self.tmp_dir, "small_original.png")
        rng = np.random.default_rng(1)
        small = rng.uniform(0, 255, size=(16, 16)).astype(np.uint8)
        cv2.imwrite(small_image_path, small)

        with self.assertRaises(CapacityError):
            run_embedding_pipeline(
                small_image_path, self.watermark_image_path, self.key, self.alpha,
                self.watermarked_image_path, self.metadata_path,
            )


class TestOutputFilesReadableBack(PipelineTestBase):
    def test_watermarked_image_and_extracted_watermark_readable_back(self):
        run_embedding_pipeline(
            self.original_image_path, self.watermark_image_path, self.key, self.alpha,
            self.watermarked_image_path, self.metadata_path,
        )
        run_extraction_pipeline(
            self.watermarked_image_path, self.key, self.metadata_path, self.extracted_watermark_path
        )

        # Baca ulang watermarked image dari disk (bukan dari memory hasil embed).
        reloaded_watermarked = load_grayscale_image(self.watermarked_image_path)
        self.assertEqual(reloaded_watermarked.shape, (64, 64))

        # Baca ulang extracted watermark image dari disk.
        reloaded_extracted = load_binary_watermark_image(self.extracted_watermark_path)
        self.assertEqual(reloaded_extracted.shape, (4, 4))
        self.assertTrue(set(np.unique(reloaded_extracted)).issubset({0, 1}))


if __name__ == "__main__":
    unittest.main()
