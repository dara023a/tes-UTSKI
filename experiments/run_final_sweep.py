import os
import pandas as pd
import numpy as np

from app.watermark import embed_watermark, extract_watermark
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from app.pipeline import load_binary_watermark_image, load_grayscale_image
from attack_simulation import (
    attack_jpeg, attack_resize, attack_pure_crop, attack_crop_resize_back,
    attack_gaussian_noise, attack_brightness_contrast
)

KEY = "KEY_BENAR_XYZ"
IMAGE_PATH = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
WM_PATH = "examples/watermark_64.png"
OUTDIR = "experiment_out_final"
os.makedirs(OUTDIR, exist_ok=True)

img_gray = load_grayscale_image(IMAGE_PATH)
wm64 = load_binary_watermark_image(WM_PATH, 127)

alpha = 100
redundancy = 3

print(f"Embedding watermark dengan alpha={alpha}, redundancy={redundancy}...")
w_img, meta = embed_watermark(img_gray, wm64, KEY, alpha=alpha, redundancy=redundancy)
psnr_embed = calculate_psnr(img_gray, w_img)
print(f"PSNR Embedding: {psnr_embed:.2f} dB")

def get_status(nc):
    if not isinstance(nc, float): return "Error"
    if nc >= 0.75: return "Terdeteksi"
    if nc >= 0.40: return "Melemah"
    return "Gagal"

ATTACKS = [
    {"name": "jpeg", "param": 90, "fn": lambda img: attack_jpeg(img, 90), "mode": "raise"},
    {"name": "jpeg", "param": 70, "fn": lambda img: attack_jpeg(img, 70), "mode": "raise"},
    {"name": "jpeg", "param": 50, "fn": lambda img: attack_jpeg(img, 50), "mode": "raise"},
    {"name": "resize", "param": "scale 0.5", "fn": lambda img: attack_resize(img, 0.5), "mode": "resize"},
    {"name": "pure_crop", "param": "10%", "fn": lambda img: attack_pure_crop(img, 10), "mode": "centered_crop"},
    {"name": "pure_crop", "param": "25%", "fn": lambda img: attack_pure_crop(img, 25), "mode": "centered_crop"},
    {"name": "crop_resize_back", "param": "10%", "fn": lambda img: attack_crop_resize_back(img, 10), "mode": "resize"},
    {"name": "crop_resize_back", "param": "25%", "fn": lambda img: attack_crop_resize_back(img, 25), "mode": "resize"},
    {"name": "gaussian_noise", "param": "sigma 10", "fn": lambda img: attack_gaussian_noise(img, 10), "mode": "raise"},
    {"name": "gaussian_noise", "param": "sigma 15", "fn": lambda img: attack_gaussian_noise(img, 15), "mode": "raise"},
    {"name": "gaussian_noise", "param": "sigma 25", "fn": lambda img: attack_gaussian_noise(img, 25), "mode": "raise"},
    {"name": "brightness", "param": "b=10", "fn": lambda img: attack_brightness_contrast(img, 1.0, 10), "mode": "raise"},
    {"name": "brightness", "param": "b=20", "fn": lambda img: attack_brightness_contrast(img, 1.0, 20), "mode": "raise"},
    {"name": "contrast", "param": "a=1.05", "fn": lambda img: attack_brightness_contrast(img, 1.05, 0), "mode": "raise"},
    {"name": "contrast", "param": "a=1.1", "fn": lambda img: attack_brightness_contrast(img, 1.1, 0), "mode": "raise"},
]

rows = []
for atk in ATTACKS:
    attacked = atk["fn"](w_img)
    try:
        ext = extract_watermark(attacked, KEY, meta, on_size_mismatch=atk["mode"])
        nc = calculate_ncc(wm64, ext)
        ber = calculate_ber(wm64, ext)
    except Exception as e:
        nc = "ERR"
        ber = "ERR"
    
    # psnr = calculate_psnr(w_img, attacked) # psnr vs watermarked
    psnr_vs_orig = calculate_psnr(img_gray, attacked) if attacked.shape == img_gray.shape else "N/A"
    
    rows.append({
        "Attack": atk["name"],
        "Parameter": atk["param"],
        "PSNR": round(psnr_vs_orig, 2) if isinstance(psnr_vs_orig, float) else psnr_vs_orig,
        "NC": round(nc, 4) if isinstance(nc, float) else nc,
        "BER": round(ber, 4) if isinstance(ber, float) else ber,
        "Status": get_status(nc)
    })

# Simpan CSV dan XLSX
df = pd.DataFrame(rows)
df.to_csv(f"{OUTDIR}/sweep_final_babV.csv", index=False)
df.to_excel(f"{OUTDIR}/sweep_final_babV.xlsx", index=False)

# EXTREME POINTS
print("\n--- CATATAN TITIK EKSTREM ---")
extremes = [
    ("Brightness", 1.0, 30),
    ("Contrast", 1.3, 0)
]

for name, a, b in extremes:
    attacked_float = w_img.astype(np.float64) * a + b
    clip = np.sum(attacked_float < 0) + np.sum(attacked_float > 255)
    pct_clip = clip / w_img.size * 100
    attacked_uint8 = np.clip(attacked_float, 0, 255).astype(np.uint8)
    ext = extract_watermark(attacked_uint8, KEY, meta)
    nc = calculate_ncc(wm64, ext)
    
    print(f"{name} ekstrem (a={a}, b={b}):")
    print(f"  Piksel clipping: {clip} ({pct_clip:.2f}%)")
    print(f"  NC: {nc:.4f} -> {get_status(nc)}\n")

print(f"Files saved in {OUTDIR}/")
