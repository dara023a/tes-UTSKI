"""
Test CLI untuk main.py (memakai unittest + subprocess -- CLI benar-benar
dijalankan sebagai proses terpisah, bukan memanggil fungsi Python secara
langsung, supaya argparse/exit code/stdout-stderr diuji apa adanya).

Mencakup (sesuai yang diminta):
1. embed berhasil menggunakan file nyata
2. extract berhasil menggunakan watermarked image + metadata + key
3. extract tidak membutuhkan original image
4. evaluate menampilkan keempat metrics
5. missing required argument -> error
6. file tidak ditemukan -> exit code non-zero
7. key kosong/invalid ditolak
8. alpha invalid ditolak
9. CLI tidak mencetak secret key
10. command tidak dikenal ditolak
"""

import sys
import os
import shutil
import subprocess
import tempfile
import unittest

import cv2
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN_PY = os.path.join(PROJECT_ROOT, "main.py")


def run_cli(*args):
    """Menjalankan `python3 main.py <args>` sebagai proses sungguhan."""
    result = subprocess.run(
        [sys.executable, MAIN_PY, *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


class CLITestBase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

        rng = np.random.default_rng(777)
        self.original_image_path = os.path.join(self.tmp_dir, "test.png")
        original = rng.uniform(0, 255, size=(64, 64)).astype(np.uint8)
        cv2.imwrite(self.original_image_path, original)

        self.watermark_image_path = os.path.join(self.tmp_dir, "logo.png")
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

        self.secret_key = "super-rahasia-jangan-tampil-di-layar"
        self.watermarked_path = os.path.join(self.tmp_dir, "watermarked.png")
        self.metadata_path = os.path.join(self.tmp_dir, "metadata.json")
        self.extracted_path = os.path.join(self.tmp_dir, "extracted.png")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _embed(self, key=None, alpha="10"):
        return run_cli(
            "embed",
            "--image", self.original_image_path,
            "--watermark", self.watermark_image_path,
            "--key", key if key is not None else self.secret_key,
            "--alpha", str(alpha),
            "--output-watermarked", self.watermarked_path,
            "--output-metadata", self.metadata_path,
        )


class TestEmbedCommand(CLITestBase):
    def test_embed_succeeds_with_real_files(self):
        result = self._embed()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isfile(self.watermarked_path))
        self.assertTrue(os.path.isfile(self.metadata_path))
        self.assertIn("Embedding selesai", result.stdout)


class TestExtractCommand(CLITestBase):
    def test_extract_succeeds_with_watermarked_metadata_and_key(self):
        embed_result = self._embed()
        self.assertEqual(embed_result.returncode, 0, msg=embed_result.stderr)

        extract_result = run_cli(
            "extract",
            "--image", self.watermarked_path,
            "--metadata", self.metadata_path,
            "--key", self.secret_key,
            "--output", self.extracted_path,
        )
        self.assertEqual(extract_result.returncode, 0, msg=extract_result.stderr)
        self.assertTrue(os.path.isfile(self.extracted_path))
        self.assertIn("Extraction selesai", extract_result.stdout)

    def test_extract_command_help_does_not_expose_original_image_flag(self):
        # extract tidak boleh punya opsi untuk original image sama sekali.
        result = run_cli("extract", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--original", result.stdout)

    def test_extract_works_after_original_image_deleted(self):
        embed_result = self._embed()
        self.assertEqual(embed_result.returncode, 0, msg=embed_result.stderr)
        os.remove(self.original_image_path)  # original image dihapus dulu

        extract_result = run_cli(
            "extract",
            "--image", self.watermarked_path,
            "--metadata", self.metadata_path,
            "--key", self.secret_key,
            "--output", self.extracted_path,
        )
        self.assertEqual(extract_result.returncode, 0, msg=extract_result.stderr)


class TestEvaluateCommand(CLITestBase):
    def test_evaluate_displays_all_four_metrics(self):
        self._embed()
        run_cli(
            "extract",
            "--image", self.watermarked_path,
            "--metadata", self.metadata_path,
            "--key", self.secret_key,
            "--output", self.extracted_path,
        )

        eval_result = run_cli(
            "evaluate",
            "--original", self.original_image_path,
            "--watermarked", self.watermarked_path,
            "--watermark", self.watermark_image_path,
            "--extracted", self.extracted_path,
        )
        self.assertEqual(eval_result.returncode, 0, msg=eval_result.stderr)
        self.assertIn("PSNR", eval_result.stdout)
        self.assertIn("SSIM", eval_result.stdout)
        self.assertIn("NCC", eval_result.stdout)
        self.assertIn("BER", eval_result.stdout)


class TestArgumentValidation(CLITestBase):
    def test_missing_required_argument_gives_error(self):
        result = run_cli("embed", "--image", self.original_image_path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stderr.lower())

    def test_file_not_found_gives_nonzero_exit_code(self):
        result = run_cli(
            "extract",
            "--image", "/path/does/not/exist.png",
            "--metadata", self.metadata_path,
            "--key", self.secret_key,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error", result.stderr)

    def test_empty_key_rejected(self):
        result = self._embed(key="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("key", result.stderr.lower())

    def test_invalid_alpha_zero_rejected(self):
        result = self._embed(alpha="0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("alpha", result.stderr.lower())

    def test_invalid_alpha_negative_rejected(self):
        result = self._embed(alpha="-3")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("alpha", result.stderr.lower())

    def test_unknown_command_rejected(self):
        result = run_cli("foobar-command")
        self.assertNotEqual(result.returncode, 0)


class TestSecretKeyNeverPrinted(CLITestBase):
    def test_embed_does_not_print_secret_key(self):
        result = self._embed()
        self.assertNotIn(self.secret_key, result.stdout)
        self.assertNotIn(self.secret_key, result.stderr)

    def test_extract_does_not_print_secret_key(self):
        self._embed()
        result = run_cli(
            "extract",
            "--image", self.watermarked_path,
            "--metadata", self.metadata_path,
            "--key", self.secret_key,
            "--output", self.extracted_path,
        )
        self.assertNotIn(self.secret_key, result.stdout)
        self.assertNotIn(self.secret_key, result.stderr)

    def test_wrong_key_error_case_does_not_leak_key(self):
        # Bahkan pada kasus sukses dengan key salah (bukan error), key tidak boleh muncul.
        self._embed()
        result = run_cli(
            "extract",
            "--image", self.watermarked_path,
            "--metadata", self.metadata_path,
            "--key", "kunci-yang-berbeda-sama-sekali",
            "--output", self.extracted_path,
        )
        self.assertNotIn("kunci-yang-berbeda-sama-sekali", result.stdout)
        self.assertNotIn("kunci-yang-berbeda-sama-sekali", result.stderr)


class TestMetadataAndCapacityErrorsViaCLI(CLITestBase):
    def test_invalid_metadata_gives_clear_error_not_traceback(self):
        self._embed()
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            f.write("bukan json valid {{{")

        result = run_cli(
            "extract",
            "--image", self.watermarked_path,
            "--metadata", self.metadata_path,
            "--key", self.secret_key,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error", result.stderr)
        # Tidak boleh ada traceback panjang untuk kesalahan input biasa.
        self.assertNotIn("Traceback (most recent call last)", result.stderr)

    def test_capacity_error_via_cli_is_clean_error_not_traceback(self):
        small_image_path = os.path.join(self.tmp_dir, "small.png")
        rng = np.random.default_rng(9)
        small = rng.uniform(0, 255, size=(16, 16)).astype(np.uint8)  # hanya 4 blok
        cv2.imwrite(small_image_path, small)

        result = run_cli(
            "embed",
            "--image", small_image_path,
            "--watermark", self.watermark_image_path,  # butuh 16 bit > 4 blok
            "--key", self.secret_key,
            "--alpha", "10",
            "--output-watermarked", self.watermarked_path,
            "--output-metadata", self.metadata_path,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error", result.stderr)
        self.assertNotIn("Traceback (most recent call last)", result.stderr)


if __name__ == "__main__":
    unittest.main()
