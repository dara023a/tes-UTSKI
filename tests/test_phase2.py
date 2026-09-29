import sys
import numpy as np

from app.watermark import embed_watermark, extract_watermark, CapacityError
from attack_simulation import attack_gaussian_noise
from app.metrics import calculate_ber, calculate_ncc


def dummy_images():
    """256x256 grayscale image + 16x16 balanced binary watermark."""
    rng = np.random.default_rng(0)
    # Gambar noise agar blok DCT tidak seragam
    image = rng.integers(50, 200, (256, 256), dtype=np.uint8)
    # Watermark checkerboard 50% bit=1 -- lebih susah ditebak key salah
    wm = np.zeros((16, 16), dtype=np.uint8)
    wm[::2, ::2] = 1
    wm[1::2, 1::2] = 1   # 128 bit=1 dari 256 total
    return image, wm


def _assert(condition, msg=""):
    if not condition:
        raise AssertionError(msg or "Assertion failed")


# ---------------------------------------------------------------------------
# Test 1: Embed + Extract dengan key benar harus sempurna
# ---------------------------------------------------------------------------
def test_embed_extract_benar():
    image, wm = dummy_images()
    w_img, meta = embed_watermark(image, wm, "TESTKEY", alpha=100, redundancy=3)
    ext_wm = extract_watermark(w_img, "TESTKEY", meta)
    ber = calculate_ber(wm, ext_wm)
    ncc = calculate_ncc(wm, ext_wm)
    _assert(ber == 0.0, f"BER harus 0.0, dapat {ber}")
    _assert(ncc == 1.0, f"NC harus 1.0, dapat {ncc}")


# ---------------------------------------------------------------------------
# Test 2: Ekstraksi key salah harus menghasilkan NC < 0.10 (formula zero-mean)
# ---------------------------------------------------------------------------
def test_key_salah_gagal():
    image, wm = dummy_images()
    w_img, meta = embed_watermark(image, wm, "BENAR", alpha=100, redundancy=3)
    ext_wm = extract_watermark(w_img, "SALAH", meta)
    ncc = calculate_ncc(wm, ext_wm)
    # Dengan zero-mean NC, output acak menghasilkan NC mendekati 0.
    # Disamakan dengan batas ambang status 'Gagal' produksi (NC < 0.40).
    _assert(ncc < 0.40, f"NC key salah harus < 0.40 (ambang Gagal), dapat {ncc:.4f}")


# ---------------------------------------------------------------------------
# Test 3: Watermark terlalu besar akan ditolak dengan CapacityError
# ---------------------------------------------------------------------------
def test_kapasitas_ditolak():
    image, wm = dummy_images()
    # 256x256 = 1024 blok DCT. watermark 16x16 = 256 bit.
    # Jika kita punya citra 128x128 = 256 blok, watermark 20x20 = 400 bit -> CapacityError
    img_small = np.zeros((128, 128), dtype=np.uint8)
    wm_large = np.zeros((20, 20), dtype=np.uint8)
    
    raised = False
    try:
        embed_watermark(img_small, wm_large, "KEY", alpha=100, redundancy=1)
    except CapacityError:
        raised = True
    _assert(raised, "CapacityError seharusnya di-raise untuk watermark yang lebih besar dari jumlah blok citra")

# ---------------------------------------------------------------------------
# Test 6: Redundancy berlebih yang melampaui sisa kapasitas citra akan ditolak
# ---------------------------------------------------------------------------
def test_kapasitas_redundancy_ditolak():
    image, wm = dummy_images()
    # 256x256 = 1024 blok DCT. watermark 16x16 = 256 bit.
    # redundancy=5 butuh 256*5=1280 slot > 1024 -> CapacityError
    raised = False
    try:
        embed_watermark(image, wm, "KEY", alpha=100, redundancy=5)
    except CapacityError:
        raised = True
    _assert(raised, "CapacityError seharusnya di-raise untuk redundancy=5 pada gambar 256x256 karena 1280 > 1024")


# ---------------------------------------------------------------------------
# Test 4: Parameter attack berpengaruh pada kualitas ekstraksi
# ---------------------------------------------------------------------------
def test_parameter_attack_berpengaruh():
    image, wm = dummy_images()
    w_img, meta = embed_watermark(image, wm, "KEY", alpha=100, redundancy=3)

    atk_ringan = attack_gaussian_noise(w_img, sigma=2, seed=42)
    ext1 = extract_watermark(atk_ringan, "KEY", meta)
    nc1 = calculate_ncc(wm, ext1)

    atk_berat = attack_gaussian_noise(w_img, sigma=80, seed=42)
    ext2 = extract_watermark(atk_berat, "KEY", meta)
    nc2 = calculate_ncc(wm, ext2)

    _assert(nc1 > nc2, f"NC attack ringan ({nc1:.4f}) harus > NC attack berat ({nc2:.4f})")


# ---------------------------------------------------------------------------
# Test 5: Fungsi NC (zero-mean) menghasilkan angka sesuai ambang status deteksi
# ---------------------------------------------------------------------------
def test_status_deteksi_sesuai_ambang():
    # Array float kontinu agar zero-mean NC bisa diuji dengan presisi.
    rng = np.random.default_rng(99)
    base = rng.standard_normal(400)   # "watermark asli" distribusi normal

    # Terdeteksi (NC >= 0.75): korelasi tinggi (noise kecil)
    noisy_high = base + rng.standard_normal(400) * 0.1
    nc_high = calculate_ncc(base, noisy_high)
    _assert(nc_high >= 0.75, f"NC sinyal kuat harus >= 0.75, dapat {nc_high:.4f}")

    # Melemah (0.40 <= NC < 0.75): campuran sinyal asli + noise sedang
    mixed = base * 0.6 + rng.standard_normal(400) * 0.8
    nc_mid = calculate_ncc(base, mixed)
    _assert(0.40 <= nc_mid < 0.75, f"NC melemah harus 0.40-0.75, dapat {nc_mid:.4f}")

    # Gagal (NC < 0.40): sinyal independen -- zero-mean NC mendekati 0
    independent = rng.standard_normal(400)
    nc_fail = calculate_ncc(base, independent)
    _assert(abs(nc_fail) < 0.40, f"NC independen harus < 0.40, dapat {nc_fail:.4f}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_embed_extract_benar,
        test_key_salah_gagal,
        test_kapasitas_ditolak,
        test_parameter_attack_berpengaruh,
        test_status_deteksi_sesuai_ambang,
        test_kapasitas_redundancy_ditolak,
    ]
    passed = 0
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  [PASS] {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  [FAIL] {fn.__name__}: {exc}")
            failed += 1
    print(f"\n{passed}/{len(tests)} tests passed.")
    sys.exit(0 if failed == 0 else 1)
