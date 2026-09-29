import os
import json
import cv2
import numpy as np
from app.pipeline import run_embedding_pipeline, run_extraction_pipeline, load_binary_watermark_image
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from web_bridge import attack, _json_safe

def run_experiments():
    image_path = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
    watermark_path = "examples/watermark_3238.png"
    
    os.makedirs("experiment_out", exist_ok=True)
    
    # 2. Eksperimen Key
    print("=== Eksperimen 2: Uji Key ===")
    key_a = "KUNCI_RAHASIA_123"
    key_b = "KUNCI_SALAH_999"
    
    res_embed = run_embedding_pipeline(
        original_image_path=image_path,
        watermark_image_path=watermark_path,
        key=key_a,
        alpha=40,
        output_watermarked_path="experiment_out/watermarked_keyA.png",
        output_metadata_path="experiment_out/meta_keyA.json",
        preserve_color=True
    )
    
    orig_wm = load_binary_watermark_image(watermark_path, 127)
    
    res_ext_A = run_extraction_pipeline(
        watermarked_image_path="experiment_out/watermarked_keyA.png",
        key=key_a,
        metadata_path="experiment_out/meta_keyA.json",
        output_extracted_watermark_path="experiment_out/ext_keyA.png"
    )
    ber_A = calculate_ber(orig_wm, res_ext_A['extracted_watermark'])
    nc_A = calculate_ncc(orig_wm, res_ext_A['extracted_watermark'])
    
    res_ext_B = run_extraction_pipeline(
        watermarked_image_path="experiment_out/watermarked_keyA.png",
        key=key_b,
        metadata_path="experiment_out/meta_keyA.json",
        output_extracted_watermark_path="experiment_out/ext_keyB.png"
    )
    ber_B = calculate_ber(orig_wm, res_ext_B['extracted_watermark'])
    nc_B = calculate_ncc(orig_wm, res_ext_B['extracted_watermark'])
    
    print(f"Extract dengan Key A (Benar): BER = {ber_A:.4f}, NC = {nc_A:.4f}")
    print(f"Extract dengan Key B (Salah): BER = {ber_B:.4f}, NC = {nc_B:.4f}")
    
    # 3. Eksperimen Attack Web Bridge
    print("\n=== Eksperimen 3: Web Bridge Attack Params ===")
    attacks = [
        {"attack_type": "jpeg", "quality": 90},
        {"attack_type": "jpeg", "quality": 70},
        {"attack_type": "jpeg", "quality": 50},
        {"attack_type": "resize", "scale": 0.5},
        {"attack_type": "pure_crop", "crop_percent": 10},
        {"attack_type": "crop_resize_back", "crop_percent": 10}
    ]
    for i, atk in enumerate(attacks):
        payload = {
            "image_path": "experiment_out/watermarked_keyA.png",
            "output_path": f"experiment_out/attack_{i}.png"
        }
        payload.update(atk)
        try:
            res = attack(payload)
            print(f"Input: {atk} -> Output parameter diterima Python: {res['parameter']}")
        except Exception as e:
            print(f"Input: {atk} -> Error: {e}")
            
    # 4. Eksperimen Alpha
    print("\n=== Eksperimen 4: Variasi Alpha + JPEG 70 ===")
    alphas = [10, 40, 80]
    
    orig_img_cv = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    for a in alphas:
        w_path = f"experiment_out/watermarked_alpha_{a}.png"
        m_path = f"experiment_out/meta_alpha_{a}.json"
        res_a = run_embedding_pipeline(
            original_image_path=image_path,
            watermark_image_path=watermark_path,
            key=key_a,
            alpha=a,
            output_watermarked_path=w_path,
            output_metadata_path=m_path,
            preserve_color=True
        )
        
        # calculate PSNR (original vs watermarked)
        w_img_cv = cv2.imread(w_path, cv2.IMREAD_UNCHANGED)
        psnr_val = calculate_psnr(orig_img_cv, w_img_cv)
        
        # run jpeg 70 attack via bridge
        attack_payload = {
            "attack_type": "jpeg",
            "quality": 70,
            "image_path": w_path,
            "output_path": f"experiment_out/attacked_alpha_{a}.png"
        }
        attack(attack_payload)
        
        # extract
        res_ext = run_extraction_pipeline(
            watermarked_image_path=attack_payload["output_path"],
            key=key_a,
            metadata_path=m_path,
            output_extracted_watermark_path=f"experiment_out/ext_alpha_{a}.png"
        )
        
        ber_val = calculate_ber(orig_wm, res_ext['extracted_watermark'])
        nc_val = calculate_ncc(orig_wm, res_ext['extracted_watermark'])
        
        print(f"Alpha {a}: PSNR = {psnr_val:.2f} dB, Setelah JPEG 70 -> BER = {ber_val:.4f}, NC = {nc_val:.4f}")

if __name__ == "__main__":
    run_experiments()
