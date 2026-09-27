#!/usr/bin/env python3
"""
main.py
-------
Entry point CLI untuk proyek watermarking Fase 1.

Modul ini HANYA membaca argumen command-line dan memanggil fungsi yang
sudah ada di app.pipeline. Tidak ada logika algoritma (DCT, PRNG,
embedding, extraction, metrics) yang diimplementasikan ulang di sini.

Command yang tersedia:
    python main.py embed    --image ... --watermark ... --key ... --alpha ...
    python main.py extract  --image ... --metadata ... --key ...
    python main.py evaluate --original ... --watermarked ... --watermark ... --extracted ...
"""

from __future__ import annotations

import argparse
import math
import sys

from app.dct import BLOCK_SIZE
from app.watermark import DEFAULT_BINARIZE_THRESHOLD, CapacityError
from app.pipeline import (
    ImageLoadError,
    MetadataError,
    PipelineError,
    load_binary_watermark_image,
    load_grayscale_image,
    run_embedding_pipeline,
    run_evaluation_pipeline,
    run_extraction_pipeline,
)

# Error yang dianggap "kesalahan input biasa" -- ditampilkan sebagai pesan
# singkat + exit code non-zero, TANPA traceback panjang.
EXPECTED_ERROR_TYPES = (
    ImageLoadError,
    MetadataError,
    PipelineError,
    CapacityError,
    ValueError,
    FileNotFoundError,
)


class CLIValidationError(ValueError):
    """Error validasi argumen CLI (mis. alpha tidak valid)."""


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Robust Blind DCT Watermarking -- Fase 1 CLI (embed / extract / evaluate).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- embed ---
    embed_parser = subparsers.add_parser("embed", help="Sisipkan watermark ke dalam gambar")
    embed_parser.add_argument("--image", required=True, help="Path original image")
    embed_parser.add_argument("--watermark", required=True, help="Path watermark image")
    embed_parser.add_argument("--key", required=True, help="Secret key (tidak akan ditampilkan kembali)")
    embed_parser.add_argument("--alpha", required=True, type=float, help="Embedding margin (harus > 0)")
    embed_parser.add_argument(
        "--output-watermarked",
        default="output/embedded/watermarked.png",
        help="Path output watermarked image (default: %(default)s)",
    )
    embed_parser.add_argument(
        "--output-metadata",
        default="output/embedded/metadata.json",
        help="Path output metadata JSON (default: %(default)s)",
    )
    embed_parser.add_argument(
        "--block-size", type=int, default=BLOCK_SIZE,
        help="Ukuran blok DCT (default: %(default)s)",
    )
    embed_parser.add_argument(
        "--threshold", type=int, default=DEFAULT_BINARIZE_THRESHOLD,
        help="Threshold binarisasi watermark, pixel >= threshold -> 1 (default: %(default)s)",
    )
    embed_parser.add_argument(
        "--redundancy", type=int, default=1,
        help="Fase 2: jumlah salinan blok per bit watermark, untuk ketahanan "
             "cropping via majority vote (default: %(default)s == perilaku Fase 1)",
    )
    embed_parser.add_argument(
        "--preserve-color", action="store_true",
        help="Fase 2: baca --image sebagai warna, tanam watermark hanya di "
             "channel luminance (Y), lalu gabung kembali dengan warna asli "
             "sehingga watermarked image tetap berwarna (default: nonaktif, "
             "gambar diproses sebagai grayscale seperti Fase 1)",
    )

    # --- extract ---
    extract_parser = subparsers.add_parser(
        "extract", help="Ekstrak watermark dari gambar (BLIND -- tidak butuh original image)"
    )
    extract_parser.add_argument("--image", required=True, help="Path watermarked (mungkin sudah di-attack) image")
    extract_parser.add_argument("--metadata", required=True, help="Path metadata JSON hasil embed")
    extract_parser.add_argument("--key", required=True, help="Secret key (tidak akan ditampilkan kembali)")
    extract_parser.add_argument(
        "--output",
        default="output/extracted/watermark.png",
        help="Path output extracted watermark image (default: %(default)s)",
    )
    extract_parser.add_argument(
        "--on-size-mismatch", choices=["raise", "resize", "centered_crop"], default="raise",
        help="Fase 2: strategi ketika ukuran image tidak sama dengan saat embed -- "
             "'raise' (default, perilaku Fase 1), 'resize' (utk resize attack), "
             "'centered_crop' (utk crop murni, butuh --redundancy > 1 saat embed "
             "agar efektif) (default: %(default)s)",
    )

    # --- evaluate ---
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Hitung PSNR, SSIM, NCC, dan BER"
    )
    evaluate_parser.add_argument("--original", required=True, help="Path original image")
    evaluate_parser.add_argument("--watermarked", required=True, help="Path watermarked image")
    evaluate_parser.add_argument("--watermark", required=True, help="Path original watermark image")
    evaluate_parser.add_argument("--extracted", required=True, help="Path extracted watermark image")
    evaluate_parser.add_argument(
        "--threshold", type=int, default=DEFAULT_BINARIZE_THRESHOLD,
        help="Threshold binarisasi watermark, dipakai untuk membaca ulang watermark/extracted image (default: %(default)s)",
    )

    return parser


