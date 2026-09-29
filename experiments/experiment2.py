import os
import json
import csv
import cv2
import numpy as np
from app.pipeline import run_embedding_pipeline, run_extraction_pipeline, load_binary_watermark_image
from app.metrics import calculate_ber, calculate_ncc, calculate_psnr
from web_bridge import attack

def run_experiments():
    image_path = "examples/assets/ChatGPT Image 26 Sep 2026, 15.33.33.png"
    watermark_path = "examples/watermark_3238.png"
    
    os.makedirs("experiment_out2", exist_ok=True)
    
    # B. Baseline BER & fraction 1s
    orig_wm = load_binary_watermark_image(watermark_path, 127)
    total_bits = orig_wm.size
    fraction_1_orig = np.sum(orig_wm == 1) / total_bits
    print(f"=== Baseline Logo ===")
    print(f"Ukuran logo: {orig_wm.shape} (total {total_bits} bit)")
    print(f"Fraksi bit 1 pada logo asli: {fraction_1_orig:.4f}")
    
    # A. Eksperimen Key Salah vs Benar (5 kali)
    key_benar = "KEY_BENAR_XYZ"
    keys_salah = [f"KEY_SALAH_{i}" for i in range(5)]
    
    # Embed sekali
    w_path = "experiment_out2/watermarked_key_test.png"
    m_path = "experiment_out2/meta_key_test.json"
    run_embedding_pipeline(
        original_image_path=image_path,
        watermark_image_path=watermark_path,
        key=key_benar,
        alpha=40,
        output_watermarked_path=w_path,
        output_metadata_path=m_path,
        preserve_color=True
    )
    
    print("\n=== A. Fraksi bit 1 dan Kinerja Key ===")
    res_benar = run_extraction_pipeline(w_path, key_benar, m_path, "experiment_out2/ext_benar.png")
    ext_benar = res_benar['extracted_watermark']
    frac_benar = np.sum(ext_benar == 1) / total_bits
    ber_b = calculate_ber(orig_wm, ext_benar)
    nc_b = calculate_ncc(orig_wm, ext_benar)
    print(f"[Key Benar] Fraksi 1: {frac_benar:.4f} | BER: {ber_b:.4f} | NC: {nc_b:.4f}")
    
    sum_ber = 0
    sum_nc = 0
    for k in keys_salah:
        res = run_extraction_pipeline(w_path, k, m_path, f"experiment_out2/ext_{k}.png")
        ext = res['extracted_watermark']
        frac = np.sum(ext == 1) / total_bits
        ber = calculate_ber(orig_wm, ext)
        nc = calculate_ncc(orig_wm, ext)
        print(f"[Key {k}] Fraksi 1: {frac:.4f} | BER: {ber:.4f} | NC: {nc:.4f}")
        sum_ber += ber
        sum_nc += nc
        
    print(f"Rata-rata 5 Key Salah: BER = {sum_ber/5:.4f}, NC = {sum_nc/5:.4f}")
    
    # E. Sweep
    print("\n=== E. Sweep (alpha x redundancy x jpeg) ===")
    alphas = [40, 60, 80, 100, 120]
    redundancies = [1, 3, 5]
    jpegs = [90, 70, 50]
    
    orig_img_cv = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    print(f"Ukuran gambar uji: {orig_img_cv.shape}")
    print(f"Threshold binarisasi: 127")
    
    results = []
    
    for a in alphas:
        for r in redundancies:
            wp = f"experiment_out2/w_{a}_{r}.png"
            mp = f"experiment_out2/m_{a}_{r}.json"
            
            try:
                run_embedding_pipeline(
                    original_image_path=image_path,
                    watermark_image_path=watermark_path,
                    key=key_benar,
                    alpha=a,
                    redundancy=r,
                    output_watermarked_path=wp,
                    output_metadata_path=mp,
                    preserve_color=True
                )
            except Exception as e:
                print(f"Skipping a={a}, r={r} due to error: {e}")
                for j in jpegs:
                    results.append({
                        "alpha": a,
                        "redundancy": r,
                        "attack": "jpeg",
                        "parameter": j,
                        "psnr": "N/A",
                        "nc": "N/A",
                        "ber": "N/A"
                    })
                continue
            
            w_img_cv = cv2.imread(wp, cv2.IMREAD_UNCHANGED)
            psnr_val = calculate_psnr(orig_img_cv, w_img_cv)
            
            for j in jpegs:
                ap = f"experiment_out2/a_{a}_{r}_{j}.png"
                attack({
                    "attack_type": "jpeg",
                    "quality": j,
                    "image_path": wp,
                    "output_path": ap
                })
                
                res_ext = run_extraction_pipeline(ap, key_benar, mp, f"experiment_out2/e_{a}_{r}_{j}.png")
                ext_w = res_ext['extracted_watermark']
                ber_val = calculate_ber(orig_wm, ext_w)
                nc_val = calculate_ncc(orig_wm, ext_w)
                
                results.append({
                    "alpha": a,
                    "redundancy": r,
                    "attack": "jpeg",
                    "parameter": j,
                    "psnr": round(psnr_val, 2),
                    "nc": round(nc_val, 4),
                    "ber": round(ber_val, 4)
                })
                
    csv_file = "experiment_out2/sweep_results.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["alpha", "redundancy", "attack", "parameter", "psnr", "nc", "ber"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Sweep selesai. Disimpan di {csv_file}")

if __name__ == "__main__":
    run_experiments()
