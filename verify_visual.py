import cv2
import os
from app.pipeline import load_grayscale_image
from attack_simulation import attack_crop_resize_back

IMAGE_PATH = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
ARTIFACT_DIR = r"C:\Users\dazik\.gemini\antigravity-ide\brain\5efcd045-3291-40d6-9b74-22c2ba362b7c\scratch"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

img_gray = load_grayscale_image(IMAGE_PATH)

# Crop+Resize 10%
cr10 = attack_crop_resize_back(img_gray, 10)
cv2.imwrite(os.path.join(ARTIFACT_DIR, "crop_resize_back_10.png"), cr10)

# Crop+Resize 25%
cr25 = attack_crop_resize_back(img_gray, 25)
cv2.imwrite(os.path.join(ARTIFACT_DIR, "crop_resize_back_25.png"), cr25)

# Save original for comparison
cv2.imwrite(os.path.join(ARTIFACT_DIR, "original.png"), img_gray)