def _validate_alpha(alpha: float) -> None:
    if alpha is None or math.isnan(alpha) or alpha <= 0:
        raise CLIValidationError(
            f"--alpha tidak valid ({alpha!r}). alpha harus berupa angka > 0."
        )


# ---------------------------------------------------------------------------
# Command handlers -- semua hanya memanggil app.pipeline, tidak ada logika baru
# ---------------------------------------------------------------------------

def cmd_embed(args: argparse.Namespace) -> int:
    _validate_alpha(args.alpha)

    result = run_embedding_pipeline(
        original_image_path=args.image,
        watermark_image_path=args.watermark,
        key=args.key,
        alpha=args.alpha,
        output_watermarked_path=args.output_watermarked,
        output_metadata_path=args.output_metadata,
        block_size=args.block_size,
        binarize_threshold=args.threshold,
        redundancy=args.redundancy,
        preserve_color=args.preserve_color,
    )

    print("Embedding selesai.")
    print(f"  Watermarked image : {result['watermarked_image_path']}")
    print(f"  Metadata          : {result['metadata_path']}")
    print(f"  Watermark shape   : {tuple(result['metadata']['watermark_shape'])}")
    print(f"  Jumlah bit        : {result['metadata']['n_bits']}")
    print(f"  Redundancy        : {result['metadata']['redundancy']}")
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    result = run_extraction_pipeline(
        watermarked_image_path=args.image,
        key=args.key,
        metadata_path=args.metadata,
        output_extracted_watermark_path=args.output,
        on_size_mismatch=args.on_size_mismatch,
    )

    print("Extraction selesai (blind -- tidak menggunakan original image).")
    print(f"  Extracted watermark : {result['extracted_watermark_path']}")
    print(f"  Watermark shape     : {result['extracted_watermark'].shape}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    original_image = load_grayscale_image(args.original)
    watermarked_image = load_grayscale_image(args.watermarked)
    original_watermark = load_binary_watermark_image(args.watermark, threshold=args.threshold)
    extracted_watermark = load_binary_watermark_image(args.extracted, threshold=args.threshold)

    metrics = run_evaluation_pipeline(
        original_image, watermarked_image, original_watermark, extracted_watermark
    )

    psnr_display = "inf" if math.isinf(metrics["psnr"]) else f"{metrics['psnr']:.2f}"

    print("Evaluation Results")
    print("------------------")
    print(f"PSNR : {psnr_display} dB")
    print(f"SSIM : {metrics['ssim']:.4f}")
    print(f"NCC  : {metrics['ncc']:.4f}")
    print(f"BER  : {metrics['ber']:.4f}")
    return 0


COMMAND_HANDLERS = {
    "embed": cmd_embed,
    "extract": cmd_extract,
    "evaluate": cmd_evaluate,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = COMMAND_HANDLERS[args.command]

    try:
        return handler(args)
    except EXPECTED_ERROR_TYPES as exc:
        # Kesalahan input biasa -- pesan singkat, TANPA traceback panjang.
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - safety net kesalahan tak terduga
        print(f"Error tidak terduga: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
