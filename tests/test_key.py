"""
Unit test untuk app/key.py (memakai unittest bawaan Python).

Mencakup (sesuai yang diminta):
3. Deterministic seed
4. Deterministic PRNG sequence
5. Uniqueness of selected block indices
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from app.key import derive_seed, generate_unique_block_sequence, SEED_MASK


class TestDeriveSeed(unittest.TestCase):
    def test_deterministic_same_key(self):
        seed1 = derive_seed("my-secret-key")
        seed2 = derive_seed("my-secret-key")
        self.assertEqual(seed1, seed2)

    def test_differs_for_different_keys(self):
        seed1 = derive_seed("my-secret-key")
        seed2 = derive_seed("my-secret-key-2")
        self.assertNotEqual(seed1, seed2)

    def test_within_32bit_range(self):
        seed = derive_seed("some-arbitrary-key-!@#$%^&*()")
        self.assertGreaterEqual(seed, 0)
        self.assertLessEqual(seed, SEED_MASK)

    def test_rejects_empty_key(self):
        with self.assertRaises(ValueError):
            derive_seed("")

    def test_not_using_builtin_hash(self):
        # built-in hash() untuk string di-randomize per proses
        # (PYTHONHASHSEED acak secara default), jadi tidak deterministic
        # antar run/mesin. Pastikan derive_seed tidak sekadar
        # membungkus hash() bawaan.
        key = "check-not-builtin-hash"
        seed = derive_seed(key)
        self.assertNotEqual(seed, hash(key) & SEED_MASK)


class TestGenerateUniqueBlockSequence(unittest.TestCase):
    def test_deterministic(self):
        seq1 = generate_unique_block_sequence("my-secret-key", number_of_blocks=100, n_bits=20)
        seq2 = generate_unique_block_sequence("my-secret-key", number_of_blocks=100, n_bits=20)
        np.testing.assert_array_equal(seq1, seq2)

    def test_differs_for_different_keys(self):
        seq1 = generate_unique_block_sequence("key-a", number_of_blocks=100, n_bits=20)
        seq2 = generate_unique_block_sequence("key-b", number_of_blocks=100, n_bits=20)
        self.assertFalse(np.array_equal(seq1, seq2))

    def test_uniqueness_full_capacity(self):
        seq = generate_unique_block_sequence("uniqueness-test-key", number_of_blocks=500, n_bits=500)
        self.assertEqual(len(seq), len(set(seq.tolist())))
        self.assertEqual(len(seq), 500)

    def test_uniqueness_partial_capacity(self):
        seq = generate_unique_block_sequence("partial-key", number_of_blocks=1000, n_bits=64)
        self.assertEqual(len(seq), 64)
        self.assertEqual(len(set(seq.tolist())), 64)
        self.assertGreaterEqual(seq.min(), 0)
        self.assertLess(seq.max(), 1000)

    def test_raises_when_n_bits_exceeds_capacity(self):
        with self.assertRaises(ValueError):
            generate_unique_block_sequence("key", number_of_blocks=10, n_bits=11)

    def test_n_bits_zero(self):
        seq = generate_unique_block_sequence("key", number_of_blocks=10, n_bits=0)
        self.assertEqual(len(seq), 0)


if __name__ == "__main__":
    unittest.main()
