"""
dct.py
------
Modul untuk operasi DCT/IDCT berbasis blok 8x8.

Tanggung jawab modul ini:
- Melakukan preprocessing ukuran gambar (crop ke kelipatan block size).
- Membagi gambar grayscale menjadi blok-blok 8x8.
- Melakukan 2D DCT (tipe-II, orthonormal) dan 2D IDCT per blok.
- Menggabungkan kembali blok-blok menjadi gambar utuh.

Keputusan teknis (dikunci bersama user):
- Block size = 8x8.
- DCT menggunakan scipy.fftpack dengan norm='ortho' (standar, bukan
  bagian dari "algoritma watermarking" itu sendiri, hanya operasi
  transformasi dasar yang boleh memakai library).
- Preprocessing ukuran: CROP ke ukuran terbesar yang merupakan
  kelipatan BLOCK_SIZE (bukan padding, bukan resize). Ukuran hasil
  crop harus selalu dikembalikan agar bisa disimpan ke metadata dan
  dipakai kembali secara konsisten saat extraction.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
from scipy.fftpack import dct, idct

BLOCK_SIZE = 8


def dct2(block: np.ndarray) -> np.ndarray:
    """2D DCT tipe-II orthonormal pada satu blok 2D (mis. 8x8).

    Menggunakan scipy.fftpack.dct sebagai operasi dasar (library boleh
    dipakai untuk transformasi standar). Logika pemilihan koefisien,
    embedding, dan extraction TIDAK berada di sini.
    """
    if block.ndim != 2:
        raise ValueError(f"dct2() membutuhkan array 2D, dapat shape {block.shape}")
    return dct(dct(block.astype(np.float64), axis=0, norm="ortho"), axis=1, norm="ortho")


def idct2(coeffs: np.ndarray) -> np.ndarray:
    """Inverse dari dct2(). Mengembalikan blok pixel domain spasial."""
    if coeffs.ndim != 2:
        raise ValueError(f"idct2() membutuhkan array 2D, dapat shape {coeffs.shape}")
    return idct(idct(coeffs, axis=0, norm="ortho"), axis=1, norm="ortho")


def crop_to_multiple_of_block(image: np.ndarray, block_size: int = BLOCK_SIZE) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Crop gambar grayscale (2D) ke ukuran terbesar yang merupakan
    kelipatan block_size, dihitung dari sudut kiri-atas (0,0).

    Mengembalikan (cropped_image, (H_used, W_used)).

    Keputusan: TIDAK melakukan resize/padding. Sisa piksel di kanan/bawah
    yang tidak genap kelipatan block_size dibuang. Ukuran hasil (H_used,
    W_used) WAJIB disimpan di metadata karena extraction harus memakai
    ukuran yang sama persis, bukan menghitung ulang dari file yang
    mungkin sudah berbeda (mis. setelah kompresi ulang).
    """
    if image.ndim != 2:
        raise ValueError(f"crop_to_multiple_of_block() membutuhkan grayscale 2D, dapat shape {image.shape}")

    h, w = image.shape
    h_used = (h // block_size) * block_size
    w_used = (w // block_size) * block_size

    if h_used == 0 or w_used == 0:
        raise ValueError(
            f"Ukuran gambar {h}x{w} terlalu kecil untuk block_size={block_size}"
        )

    cropped = image[:h_used, :w_used]
    return cropped, (h_used, w_used)


def split_into_blocks(image: np.ndarray, block_size: int = BLOCK_SIZE) -> List[np.ndarray]:
    """Membagi gambar (yang ukurannya harus SUDAH kelipatan block_size)
    menjadi list blok 2D berurutan secara row-major (kiri->kanan,
    atas->bawah). Index list ini yang dipakai sebagai "nomor blok"
    oleh key.py / watermark.py.
    """
    h, w = image.shape
    if h % block_size != 0 or w % block_size != 0:
        raise ValueError(
            f"Ukuran gambar {h}x{w} bukan kelipatan block_size={block_size}. "
            "Panggil crop_to_multiple_of_block() terlebih dahulu."
        )

    blocks = []
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            blocks.append(image[i : i + block_size, j : j + block_size].copy())
    return blocks


def reconstruct_from_blocks(blocks: List[np.ndarray], image_shape: Tuple[int, int], block_size: int = BLOCK_SIZE) -> np.ndarray:
    """Kebalikan dari split_into_blocks(): menggabungkan list blok
    (urutan row-major yang sama) menjadi satu gambar dengan shape
    image_shape.
    """
    h, w = image_shape
    if h % block_size != 0 or w % block_size != 0:
        raise ValueError(
            f"image_shape {image_shape} bukan kelipatan block_size={block_size}"
        )

    n_blocks_h = h // block_size
    n_blocks_w = w // block_size
    if len(blocks) != n_blocks_h * n_blocks_w:
        raise ValueError(
            f"Jumlah blok ({len(blocks)}) tidak cocok dengan image_shape {image_shape} "
            f"untuk block_size={block_size} (harus {n_blocks_h * n_blocks_w})"
        )

    image = np.zeros((h, w), dtype=np.float64)
    idx = 0
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            image[i : i + block_size, j : j + block_size] = blocks[idx]
            idx += 1
    return image


def num_blocks(image_shape: Tuple[int, int], block_size: int = BLOCK_SIZE) -> int:
    """Menghitung jumlah blok yang tersedia untuk image_shape tertentu.
    Dipakai untuk capacity check di watermark.py.
    """
    h, w = image_shape
    return (h // block_size) * (w // block_size)
