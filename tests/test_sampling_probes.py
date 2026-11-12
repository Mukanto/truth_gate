"""Seeds, sample counts, data validation (spec section 4) and generic probes (sections 5.5, 6)."""

import unittest
import zlib

import numpy as np

import _helpers  # noqa: F401
from kapi import probes
from kapi.sampling import copy_data, sample_count, stream_rng, validate_data


class TestSeeds(unittest.TestCase):
    def test_matches_documented_seed_sequence(self):
        expected = np.random.default_rng(np.random.SeedSequence([7, zlib.crc32(b"world:plus"), 3]))
        got = stream_rng(7, "world:plus", 3)
        self.assertEqual(got.random(), expected.random())

    def test_same_stream_same_index_reproducible(self):
        self.assertEqual(stream_rng(1, "world:plus", 0).random(), stream_rng(1, "world:plus", 0).random())

    def test_streams_indices_and_seeds_differ(self):
        base = stream_rng(1, "world:plus", 0).random()
        self.assertNotEqual(base, stream_rng(1, "world:minus", 0).random())
        self.assertNotEqual(base, stream_rng(1, "world:plus", 1).random())
        self.assertNotEqual(base, stream_rng(2, "world:plus", 0).random())


class TestSampleCount(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(sample_count(False, 200, 20, quick=False), 200)
        self.assertEqual(sample_count(False, 200, 20, quick=True), 20)
        self.assertEqual(sample_count(True, 200, 20, quick=False), 1)
        self.assertEqual(sample_count(True, 200, 20, quick=True), 1)


class TestDataHandling(unittest.TestCase):
    def test_copy_data_is_independent(self):
        data = {"x": np.arange(3.0)}
        clone = copy_data(data)
        clone["x"][0] = 99.0
        self.assertEqual(data["x"][0], 0.0)

    def test_validate_data(self):
        self.assertEqual(validate_data({"x": np.zeros(2)}).keys(), {"x"})
        for bad in (None, [1, 2], {"x": [1, 2]}, {1: np.zeros(2)}):
            with self.assertRaises(TypeError):
                validate_data(bad)


class TestProbes(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)
        self.data = {
            "f": np.ones((4, 3)),
            "i": np.arange(5),
            "b": np.array([True, False, True]),
            "s": np.array(["a", "b"]),
        }

    def test_noise_probe(self):
        out = probes.noise_probe(self.data, self.rng)
        self.assertEqual(list(out), list(self.data))
        self.assertEqual(out["f"].shape, (4, 3))
        self.assertEqual(out["f"].dtype, np.float64)
        self.assertEqual(out["i"].dtype, np.float64)
        self.assertEqual(out["i"].shape, (5,))
        self.assertEqual(out["b"].dtype, np.bool_)
        self.assertTrue(np.array_equal(out["s"], self.data["s"]))
        big = probes.noise_probe({"x": np.zeros(20000)}, np.random.default_rng(1))["x"]
        self.assertAlmostEqual(float(big.mean()), 0.0, delta=0.05)
        self.assertAlmostEqual(float(big.std()), 1.0, delta=0.05)

    def test_noise_bool_is_bernoulli_half(self):
        out = probes.noise_probe({"b": np.zeros(20000, dtype=bool)}, np.random.default_rng(2))["b"]
        self.assertAlmostEqual(float(out.mean()), 0.5, delta=0.02)

    def test_zeros_probe(self):
        out = probes.zeros_probe(self.data)
        self.assertTrue(np.all(out["f"] == 0) and out["f"].dtype == np.float64)
        self.assertTrue(np.all(out["i"] == 0) and out["i"].dtype == np.float64)
        self.assertFalse(out["b"].any())
        self.assertTrue(np.array_equal(out["s"], self.data["s"]))

    def test_probes_do_not_mutate_input(self):
        before = {k: v.copy() for k, v in self.data.items()}
        probes.noise_probe(self.data, self.rng)
        probes.zeros_probe(self.data)
        probes.shuffle_probe({"a": np.arange(5), "b": np.arange(5)}, self.rng, "a", "b")
        for k in before:
            self.assertTrue(np.array_equal(before[k], self.data[k]))

    def test_unchanged_keys_listed(self):
        self.assertEqual(probes.unchanged_keys(self.data, "noise"), ["s"])
        self.assertEqual(probes.unchanged_keys(self.data, "zeros"), ["s"])

    def test_shuffle_permutes_b_only(self):
        data = {"a": np.arange(8), "b": np.arange(8) * 10}
        out = probes.shuffle_probe(data, self.rng, "a", "b")
        self.assertTrue(np.array_equal(out["a"], data["a"]))
        self.assertEqual(sorted(out["b"].tolist()), data["b"].tolist())
        self.assertFalse(np.array_equal(out["b"], data["b"]))

    def test_shuffle_errors(self):
        with self.assertRaises(KeyError):
            probes.shuffle_probe({"a": np.arange(3)}, self.rng, "a", "b")
        with self.assertRaises(ValueError):
            probes.shuffle_probe({"a": np.arange(3), "b": np.float64(1.0) * np.ones(())}, self.rng, "a", "b")

    def test_shuffle_name(self):
        self.assertEqual(probes.shuffle_name("a", "b"), "shuffle:a,b")


if __name__ == "__main__":
    unittest.main()
