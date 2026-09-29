#!/usr/bin/env python3
"""
attack_simulation.py
---------------------
Skrip orkestrasi untuk bab analisis ketahanan (JPEG compression, resize,
cropping) -- judul penelitian: "Robust Watermarking Blind Berbasis DCT
Frekuensi Menengah ... Analisis Ketahanan terhadap Kompresi JPEG, Resize,
dan Cropping".

TIDAK mengimplementasikan ulang algoritma apapun. Hanya memanggil:
- app.pipeline.run_embedding_pipeline()  (sekali, di awal)
- app.watermark.extract_watermark()      (berulang, per skenario attack)
- app.metrics.calculate_ber / calculate_ncc / calculate_psnr

Attack itu sendiri (JPEG re-encode, resize, crop) dilakukan di sini
memakai OpenCV apa adanya -- bukan bagian dari "algoritma watermarking",
sama seperti resize_to_shape() di app.watermark dipakai untuk resync,
bukan bagian dari algoritma DCT.

Empat kelompok skenario yang diuji:
1. JPEG compression pada beberapa quality level (ukuran gambar tidak
   berubah -> extract_watermark() dipanggil tanpa parameter khusus).
2. Resize murni (gambar diskalakan ke ukuran lain, TIDAK dikembalikan)
   -> extract_watermark(..., on_size_mismatch="resize").
3. Crop lalu di-resize balik ke ukuran semula (skenario umum di
   literatur/benchmark blind_watermark) -> ukuran sudah balik ke
   processed_image_size, extract_watermark() dipanggil tanpa parameter
   khusus juga.
4. Crop murni TANPA resize balik (kanvas mengecil) -> extract_watermark(
   ..., on_size_mismatch="centered_crop"). Efektivitasnya bergantung pada
   redundancy > 1 yang dipakai saat embedding.

Output:
- CSV berisi seluruh baris hasil (attack_type, parameter, ber, ncc, psnr)
- PNG grafik BER vs parameter untuk tiap kelompok attack (4 file)
- Ringkasan di stdout

Cara pakai:
    python attack_simulation.py \
        --image input/images/cat.png \
        --watermark input/watermarks/panda_128.png \
        --key "secret-key-kalian" \
        --alpha 40 \
        --redundancy 5 \
        --preserve-color \
        --output-dir output/attack_report
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Dict, List, Optional

import cv2
import matplotlib

matplotlib.use("Agg")  # tidak butuh display, langsung simpan ke file
import matplotlib.pyplot as plt
import numpy as np

from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from app.pipeline import (
    ImageLoadError,
    MetadataError,
    PipelineError,
    load_binary_watermark_image,
    load_color_image,
    run_embedding_pipeline,
    split_luma_chroma,
)
from app.watermark import CapacityError, extract_watermark


# ---------------------------------------------------------------------------
# Grid parameter attack -- ubah di sini kalau mau menambah/mengurangi titik
# uji (mis. lebih banyak level JPEG quality).
# ---------------------------------------------------------------------------

JPEG_QUALITIES = [90, 80, 70, 50, 30, 10]
RESIZE_SCALES = [0.9, 0.75, 0.5, 0.25]
CROP_RESIZE_BACK_PERCENTAGES = [5, 10, 20, 30]
PURE_CROP_PERCENTAGES = [5, 10, 20, 30]


# ---------------------------------------------------------------------------
# Helper: mengambil channel yang benar (Y kalau color_mode, grayscale
# kalau tidak) dari sebuah array hasil attack, supaya konsisten dengan
# apa yang diharapkan extract_watermark().
# ---------------------------------------------------------------------------

def _to_extraction_channel(image_array: np.ndarray, is_color: bool) -> np.ndarray:
    if is_color:
        y, _cr, _cb = split_luma_chroma(image_array)
        return y
    return image_array.astype(np.float64)


def _extract_and_score(
    attacked_image: np.ndarray,
    is_color: bool,
    key: str,
    metadata: Dict,
    original_watermark: np.ndarray,
    on_size_mismatch: str = "raise",
) -> Dict[str, float]:
    channel = _to_extraction_channel(attacked_image, is_color)
    try:
        extracted = extract_watermark(channel, key, metadata, on_size_mismatch=on_size_mismatch)
    except ValueError as exc:
        # Attack terlalu ekstrem / kombinasi mode salah -- dicatat sebagai
        # kegagalan total (BER=1.0), bukan menghentikan seluruh simulasi.
        return {"ber": 1.0, "ncc": 0.0, "error": str(exc)}

    ber = float(calculate_ber(original_watermark, extracted))
    ncc = float(calculate_ncc(original_watermark, extracted))
    return {"ber": ber, "ncc": ncc, "error": ""}


# ---------------------------------------------------------------------------
# Definisi attack individual. Semua menerima watermarked_image (array,
# grayscale ATAU BGR sesuai is_color) dan mengembalikan array hasil attack.
# ---------------------------------------------------------------------------

def attack_jpeg(image: np.ndarray, quality: int) -> np.ndarray:
    """Re-encode sebagai JPEG di memori (tanpa file sementara) lalu decode
    ulang -- inilah bentuk kompresi JPEG yang sebenarnya (lossy), bukan
    simulasi noise buatan."""
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Gagal encode JPEG")
    flag = cv2.IMREAD_COLOR if image.ndim == 3 else cv2.IMREAD_GRAYSCALE
    decoded = cv2.imdecode(encoded, flag)
    return decoded.astype(np.float64) if decoded.ndim == 2 else decoded


def attack_resize(image: np.ndarray, scale: float) -> np.ndarray:
    """Resize murni -- HASIL TETAP di ukuran baru (tidak dikembalikan)."""
    h, w = image.shape[:2]
    new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    return resized


def attack_crop_resize_back(image: np.ndarray, crop_percent: float) -> np.ndarray:
    """Crop crop_percent dari SETIAP sisi (kiri/kanan/atas/bawah), lalu
    resize balik ke ukuran semula."""
    h, w = image.shape[:2]
    dh, dw = int(h * crop_percent / 100 / 2), int(w * crop_percent / 100 / 2)
    cropped = image[dh : h - dh, dw : w - dw]
    resized_back = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_CUBIC)
    return resized_back


def attack_pure_crop(image: np.ndarray, crop_percent: float) -> np.ndarray:
    """Crop crop_percent dari SETIAP sisi, TANPA resize balik -- kanvas
    hasil lebih kecil dari aslinya."""
    h, w = image.shape[:2]
    dh, dw = int(h * crop_percent / 100 / 2), int(w * crop_percent / 100 / 2)
    return image[dh : h - dh, dw : w - dw]

def attack_gaussian_noise(image: np.ndarray, sigma: float, seed: Optional[int] = None) -> np.ndarray:
    """Menambahkan noise gaussian ke gambar."""
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    noise = rng.normal(0, sigma, image.shape)
    attacked = image.astype(np.float64) + noise
    return np.clip(attacked, 0, 255).astype(np.uint8)

def attack_brightness_contrast(image: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """Mengubah contrast (alpha) dan brightness (beta)."""
    attacked = image.astype(np.float64) * alpha + beta
    return np.clip(attacked, 0, 255).astype(np.uint8)



# ---------------------------------------------------------------------------
# Orkestrasi utama
# ---------------------------------------------------------------------------

def run_all_attacks(
    image_path: str,
    watermark_path: str,
    key: str,
    alpha: float,
    output_dir: str,
    redundancy: int = 1,
    preserve_color: bool = False,
) -> List[Dict]:
    os.makedirs(output_dir, exist_ok=True)
    watermarked_path = os.path.join(output_dir, "watermarked.png")
    metadata_path = os.path.join(output_dir, "metadata.json")

    embed_result = run_embedding_pipeline(
        original_image_path=image_path,
        watermark_image_path=watermark_path,
        key=key,
        alpha=alpha,
        output_watermarked_path=watermarked_path,
        output_metadata_path=metadata_path,
        redundancy=redundancy,
        preserve_color=preserve_color,
    )
    metadata = embed_result["metadata"]
    watermarked_image = embed_result["watermarked_image"]
    original_watermark = load_binary_watermark_image(
        watermark_path, threshold=metadata["binarize_threshold"]
    )

    is_color = preserve_color
    watermarked_ref_channel = _to_extraction_channel(watermarked_image, is_color)

    rows: List[Dict] = []

    # --- 1. JPEG compression ---
    for q in JPEG_QUALITIES:
        attacked = attack_jpeg(watermarked_image, q)
        score = _extract_and_score(attacked, is_color, key, metadata, original_watermark, "raise")
        attacked_channel = _to_extraction_channel(attacked, is_color)
        psnr = calculate_psnr(watermarked_ref_channel, attacked_channel)
        rows.append({"attack_type": "jpeg", "parameter": q, "psnr_vs_watermarked": psnr, **score})
        print(f"[JPEG q={q:>3}]                BER={score['ber']:.4f}  NCC={score['ncc']:.4f}  PSNR={psnr:.2f}dB")

    # --- 2. Resize murni ---
    for scale in RESIZE_SCALES:
        attacked = attack_resize(watermarked_image, scale)
        score = _extract_and_score(attacked, is_color, key, metadata, original_watermark, "resize")
        rows.append({"attack_type": "resize", "parameter": scale, "psnr_vs_watermarked": None, **score})
        print(f"[Resize scale={scale:>4}]         BER={score['ber']:.4f}  NCC={score['ncc']:.4f}")

    # --- 3. Crop lalu resize balik ---
    for pct in CROP_RESIZE_BACK_PERCENTAGES:
        attacked = attack_crop_resize_back(watermarked_image, pct)
        score = _extract_and_score(attacked, is_color, key, metadata, original_watermark, "raise")
        attacked_channel = _to_extraction_channel(attacked, is_color)
        psnr = calculate_psnr(watermarked_ref_channel, attacked_channel)
        rows.append({"attack_type": "crop_resize_back", "parameter": pct, "psnr_vs_watermarked": psnr, **score})
        print(f"[Crop+resize-back {pct:>2}%]      BER={score['ber']:.4f}  NCC={score['ncc']:.4f}  PSNR={psnr:.2f}dB")

    # --- 4. Crop murni (tanpa resize balik) ---
    for pct in PURE_CROP_PERCENTAGES:
        attacked = attack_pure_crop(watermarked_image, pct)
        score = _extract_and_score(attacked, is_color, key, metadata, original_watermark, "centered_crop")
        rows.append({"attack_type": "pure_crop", "parameter": pct, "psnr_vs_watermarked": None, **score})
        print(f"[Pure crop {pct:>2}%]             BER={score['ber']:.4f}  NCC={score['ncc']:.4f}")

    return rows


# ---------------------------------------------------------------------------
# Output: CSV + grafik
# ---------------------------------------------------------------------------

def save_csv(rows: List[Dict], path: str) -> None:
    fieldnames = ["attack_type", "parameter", "ber", "ncc", "psnr_vs_watermarked", "error"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def save_charts(rows: List[Dict], output_dir: str) -> None:
    groups = {
        "jpeg": ("JPEG Quality", "BER vs Kualitas Kompresi JPEG", "ber_vs_jpeg_quality.png"),
        "resize": ("Skala Resize", "BER vs Skala Resize (murni)", "ber_vs_resize_scale.png"),
        "crop_resize_back": ("Persentase Crop (%)", "BER vs Crop + Resize Balik", "ber_vs_crop_resize_back.png"),
        "pure_crop": ("Persentase Crop (%)", "BER vs Crop Murni (tanpa resize balik)", "ber_vs_pure_crop.png"),
    }
    for attack_type, (xlabel, title, filename) in groups.items():
        subset = [r for r in rows if r["attack_type"] == attack_type]
        if not subset:
            continue
        subset.sort(key=lambda r: r["parameter"])
        xs = [r["parameter"] for r in subset]
        bers = [r["ber"] for r in subset]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(xs, bers, marker="o", color="#c0392b")
        ax.axhline(0.5, color="gray", linestyle="--", linewidth=1, label="BER=0.5 (setara acak)")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Bit Error Rate (BER)")
        ax.set_title(title)
        ax.set_ylim(-0.02, 1.02)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, filename), dpi=150)
        plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Jalankan seluruh simulasi attack (JPEG/resize/crop) untuk bab analisis ketahanan."
    )
    parser.add_argument("--image", required=True, help="Path original image (cover)")
    parser.add_argument("--watermark", required=True, help="Path watermark image (biner/akan dibinarisasi)")
    parser.add_argument("--key", required=True, help="Secret key")
    parser.add_argument("--alpha", required=True, type=float, help="Embedding margin")
    parser.add_argument("--redundancy", type=int, default=1, help="Jumlah salinan blok per bit (default: 1)")
    parser.add_argument("--preserve-color", action="store_true", help="Pertahankan warna asli (channel Y saja yang di-watermark)")
    parser.add_argument("--output-dir", default="output/attack_report", help="Folder output CSV + grafik")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        rows = run_all_attacks(
            image_path=args.image,
            watermark_path=args.watermark,
            key=args.key,
            alpha=args.alpha,
            output_dir=args.output_dir,
            redundancy=args.redundancy,
            preserve_color=args.preserve_color,
        )
    except (ImageLoadError, MetadataError, PipelineError, CapacityError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    csv_path = os.path.join(args.output_dir, "attack_results.csv")
    save_csv(rows, csv_path)
    save_charts(rows, args.output_dir)

    print()
    print(f"Selesai. {len(rows)} skenario diuji.")
    print(f"  CSV    : {csv_path}")
    print(f"  Grafik : {args.output_dir}/ber_vs_*.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
