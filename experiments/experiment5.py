"""
Eksperimen 5 — Grid lengkap kandidat final.

Poin 1: Uji redundancy=1 vs crop (pure_crop & crop_resize_back)
Poin 2: alpha={80,100} x redundancy={3,5} x 8 attack = 32 baris
Poin 3: Tandai baris dengan PSNR < 30 dB
"""
import csv, os, sys, traceback
import numpy as np
import cv2
from app.watermark import embed_watermark, extract_watermark, CapacityError
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from app.pipeline import (
    load_binary_watermark_image, load_grayscale_image,
    run_embedding_pipeline, run_extraction_pipeline,
    save_grayscale_image,
)
from attack_simulation import (
    attack_jpeg, attack_resize, attack_pure_crop, attack_crop_resize_back,
    attack_gaussian_noise, attack_brightness_contrast,
)

KEY = "KEY_BENAR_XYZ"
IMAGE_PATH = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
WM64_PATH  = "examples/watermark_64.png"
OUTDIR     = "experiment_out5"
os.makedirs(OUTDIR, exist_ok=True)

wm64 = load_binary_watermark_image(WM64_PATH, 127)
img_gray = load_grayscale_image(IMAGE_PATH)

# ═══════════════════════════════════════════════════════════════════
# POIN 1: Uji redundancy=1 vs crop
# ═══════════════════════════════════════════════════════════════════
print("=" * 70)
print("POIN 1: Uji redundancy=1 vs crop attacks")
print("=" * 70)

w1, meta1 = embed_watermark(img_gray, wm64, KEY, alpha=100, redundancy=1)
w1_path = f"{OUTDIR}/w_r1.png"
save_grayscale_image(w1_path, w1)
psnr_r1 = calculate_psnr(img_gray, w1)

crop_tests = [
    ("pure_crop",        10),
    ("pure_crop",        25),
    ("crop_resize_back", 10),
    ("crop_resize_back", 25),
]

for atk_name, crop_pct in crop_tests:
    print(f"\n  Attack: {atk_name}, crop_percent={crop_pct}, redundancy=1")
    if atk_name == "pure_crop":
        attacked = attack_pure_crop(w1, crop_pct)
    else:
        attacked = attack_crop_resize_back(w1, crop_pct)

    print(f"    Attacked shape: {attacked.shape} (original: {w1.shape})")
    atk_shape = attacked.shape
    orig_shape = tuple(meta1["processed_image_size"])

    if atk_shape == orig_shape:
        # Same size → extraction langsung bisa
        ext = extract_watermark(attacked, KEY, meta1)
        nc = calculate_ncc(wm64, ext)
        ber = calculate_ber(wm64, ext)
        print(f"    Extraction OK (same size). NC={nc:.4f}, BER={ber:.4f}")
    else:
        # Size mismatch → coba default (raise), lalu centered_crop, lalu resize
        for mode in ["raise", "centered_crop", "resize"]:
            try:
                ext = extract_watermark(attacked, KEY, meta1, on_size_mismatch=mode)
                nc = calculate_ncc(wm64, ext)
                ber = calculate_ber(wm64, ext)
                print(f"    mode='{mode}': NC={nc:.4f}, BER={ber:.4f}")
            except Exception as e:
                print(f"    mode='{mode}': ERROR -> {type(e).__name__}: {e}")

# ═══════════════════════════════════════════════════════════════════
# POIN 2: Grid lengkap — 4 kombinasi × 8 attack = 32 baris
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("POIN 2: Grid lengkap alpha={80,100} x redundancy={3,5} x 8 attack")
print("=" * 70)

ATTACKS = [
    {"name": "jpeg",             "type": "jpeg",             "param_label": "quality=90", "fn": lambda img: attack_jpeg(img, 90)},
    {"name": "jpeg",             "type": "jpeg",             "param_label": "quality=70", "fn": lambda img: attack_jpeg(img, 70)},
    {"name": "jpeg",             "type": "jpeg",             "param_label": "quality=50", "fn": lambda img: attack_jpeg(img, 50)},
    {"name": "resize",           "type": "resize",           "param_label": "scale=0.5",  "fn": lambda img: attack_resize(img, 0.5)},
    {"name": "pure_crop",        "type": "pure_crop",        "param_label": "crop=10%",   "fn": lambda img: attack_pure_crop(img, 10)},
    {"name": "pure_crop",        "type": "pure_crop",        "param_label": "crop=25%",   "fn": lambda img: attack_pure_crop(img, 25)},
    {"name": "crop_resize_back", "type": "crop_resize_back", "param_label": "crop=10%",   "fn": lambda img: attack_crop_resize_back(img, 10)},
    {"name": "crop_resize_back", "type": "crop_resize_back", "param_label": "crop=25%",   "fn": lambda img: attack_crop_resize_back(img, 25)},
    {"name": "gaussian_noise",   "type": "gaussian_noise",   "param_label": "sigma=15",   "fn": lambda img: attack_gaussian_noise(img, sigma=15, seed=42)},
    {"name": "brightness",       "type": "brightness",       "param_label": "alpha=1.0,beta=30", "fn": lambda img: attack_brightness_contrast(img, alpha=1.0, beta=30)},
    {"name": "contrast",         "type": "contrast",         "param_label": "alpha=1.3,beta=0",  "fn": lambda img: attack_brightness_contrast(img, alpha=1.3, beta=0)},
]

