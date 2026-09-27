"""
key.py
------
Modul untuk mengubah secret key (string) menjadi deterministic seed,
lalu menghasilkan urutan blok pseudo-random yang unik.

Keputusan teknis (dikunci bersama user):
- Seed: SHA-256(key.encode()) -> integer -> dipotong ke 32-bit ->
  dipakai sebagai seed untuk numpy.random.default_rng().
  TIDAK menggunakan built-in Python hash() karena hash() untuk string
  di-randomize per proses (PYTHONHASHSEED) sehingga tidak deterministic
  antar run/antar mesin.
- Urutan blok: rng.permutation(number_of_blocks), diambil sejumlah
  n_bits pertama. Karena berbasis permutasi (bukan sampling dengan
  pengembalian), setiap indeks blok dijamin unik -- tidak ada satu
  blok dipakai untuk lebih dari satu bit watermark.

Secret key TIDAK pernah di-hardcode di modul ini; selalu berasal dari
parameter yang diberikan caller (yang pada akhirnya berasal dari input
user / CLI).
"""

from __future__ import annotations

import hashlib

import numpy as np

SEED_BITS = 32
SEED_MASK = (1 << SEED_BITS) - 1  # 0xFFFFFFFF


def derive_seed(key: str) -> int:
    """Mengubah secret key (string) menjadi integer seed deterministic.

    Langkah:
    1. Encode key ke UTF-8 bytes.
    2. Hash dengan SHA-256 -> digest 256-bit.
    3. Ambil representasi integer dari digest (big-endian, sesuai
       hexdigest -> int base 16).
    4. Mask ke 32-bit terakhir agar cocok dengan rentang seed yang
       diterima numpy secara umum dan tetap deterministic.

    Key string yang sama akan SELALU menghasilkan seed yang sama, pada
    proses/mesin manapun.
    """
    if not isinstance(key, str) or len(key) == 0:
        raise ValueError("secret key harus berupa string non-kosong")

    digest_hex = hashlib.sha256(key.encode("utf-8")).hexdigest()
    full_int = int(digest_hex, 16)
    seed = full_int & SEED_MASK
    return seed


def generate_unique_block_sequence(key: str, number_of_blocks: int, n_bits: int) -> np.ndarray:
    """Menghasilkan urutan indeks blok yang unik dan deterministic,
    berdasarkan secret key, untuk dipakai sebagai lokasi embedding
    (atau lokasi extraction dengan key yang sama).

    Parameters
    ----------
    key: secret key (string), sumber deterministic seed.
    number_of_blocks: total blok yang tersedia pada gambar (setelah
        preprocessing/crop).
    n_bits: jumlah bit watermark yang perlu ditempatkan -- juga jumlah
        indeks blok yang akan diambil dari permutasi.

    Returns
    -------
    np.ndarray berisi n_bits indeks blok, masing-masing unik, dengan
    nilai di rentang [0, number_of_blocks).

    Raises
    ------
    ValueError jika n_bits melebihi number_of_blocks (capacity check
    tingkat rendah; capacity check yang lebih deskriptif untuk user
    dilakukan di watermark.py).
    """
    if n_bits > number_of_blocks:
        raise ValueError(
            f"n_bits ({n_bits}) melebihi number_of_blocks yang tersedia ({number_of_blocks})"
        )
    if n_bits < 0 or number_of_blocks < 0:
        raise ValueError("n_bits dan number_of_blocks harus non-negatif")

    seed = derive_seed(key)
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(number_of_blocks)
    return permutation[:n_bits]


# ---------------------------------------------------------------------------
# Fase 2 addition (opsional, TIDAK mengubah mekanisme di atas): redundancy
# untuk ketahanan terhadap cropping murni. generate_unique_block_sequence()
# di atas tetap dipakai apa adanya ketika redundancy == 1 (default), supaya
# perilaku Fase 1 yang sudah dikunci tidak berubah sama sekali.
# ---------------------------------------------------------------------------

def generate_redundant_block_sequence(
    key: str, number_of_blocks: int, n_bits: int, redundancy: int
) -> np.ndarray:
    """Menghasilkan `redundancy` salinan blok UNIK untuk setiap bit watermark,
    semuanya diturunkan dari SATU permutasi PRNG yang sama (mekanisme
    seed/PRNG identik dengan generate_unique_block_sequence() -- hanya
    jumlah blok yang diambil dari permutasi yang lebih banyak).

    Return: array shape (n_bits, redundancy). Baris i berisi `redundancy`
    indeks blok berbeda yang semuanya akan diisi bit watermark ke-i yang
    SAMA saat embedding. Karena satu permutasi tunggal dipakai untuk
    seluruh alokasi (bukan per-region/per-tile), setiap salinan tersebar
    pseudo-acak di seluruh grid blok -- bukan mengelompok di satu area --
    sehingga sebagian salinan punya peluang lebih besar untuk selamat dari
    cropping parsial.
    """
    if redundancy < 1:
        raise ValueError(f"redundancy harus >= 1, dapat {redundancy!r}")

    total_needed = n_bits * redundancy
    if total_needed > number_of_blocks:
        raise ValueError(
            f"redundancy={redundancy} x n_bits={n_bits} = {total_needed} blok dibutuhkan, "
            f"tetapi hanya {number_of_blocks} blok tersedia."
        )

    seed = derive_seed(key)
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(number_of_blocks)
    selected = permutation[:total_needed]
    return selected.reshape(redundancy, n_bits).T
