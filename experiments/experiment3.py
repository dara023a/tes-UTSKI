import os
import csv
import cv2
import numpy as np
from app.pipeline import run_embedding_pipeline, run_extraction_pipeline, load_binary_watermark_image
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from web_bridge import attack

def run_experiments():
    image_path = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
    watermark_path = "examples/watermark_3238.png"
    small_wm_path = "examples/watermark_64.png"
    
    # 1. Resize watermark to 64x64
    wm_img = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
    small_wm = cv2.resize(wm_img, (64, 64), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(small_wm_path, small_wm)
    
    os.makedirs("experiment_out3", exist_ok=True)
    
    # B. Baseline BER & fraction 1s
    orig_wm = load_binary_watermark_image(small_wm_path, 127)
    total_bits = orig_wm.size
    print(f"Ukuran logo baru: {orig_wm.shape} (total {total_bits} bit)")
    
    key_benar = "KEY_BENAR_XYZ"
    
    # E. Sweep
    print("\n=== Sweep (alpha x redundancy x jpeg) ===")
    alphas = [60, 80, 100]
    redundancies = [1, 3, 5]
    jpegs = [90, 70, 50]
    
    orig_img_cv = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    results = []
    
    for a in alphas:
        for r in redundancies:
            wp = f"experiment_out3/w_{a}_{r}.png"
            mp = f"experiment_out3/m_{a}_{r}.json"
            
            try:
                run_embedding_pipeline(
                    original_image_path=image_path,
                    watermark_image_path=small_wm_path,
                    key=key_benar,
                    alpha=a,
                    redundancy=r,
                    output_watermarked_path=wp,
                    output_metadata_path=mp,
                    preserve_color=True
                )
            except Exception as e:
                print(f"Skipping a={a}, r={r} due to error: {e}")
                continue
            
            w_img_cv = cv2.imread(wp, cv2.IMREAD_UNCHANGED)
            psnr_val = calculate_psnr(orig_img_cv, w_img_cv)
            
            for j in jpegs:
                ap = f"experiment_out3/a_{a}_{r}_{j}.png"
                attack({
                    "attack_type": "jpeg",
                    "quality": j,
                    "image_path": wp,
                    "output_path": ap
                })
                
                res_ext = run_extraction_pipeline(ap, key_benar, mp, f"experiment_out3/e_{a}_{r}_{j}.png")
                ext_w = res_ext['extracted_watermark']
                ber_val = calculate_ber(orig_wm, ext_w)
                nc_val = calculate_ncc(orig_wm, ext_w)
                
                res_dict = {
                    "alpha": a,
                    "redundancy": r,
                    "attack": "jpeg",
                    "parameter": j,
                    "psnr": round(psnr_val, 2),
                    "nc": round(nc_val, 4),
                    "ber": round(ber_val, 4)
                }
                results.append(res_dict)
                print(res_dict)
                
    csv_file = "experiment_out3/sweep_results.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["alpha", "redundancy", "attack", "parameter", "psnr", "nc", "ber"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Sweep selesai. Disimpan di {csv_file}")
    
    print("\n=== Kombinasi yang lolos JPEG 50 (NC >= 0.75, PSNR >= 30) ===")
    best_nc = -1
    best_comb = None
    passed = []
    for r in results:
        if r['attack'] == 'jpeg' and r['parameter'] == 50:
            if r['nc'] >= 0.75 and r['psnr'] >= 30:
                passed.append(r)
            if r['nc'] > best_nc and r['psnr'] >= 30:
                best_nc = r['nc']
                best_comb = r
                
    if len(passed) > 0:
        for p in passed:
            print(p)
    else:
        print("TIDAK ADA KOMBINASI YANG LOLOS JPEG 50 DENGAN PSNR >= 30.")
        if best_comb:
            print(f"Kombinasi terbaik yang mendekati (PSNR >= 30): {best_comb}")
        else:
            print("Bahkan tidak ada kombinasi dengan PSNR >= 30.")

if __name__ == "__main__":
    run_experiments()
