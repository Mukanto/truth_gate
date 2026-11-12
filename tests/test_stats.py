"""Statistical primitive (spec section 4): Wilson bounds, Bonferroni level, SL."""

import unittest
from statistics import NormalDist

import _helpers  # noqa: F401  (sets sys.path)
from kapi.stats import (
    bonferroni_a, sl_deterministic, sl_stochastic, wilson_bounds, wilson_lower, wilson_upper, z_value,
)

# a = 0.025 gives z = 1.959964 (one-sided), the familiar 95% two-sided Wilson interval.
A95 = 0.025


class TestWilson(unittest.TestCase):
    def test_hand_computed_8_of_10(self):
        # p=0.8, n=10, z=1.959964: centre=(0.8+0.192073)/1.384146, half=z*sqrt(0.016+0.0096037)/1.384146
        lo, hi = wilson_bounds(8, 10, A95)
        self.assertAlmostEqual(lo, 0.49016, places=4)
        self.assertAlmostEqual(hi, 0.94332, places=4)

    def test_hand_computed_50_of_100(self):
        self.assertAlmostEqual(wilson_lower(50, 100, A95), 0.40383, places=4)
        self.assertAlmostEqual(wilson_upper(50, 100, A95), 0.59617, places=4)

    def test_hand_computed_5_of_20_at_a_005(self):
        # z = 1.644854
        self.assertAlmostEqual(wilson_lower(5, 20, 0.05), 0.12738, places=4)
        self.assertAlmostEqual(wilson_upper(5, 20, 0.05), 0.43220, places=4)

    def test_zero_successes(self):
        # lower is exactly 0; upper = z^2 / (n + z^2) = 3.841459 / 13.841459
        self.assertEqual(wilson_lower(0, 10, A95), 0.0)
        self.assertAlmostEqual(wilson_upper(0, 10, A95), 0.27753, places=4)

    def test_all_successes(self):
        # upper is exactly 1; lower = n / (n + z^2)
        self.assertEqual(wilson_upper(10, 10, A95), 1.0)
        self.assertAlmostEqual(wilson_lower(10, 10, A95), 0.72247, places=4)

    def test_bounds_ordered_and_in_unit_interval(self):
        for n in (1, 5, 40):
            for k in range(n + 1):
                lo, hi = wilson_bounds(k, n, 0.01)
                self.assertTrue(0.0 <= lo <= k / n <= hi <= 1.0, (k, n, lo, hi))

    def test_empty_sample(self):
        self.assertEqual(wilson_bounds(0, 0, A95), (0.0, 1.0))

    def test_smaller_a_gives_wider_interval(self):
        lo1, hi1 = wilson_bounds(30, 100, 0.05)
        lo2, hi2 = wilson_bounds(30, 100, 0.001)
        self.assertLess(lo2, lo1)
        self.assertGreater(hi2, hi1)

    def test_z_is_stdlib_inverse_cdf(self):
        self.assertEqual(z_value(0.01), NormalDist().inv_cdf(0.99))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            wilson_bounds(5, 4, A95)
        with self.assertRaises(ValueError):
            wilson_bounds(-1, 4, A95)
        with self.assertRaises(ValueError):
            wilson_bounds(1, 4, 0.0)
        with self.assertRaises(ValueError):
            wilson_bounds(1, 4, 1.0)


class TestBonferroni(unittest.TestCase):
    def test_alpha_over_two_m(self):
        self.assertAlmostEqual(bonferroni_a(0.05, 1), 0.025)
        self.assertAlmostEqual(bonferroni_a(0.05, 5), 0.005)
        self.assertAlmostEqual(bonferroni_a(0.05, 25), 0.001)
        self.assertAlmostEqual(bonferroni_a(0.10, 10), 0.005)

    def test_m_must_be_positive(self):
        with self.assertRaises(ValueError):
            bonferroni_a(0.05, 0)


class TestSL(unittest.TestCase):
    def test_clearly_lower(self):
        self.assertTrue(sl_stochastic(0, 100, 100, 100, A95))

    def test_equal_rates_not_lower(self):
        self.assertFalse(sl_stochastic(50, 100, 50, 100, A95))

    def test_overlapping_intervals_not_lower(self):
        # 40/100 vs 55/100 at a=0.025: upper(40)=0.4994 > lower(55)=0.4521
        self.assertFalse(sl_stochastic(40, 100, 55, 100, A95))

    def test_boundary_matches_bounds(self):
        # 20/100 vs 80/100: upper(20)=0.2807 < lower(80)=0.7193
        self.assertTrue(sl_stochastic(20, 100, 80, 100, A95))
        self.assertEqual(
            sl_stochastic(30, 100, 60, 100, A95),
            wilson_upper(30, 100, A95) < wilson_lower(60, 100, A95),
        )

    def test_stricter_level_makes_sl_harder(self):
        self.assertTrue(sl_stochastic(10, 20, 20, 20, 0.05))  # upper(10/20)=0.7134 < lower(20/20)=0.8399
        self.assertFalse(sl_stochastic(10, 20, 20, 20, 0.0001))

    def test_deterministic_truth_table(self):
        for low in ("HOLDS", "FAILS", "UNDEFINED"):
            for high in ("HOLDS", "FAILS", "UNDEFINED"):
                expected = low in ("FAILS", "UNDEFINED") and high == "HOLDS"
                self.assertEqual(sl_deterministic(low, high), expected, (low, high))


if __name__ == "__main__":
    unittest.main()
