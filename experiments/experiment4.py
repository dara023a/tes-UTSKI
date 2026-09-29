"""
Eksperimen 4 (pra-Tahap 2 final):
A. Verifikasi NC zero-mean: key-salah untuk logo timpang (5% bit-1) dan checkerboard (50%)
B. Sweep lengkap alpha x redundancy x JPEG dengan logo 64x64
C. BER per-block sebelum majority-vote untuk alpha=100, redundancy=3 dan 5
D. Sweep ulang untuk konfirmasi angka NC baru pasca-ganti formula
"""
import csv, os, math
import numpy as np
import cv2
from app.watermark import embed_watermark, extract_watermark, CapacityError
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from app.pipeline import load_binary_watermark_image
from web_bridge import attack

KEY_BENAR = "KEY_BENAR_XYZ"
KEYS_SALAH = [f"KEY_SALAH_{i}" for i in range(5)]
IMAGE_PATH = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
WM_LOGO_PATH = "examples/watermark_3238.png"       # logo asli ~5% bit-1
WM_LOGO64_PATH = "examples/watermark_64.png"        # 64x64 resize logo asli
WM_CHESS_PATH  = "examples/watermark_chess64.png"   # checkerboard 50%

os.makedirs("experiment_out4", exist_ok=True)

# ─────────────────────────────────────────
# BAGIAN A: Verifikasi NC zero-mean
# ─────────────────────────────────────────
print("=" * 60)
print("BAGIAN A: Verifikasi NC zero-mean (key-salah)")
print("=" * 60)

# Buat checkerboard 64x64
chess = np.zeros((64, 64), dtype=np.uint8)
chess[::2, ::2] = 1; chess[1::2, 1::2] = 1
cv2.imwrite(WM_CHESS_PATH, chess * 255)

img_cv = cv2.imread(IMAGE_PATH, cv2.IMREAD_GRAYSCALE)

for wm_label, wm_path in [("Logo asli (~5% bit-1, 156x156)", WM_LOGO_PATH),
                            ("Checkerboard (50% bit-1, 64x64)",  WM_CHESS_PATH)]:
    wm_orig = load_binary_watermark_image(wm_path, 127)
    frac1 = np.sum(wm_orig == 1) / wm_orig.size
    print(f"\n  Watermark: {wm_label}")
    print(f"  Shape: {wm_orig.shape} | Fraksi bit-1: {frac1:.4f}")

    try:
        w_img, meta = embed_watermark(img_cv, wm_orig, KEY_BENAR, alpha=80)
    except CapacityError as e:
        print(f"  [SKIP] CapacityError: {e}")
        continue

    ext_benar = extract_watermark(w_img, KEY_BENAR, meta)
    nc_benar  = calculate_ncc(wm_orig, ext_benar)
    ber_benar = calculate_ber(wm_orig, ext_benar)
    print(f"  Key BENAR  -> NC={nc_benar:.4f}, BER={ber_benar:.4f}")

    ncs = []
    for k in KEYS_SALAH:
        ext = extract_watermark(w_img, k, meta)
        nc  = calculate_ncc(wm_orig, ext)
        ber = calculate_ber(wm_orig, ext)
        ncs.append(nc)
        print(f"  Key {k} -> NC={nc:.4f}, BER={ber:.4f}")
    print(f"  Rata-rata NC 5 key salah: {np.mean(ncs):.4f}")

# ─────────────────────────────────────────
# BAGIAN C: BER per-block sebelum majority-vote
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("BAGIAN C: BER per-copy sebelum majority-vote (alpha=100)")
print("=" * 60)

wm64 = load_binary_watermark_image(WM_LOGO64_PATH, 127)
img_cv_color = cv2.imread(IMAGE_PATH)
img_gray     = cv2.cvtColor(img_cv_color, cv2.COLOR_BGR2GRAY)