COMBOS = [
    (80, 3), (80, 5),
    (100, 3), (100, 5),
]

h, w = img_gray.shape[:2]
wm_h, wm_w = wm64.shape

rows = []
for alpha, red in COMBOS:
    print(f"\n--- alpha={alpha}, redundancy={red} ---")
    try:
        w_img, meta = embed_watermark(img_gray, wm64, KEY, alpha=alpha, redundancy=red)
    except CapacityError as e:
        print(f"  [SKIP] CapacityError: {e}")
        for atk in ATTACKS:
            rows.append({
                "image_size": f"{h}x{w}", "logo_size": f"{wm_h}x{wm_w}",
                "alpha": alpha, "redundancy": red,
                "attack": atk["name"], "parameter": atk["param_label"],
                "psnr": "N/A", "nc": "N/A", "ber": "N/A",
                "psnr_ok": "N/A", "note": "CapacityError",
            })
        continue

    psnr_embed = calculate_psnr(img_gray, w_img)
    psnr_ok_embed = "YES" if psnr_embed >= 30 else "NO(<30)"

    for atk in ATTACKS:
        attacked = atk["fn"](w_img)
        atk_shape = attacked.shape
        orig_shape = tuple(meta["processed_image_size"])

        # Pilih mode ekstraksi sesuai tipe attack
        if atk["type"] == "pure_crop":
            mode = "centered_crop"
        elif atk["type"] == "resize":
            mode = "resize"
        elif atk["type"] == "crop_resize_back":
            mode = "resize"  # crop+resize kembali ke ukuran asli, tapi bisa sedikit beda
        else:
            mode = "raise"  # jpeg, gaussian, brightness, contrast → same size

        try:
            ext = extract_watermark(attacked, KEY, meta, on_size_mismatch=mode)
            nc = calculate_ncc(wm64, ext)
            ber = calculate_ber(wm64, ext)
            note = ""
        except Exception as e:
            nc = "ERR"
            ber = "ERR"
            note = f"{type(e).__name__}: {str(e)[:80]}"

        row = {
            "image_size": f"{h}x{w}",
            "logo_size": f"{wm_h}x{wm_w}",
            "alpha": alpha,
            "redundancy": red,
            "attack": atk["name"],
            "parameter": atk["param_label"],
            "psnr": round(psnr_embed, 2),
            "nc": round(nc, 4) if isinstance(nc, float) else nc,
            "ber": round(ber, 4) if isinstance(ber, float) else ber,
            "psnr_ok": psnr_ok_embed,
            "note": note,
        }
        rows.append(row)
        status = f"NC={row['nc']}, BER={row['ber']}, PSNR={row['psnr']} [{row['psnr_ok']}]"
        print(f"  {atk['name']:20s} {atk['param_label']:25s} -> {status}  {note}")

# ═══════════════════════════════════════════════════════════════════
# Tulis CSV
# ═══════════════════════════════════════════════════════════════════
csv_path = f"{OUTDIR}/grid_final.csv"
fieldnames = ["image_size","logo_size","alpha","redundancy","attack","parameter",
              "psnr","nc","ber","psnr_ok","note"]
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV disimpan di: {csv_path}")

# ═══════════════════════════════════════════════════════════════════
# Ringkasan baris yang gugur PSNR
# ═══════════════════════════════════════════════════════════════════
print("\n--- Baris yang gugur PSNR (<30 dB) meskipun NC bagus ---")
for r in rows:
    if r["psnr_ok"] == "NO(<30)" and isinstance(r["nc"], float) and r["nc"] >= 0.40:
        print(f"  alpha={r['alpha']}, r={r['redundancy']}, "
              f"attack={r['attack']} {r['parameter']}: PSNR={r['psnr']}, NC={r['nc']}")

no_psnr_issue = all(r["psnr_ok"] != "NO(<30)" for r in rows if isinstance(r["nc"], float) and r["nc"] >= 0.40)
if no_psnr_issue:
    print("  (Tidak ada baris dengan NC>=0.40 yang gugur PSNR)")
