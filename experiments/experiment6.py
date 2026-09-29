import os
import cv2
import numpy as np

from app.watermark import embed_watermark, extract_watermark
from app.metrics import calculate_ncc
from app.pipeline import load_binary_watermark_image, load_grayscale_image
from attack_simulation import attack_brightness_contrast, attack_resize

# Setup
IMAGE_PATH = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
WM64_PATH  = "examples/watermark_64.png"
KEY = "KEY_BENAR_XYZ"

img_gray = load_grayscale_image(IMAGE_PATH)
wm64 = load_binary_watermark_image(WM64_PATH, 127)

w_img, meta = embed_watermark(img_gray, wm64, KEY, alpha=80, redundancy=3)

print("=" * 60)
print("POIN 1: Investigasi Brightness & Contrast (Clipping & Low Mag)")
print("=" * 60)

# Cek clipping pada a=1.3, b=0 dan a=1.0, b=30
for name, a, b in [("Brightness (b=30)", 1.0, 30), ("Contrast (a=1.3)", 1.3, 0)]:
    attacked_float = w_img.astype(np.float64) * a + b
    clipped_0 = np.sum(attacked_float < 0)
    clipped_255 = np.sum(attacked_float > 255)
    total_pixels = w_img.size
    pct_clip = (clipped_0 + clipped_255) / total_pixels * 100
    
    attacked_uint8 = np.clip(attacked_float, 0, 255).astype(np.uint8)
    ext = extract_watermark(attacked_uint8, KEY, meta)
    nc = calculate_ncc(wm64, ext)
    print(f"[{name}]")
    print(f"  Pixel terpotong (<0 atau >255): {clipped_0 + clipped_255} dari {total_pixels} ({pct_clip:.2f}%)")
    print(f"  NC: {nc:.4f}\n")

# Uji magnitude kecil
print("Uji magnitude sangat kecil:")
for b in [5, 10, 20]:
    attacked = attack_brightness_contrast(w_img, 1.0, b)
    ext = extract_watermark(attacked, KEY, meta)
    nc = calculate_ncc(wm64, ext)
    print(f"  Brightness (a=1.0, b={b:2d}) -> NC={nc:.4f}")

for a in [1.05, 1.1, 1.2]:
    attacked = attack_brightness_contrast(w_img, a, 0)
    ext = extract_watermark(attacked, KEY, meta)
    nc = calculate_ncc(wm64, ext)
    print(f"  Contrast   (a={a:.2f}, b=0 ) -> NC={nc:.4f}")


print("\n" + "=" * 60)
print("POIN 3: Bukti Eksekusi Resize (on_size_mismatch='resize')")
print("=" * 60)

attacked_resize = attack_resize(w_img, 0.5)
print(f"Bentuk setelah attack_resize (scale=0.5): {attacked_resize.shape}")

import app.watermark as aw
# Monkey-patch fungsi resize_to_shape khusus untuk mencetak log
orig_resize_to_shape = aw.resize_to_shape

def mock_resize_to_shape(image, target_shape):
    print(f"[BUKTI LOG] fungsi resize_to_shape() dipanggil secara internal!")
    print(f"[BUKTI LOG] -> Meresize citra dari {image.shape} kembali ke {target_shape} sebelum DCT dilakukan.")
    return orig_resize_to_shape(image, target_shape)

aw.resize_to_shape = mock_resize_to_shape

try:
    ext = extract_watermark(attacked_resize, KEY, meta, on_size_mismatch="resize")
    nc = calculate_ncc(wm64, ext)
    print(f"Ekstraksi selesai. NC={nc:.4f}")
finally:
    # kembalikan seperti semula
    aw.resize_to_shape = orig_resize_to_shape