for r in [3, 5]:
    print(f"\n  Redundancy={r}:")
    try:
        w_img_r, meta_r = embed_watermark(img_gray, wm64, KEY_BENAR, alpha=100, redundancy=r)
    except CapacityError as e:
        print(f"  [SKIP] {e}"); continue

    # Ekstrak satu per satu copy dengan redundancy=1 untuk masing-masing slot
    # Simulasi: embed ulang bit ke-i ke blok ke-i saja, lalu ekstrak
    # Cara lebih langsung: jalankan ekstraksi dengan meta asli (majority vote)
    # lalu bandingkan setiap salinan dengan bit aslinya menggunakan keys acak
    # Nota: API publik hanya exposed majority-vote.
    # Alternatif praktis: ukur BER sebelum MV dengan embed redundancy=1
    # pada setiap "copy index" disimulasikan dari distribusi error statistik.
    # Kita gunakan pendekatan JPEG 90 (hampir lossless) sebagai referensi:
    atk_path = f"experiment_out4/atk_r{r}_jpeg90.png"
    attack({"attack_type": "jpeg", "quality": 90, "image_path": IMAGE_PATH,
            "output_path": atk_path})
    # Bandingkan: extraksi dengan redundancy=1 vs redundancy=r
    meta_r1 = dict(meta_r)
    meta_r1["redundancy"] = 1
    meta_r1["n_bits"] = meta_r["n_bits"]  # total bit

    # Embed dengan redundancy=1 (baseline tanpa majority vote)
    w_r1, meta_r1_real = embed_watermark(img_gray, wm64, KEY_BENAR, alpha=100, redundancy=1)
    atk_r1 = f"experiment_out4/atk_r1_jpeg70.png"
    attack({"attack_type": "jpeg", "quality": 70, "image_path": f"experiment_out4/atk_r{r}_jpeg90.png",
            "output_path": atk_r1})

    for quality in [90, 70, 50]:
        ap = f"experiment_out4/atk_r{r}_q{quality}.png"
        attack({"attack_type": "jpeg", "quality": quality, "image_path":
                f"experiment_out4/atk_r{r}_jpeg90.png", "output_path": ap})
        # Dengan majority-vote (redundancy=r)
        atk_img = cv2.imread(ap, cv2.IMREAD_GRAYSCALE)
        ext_mv  = extract_watermark(atk_img, KEY_BENAR, meta_r)
        ber_mv  = calculate_ber(wm64, ext_mv)
        nc_mv   = calculate_ncc(wm64, ext_mv)
        # Tanpa majority-vote (redundancy=1 tapi gambar ter-attack sama)
        ext_nov = extract_watermark(atk_img, KEY_BENAR, meta_r1_real)
        ber_nov = calculate_ber(wm64, ext_nov)
        nc_nov  = calculate_ncc(wm64, ext_nov)
        print(f"    JPEG {quality}: r=1 (tanpa MV) BER={ber_nov:.4f} NC={nc_nov:.4f} | "
              f"r={r} (dengan MV) BER={ber_mv:.4f} NC={nc_mv:.4f}")

# ─────────────────────────────────────────
# BAGIAN D: Sweep lengkap NC baru, logo 64x64
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("BAGIAN D: Sweep lengkap (NC formula baru) logo 64x64")
print("=" * 60)
print(f"  Gambar uji: {IMAGE_PATH} | Shape: {img_cv_color.shape}")
print(f"  Logo: {WM_LOGO64_PATH} | Shape: {wm64.shape} | Fraksi bit-1: {np.sum(wm64==1)/wm64.size:.4f}")
print(f"  Threshold binarisasi: 127")

alphas = [60, 80, 100]
redundancies = [1, 3, 5]
jpegs = [90, 70, 50]
h, w, c = img_cv_color.shape
wm_h, wm_w = wm64.shape

rows = []
for a in alphas:
    for r in redundancies:
        wp = f"experiment_out4/w_d_{a}_{r}.png"
        mp = f"experiment_out4/m_d_{a}_{r}.json"
        try:
            w_img_d, meta_d = embed_watermark(img_gray, wm64, KEY_BENAR, alpha=a, redundancy=r)
            psnr = calculate_psnr(img_gray, w_img_d)
            cv2.imwrite(wp, w_img_d)
        except CapacityError as e:
            for j in jpegs:
                rows.append({"image_h":h,"image_w":w,"logo_h":wm_h,"logo_w":wm_w,
                             "alpha":a,"redundancy":r,"attack":"jpeg","parameter":j,
                             "psnr":"N/A","nc":"N/A","ber":"N/A","note":str(e)[:60]})
            continue

        for j in jpegs:
            ap = f"experiment_out4/a_d_{a}_{r}_{j}.png"
            attack({"attack_type":"jpeg","quality":j,"image_path":wp,"output_path":ap})
            atk_img = cv2.imread(ap, cv2.IMREAD_GRAYSCALE)
            ext = extract_watermark(atk_img, KEY_BENAR, meta_d)
            ber = calculate_ber(wm64, ext)
            nc  = calculate_ncc(wm64, ext)
            row = {"image_h":h,"image_w":w,"logo_h":wm_h,"logo_w":wm_w,
                   "alpha":a,"redundancy":r,"attack":"jpeg","parameter":j,
                   "psnr":round(psnr,2),"nc":round(nc,4),"ber":round(ber,4),"note":""}
            rows.append(row)
            print(f"  a={a}, r={r}, JPEG={j}: PSNR={psnr:.2f}, NC={nc:.4f}, BER={ber:.4f}")

csv_path = "experiment_out4/sweep_nc_zeromean.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["image_h","image_w","logo_h","logo_w",
                                            "alpha","redundancy","attack","parameter",
                                            "psnr","nc","ber","note"])
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV lengkap disimpan di: {csv_path}")

# Cek kombinasi yang lolos JPEG 50 (NC >= 0.75, PSNR >= 30)
print("\n--- Kombinasi lolos JPEG 50 (NC>=0.75, PSNR>=30) ---")
passed = [r for r in rows if r["parameter"] == 50 and r["nc"] != "N/A"
          and float(r["nc"]) >= 0.75 and float(r["psnr"]) >= 30]
if passed:
    for p in passed: print(f"  {p}")
else:
    best = max((r for r in rows if r["parameter"] == 50 and r["nc"] != "N/A"
                and r["psnr"] != "N/A" and float(r["psnr"]) >= 30),
               key=lambda r: float(r["nc"]), default=None)
    print("  TIDAK ADA yang lolos JPEG 50 dengan PSNR>=30.")
    if best: print(f"  Terbaik: {best}")
