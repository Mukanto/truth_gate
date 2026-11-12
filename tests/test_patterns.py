"""Criterion patterns (spec 0.6, section 4): truth tables, UNDEFINED conditions, the missing-key rule, validation."""

import itertools
import unittest

import numpy as np

import _helpers  # noqa: F401  (puts the repository root on sys.path)
from truth_gate.common import ManifestError
from truth_gate.minus import RecordingDict
from truth_gate.patterns import FAILS, HOLDS, UNDEFINED, Pattern, apply_stat

NAN = float("nan")


def ev(table, data):
    return Pattern(table).evaluate(data)


def arr(*values, dtype=None):
    return np.array(values, dtype=dtype)


class TestStatistics(unittest.TestCase):
    def test_every_statistic(self):
        x = np.array([4.0, 1.0, 3.0, 2.0])
        expected = {"mean": 2.5, "median": 2.5, "min": 1.0, "max": 4.0, "sum": 10.0, "std": float(np.std(x, ddof=1)),
                    "first": 4.0, "last": 2.0, "count": 4.0}
        for stat, value in expected.items():
            with self.subTest(stat=stat):
                self.assertEqual(apply_stat(x, stat), value)
        self.assertEqual(apply_stat(x, "quantile", 0.25), float(np.quantile(x, 0.25)))  # numpy's linear method
        self.assertEqual(apply_stat(np.array([True, False, True, True]), "fraction_true"), 0.75)

    def test_statistics_flatten_n_dimensional_arrays(self):
        self.assertEqual(apply_stat(np.arange(6.0).reshape(2, 3), "mean"), 2.5)
        self.assertEqual(apply_stat(np.zeros((2, 3)), "count"), 6.0)

    def test_std_needs_two_values_and_str_has_no_mean(self):
        for stat, data in (("std", arr(1.0)), ("mean", arr("a", "b")), ("mean", arr(True, False)),
                           ("fraction_true", arr(1.0, 2.0)), ("mean", arr(1.0, NAN)), ("mean", arr(1.0, np.inf))):
            with self.subTest(stat=stat, data=data):
                self.assertEqual(ev({"pattern": "threshold", "x": "x", "stat": stat, "op": ">", "value": 0}, {"x": data}),
                                 UNDEFINED)


class TestThreshold(unittest.TestCase):
    def make(self, **kw):
        return {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0, **kw}

    def test_truth_table(self):
        data = {"x": arr(1.0, 2.0, 3.0)}  # mean 2
        for op, value, outcome in ((">", 1.0, HOLDS), (">", 2.0, FAILS), (">=", 2.0, HOLDS), ("<", 2.0, FAILS),
                                   ("<", 2.5, HOLDS), ("<=", 2.0, HOLDS), ("<=", 1.9, FAILS)):
            with self.subTest(op=op, value=value):
                self.assertEqual(ev(self.make(op=op, value=value), data), outcome)

    def test_count_equality_is_the_only_equality(self):
        data = {"x": arr(1.0, 2.0, 3.0)}
        self.assertEqual(ev(self.make(stat="count", op="==", value=3), data), HOLDS)
        self.assertEqual(ev(self.make(stat="count", op="==", value=4), data), FAILS)
        with self.assertRaisesRegex(ManifestError, "op"):
            Pattern(self.make(stat="mean", op="==", value=2))
        with self.assertRaisesRegex(ManifestError, "value"):
            Pattern(self.make(stat="count", op="==", value=2.5))  # both sides must be integers

    def test_selections(self):
        data = {"x": arr(1.0, 2.0, 3.0, 4.0), "g": arr("a", "b", "a", "b"), "n": arr(1, 2, 3, 4)}
        self.assertEqual(ev(self.make(x_where={"column": "g", "equals": "b"}, value=2.5), data), HOLDS)  # mean 3
        self.assertEqual(ev(self.make(x_where={"column": "g", "equals": "a"}, value=2.5), data), FAILS)  # mean 2
        self.assertEqual(ev(self.make(x_where={"column": "n", "op": ">=", "value": 3}, value=3.4), data), HOLDS)
        self.assertEqual(ev(self.make(x_index=[0, 1], value=1.4), data), HOLDS)  # mean 1.5
        self.assertEqual(ev(self.make(x_index=[0, 1], value=1.6), data), FAILS)

    def test_undefined_conditions(self):
        base = {"x": arr(1.0, 2.0), "g": arr("a", "b"), "f": arr(1.0, 2.0)}
        cases = {
            "empty selection": self.make(x_where={"column": "g", "equals": "zzz"}),
            "equals on a numeric column": self.make(x_where={"column": "f", "equals": "a"}),
            "numeric where on a str column": self.make(x_where={"column": "g", "op": ">", "value": 1}),
            "mask of the wrong length": self.make(x_where={"column": "m", "equals": True}),
            "mean of a str column": self.make(x="g"),
        }
        data = {**base, "m": arr(True, False, True)}
        for name, table in cases.items():
            with self.subTest(name):
                self.assertEqual(ev(table, data), UNDEFINED)

    def test_selection_index_out_of_range_is_undefined_not_an_exception(self):
        """R-32 (audit F4): a data condition; the leaf is UNDEFINED, nothing is raised."""
        self.assertEqual(ev(self.make(x_index=[5]), {"x": arr(1.0, 2.0)}), UNDEFINED)
        self.assertEqual(ev(self.make(x_index=[0, 2]), {"x": arr(1.0, 2.0)}), UNDEFINED)  # one position outside is enough
        self.assertEqual(ev(self.make(x_index=[0, 1]), {"x": arr(1.0, 2.0)}), HOLDS)  # the last position is in range

    def test_count_of_an_empty_selection_is_undefined(self):
        """R-32 (audit F3): count obeys the common rule 'UNDEFINED when a selection is empty'."""
        data = {"x": arr(1.0, 2.0), "g": arr("a", "b")}
        empty = {"x_where": {"column": "g", "equals": "zzz"}}
        for op, value in (("==", 0), (">=", 0), ("<", 1)):
            with self.subTest(op=op, value=value):
                self.assertEqual(ev(self.make(stat="count", op=op, value=value, **empty), data), UNDEFINED)
        self.assertEqual(ev(self.make(stat="count", op="==", value=0), {"x": arr(dtype=float)}), UNDEFINED)
        self.assertEqual(ev(self.make(stat="count", op="==", value=1, x_where={"column": "g", "equals": "a"}), data),
                         HOLDS)  # a non-empty selection still counts

    def test_an_out_of_range_leaf_takes_part_in_the_kleene_logic(self):
        bad = self.make(x_index=[9])
        good = self.make()
        data = {"x": arr(1.0, 2.0, 3.0)}
        failing = self.make(value=100.0)
        self.assertEqual(ev({"pattern": "all_of", "of": [bad, failing]}, data), FAILS)
        self.assertEqual(ev({"pattern": "all_of", "of": [bad, good]}, data), UNDEFINED)
        self.assertEqual(ev({"pattern": "any_of", "of": [bad, good]}, data), HOLDS)
        self.assertEqual(ev({"pattern": "any_of", "of": [bad, failing]}, data), UNDEFINED)

    def test_rate_with_an_out_of_range_index_is_undefined(self):
        table = {"pattern": "rate", "condition": {"column": "x", "op": ">", "value": 0.0}, "op": ">", "value": 0.5,
                 "index": [0, 7]}
        self.assertEqual(ev(table, {"x": arr(1.0, 2.0)}), UNDEFINED)

    def test_missing_key_raises(self):
        with self.assertRaises(KeyError):
            ev(self.make(), {"y": arr(1.0)})
        with self.assertRaises(KeyError):  # the selection column is a referenced key too
            ev(self.make(x_where={"column": "g", "equals": "a"}), {"x": arr(1.0)})

    def test_quantile_needs_q(self):
        with self.assertRaisesRegex(ManifestError, "q"):
            Pattern(self.make(stat="quantile"))
        with self.assertRaisesRegex(ManifestError, "q"):
            Pattern(self.make(stat="mean", q=0.5))
        self.assertEqual(ev(self.make(stat="quantile", q=0.5, value=1.5), {"x": arr(1.0, 2.0, 3.0)}), HOLDS)


class TestDifference(unittest.TestCase):
    def make(self, **kw):
        return {"pattern": "difference", "a": "a", "b": "b", "stat": "mean", "op": ">=", "value": 0.5, **kw}

    def test_unpaired(self):
        self.assertEqual(ev(self.make(), {"a": arr(2.0, 4.0), "b": arr(1.0, 1.0, 4.0)}), HOLDS)  # 3 - 2 = 1
        self.assertEqual(ev(self.make(), {"a": arr(2.0, 2.0), "b": arr(1.9)}), FAILS)  # 0.1

    def test_paired_is_the_statistic_of_the_elementwise_difference(self):
        data = {"a": arr(5.0, 1.0, 3.0), "b": arr(1.0, 1.0, 1.0)}  # differences 4, 0, 2: median 2, mean 2
        self.assertEqual(ev(self.make(paired=True, stat="median", op=">=", value=2.0), data), HOLDS)
        self.assertEqual(ev(self.make(paired=True, stat="min", value=0.5), data), FAILS)  # min of a - b is 0
        self.assertEqual(ev(self.make(paired=True, stat="min", op=">=", value=0.0), data), HOLDS)

    def test_paired_with_unequal_lengths_is_undefined(self):
        self.assertEqual(ev(self.make(paired=True), {"a": arr(1.0, 2.0), "b": arr(1.0)}), UNDEFINED)

    def test_selection_example_of_the_manifest(self):
        data = {"y": arr(6.0, 5.0, 6.2, 5.0), "g": arr("treated", "control", "treated", "control")}
        table = {"pattern": "difference", "a": "y", "a_where": {"column": "g", "equals": "treated"}, "b": "y",
                 "b_where": {"column": "g", "equals": "control"}, "stat": "mean", "op": ">=", "value": 0.5}
        self.assertEqual(ev(table, data), HOLDS)  # 6.1 - 5.0
        self.assertEqual(ev({**table, "value": 1.2}, data), FAILS)

    def test_undefined_conditions(self):
        self.assertEqual(ev(self.make(), {"a": arr(NAN), "b": arr(1.0)}), UNDEFINED)  # not finite
        self.assertEqual(ev(self.make(), {"a": arr("x"), "b": arr(1.0)}), UNDEFINED)  # types do not fit
        self.assertEqual(ev(self.make(a_where={"column": "g", "equals": "z"}),
                            {"a": arr(1.0), "b": arr(1.0), "g": arr("a")}), UNDEFINED)  # empty selection
        self.assertEqual(ev(self.make(paired=True, stat="fraction_true"), {"a": arr(1.0), "b": arr(1.0)}), UNDEFINED)

    def test_selection_applies_to_its_own_argument_only(self):
        data = {"a": arr(10.0, 0.0), "b": arr(0.0, 10.0), "g": arr("u", "v")}
        t = self.make(a_where={"column": "g", "equals": "u"}, value=9.0)  # a -> [10], b stays [0, 10]: 10 - 5 = 5
        self.assertEqual(ev(t, data), FAILS)
        self.assertEqual(ev({**t, "value": 4.0}, data), HOLDS)

    def test_missing_key(self):
        with self.assertRaises(KeyError):
            ev(self.make(), {"a": arr(1.0)})


class TestRatioBand(unittest.TestCase):
    def make(self, **kw):
        return {"pattern": "ratio_band", "a": "a", "b": "b", "stat": "mean", "lo": 0.9, "hi": 1.1, **kw}

    def test_truth_table(self):
        self.assertEqual(ev(self.make(), {"a": arr(1.0), "b": arr(1.0)}), HOLDS)
        self.assertEqual(ev(self.make(hi=1.15), {"a": arr(1.1), "b": arr(1.0)}), HOLDS)
        self.assertEqual(ev(self.make(), {"a": arr(1.2), "b": arr(1.0)}), FAILS)
        self.assertEqual(ev(self.make(), {"a": arr(0.5), "b": arr(1.0)}), FAILS)

    def test_denominator_zero_and_other_undefined(self):
        self.assertEqual(ev(self.make(), {"a": arr(1.0), "b": arr(0.0)}), UNDEFINED)
        self.assertEqual(ev(self.make(), {"a": arr(NAN), "b": arr(1.0)}), UNDEFINED)
        self.assertEqual(ev(self.make(), {"a": arr("x"), "b": arr(1.0)}), UNDEFINED)

    def test_both_bounds_are_required(self):
        t = self.make()
        for key in ("lo", "hi"):
            with self.subTest(key=key):
                bad = {k: v for k, v in t.items() if k != key}
                with self.assertRaisesRegex(ManifestError, key):
                    Pattern(bad)
        with self.assertRaisesRegex(ManifestError, "lo"):
            Pattern(self.make(lo=2.0, hi=1.0))


class TestWithin(unittest.TestCase):
    def test_stat_mode(self):
        t = {"pattern": "within", "a": "a", "b": "b", "tol": 0.1, "stat": "mean"}
        self.assertEqual(ev(t, {"a": arr(1.0, 1.1), "b": arr(1.0)}), HOLDS)  # |1.05 - 1| = 0.05
        self.assertEqual(ev(t, {"a": arr(1.5), "b": arr(1.0)}), FAILS)
        self.assertEqual(ev({**t, "mode": "stat"}, {"a": arr(1.0), "b": arr(1.0)}), HOLDS)

    def test_all_mode(self):
        t = {"pattern": "within", "a": "a", "b": "b", "tol": 0.1, "mode": "all"}
        self.assertEqual(ev(t, {"a": arr(1.0, 2.0), "b": arr(1.05, 1.95)}), HOLDS)
        self.assertEqual(ev(t, {"a": arr(1.0, 2.0), "b": arr(1.05, 1.5)}), FAILS)
        self.assertEqual(ev(t, {"a": arr(1.0, 2.0), "b": arr(1.0)}), UNDEFINED)  # unequal lengths
        self.assertEqual(ev(t, {"a": arr(1.0, NAN), "b": arr(1.0, 1.0)}), UNDEFINED)
        with self.assertRaisesRegex(ManifestError, "stat"):
            Pattern({**t, "stat": "mean"})

    def test_stat_mode_undefined_and_missing(self):
        t = {"pattern": "within", "a": "a", "b": "b", "tol": 0.1, "stat": "std"}
        self.assertEqual(ev(t, {"a": arr(1.0), "b": arr(1.0, 2.0)}), UNDEFINED)
        with self.assertRaises(KeyError):
            ev(t, {"a": arr(1.0)})


class TestRate(unittest.TestCase):
    T = {"pattern": "rate", "condition": {"column": "p", "op": ">", "value": 1.5}, "op": ">", "value": 0.5}

    def test_truth_table(self):
        self.assertEqual(ev(self.T, {"p": arr(2.0, 2.0, 1.0)}), HOLDS)  # 2/3 > 0.5
        self.assertEqual(ev(self.T, {"p": arr(2.0, 1.0, 1.0)}), FAILS)
        self.assertEqual(ev({**self.T, "op": ">=", "value": 0.5}, {"p": arr(2.0, 1.0)}), HOLDS)  # 0.5 >= 0.5
        self.assertEqual(ev({**self.T, "op": "<", "value": 0.5}, {"p": arr(2.0, 1.0)}), FAILS)

    def test_matches_the_python_formula_of_example_03(self):
        rng = np.random.default_rng(5)
        for _ in range(20):
            p = rng.normal(2.0, 1.0, 64)
            self.assertEqual(ev({**self.T, "value": 0.8}, {"p": p}), HOLDS if bool(np.mean(p > 1.5) > 0.8) else FAILS)

    def test_undefined_conditions(self):
        self.assertEqual(ev(self.T, {"p": arr(2.0, NAN)}), UNDEFINED)
        self.assertEqual(ev(self.T, {"p": arr("a", "b")}), UNDEFINED)
        self.assertEqual(ev(self.T, {"p": np.array([], dtype=float)}), UNDEFINED)
        with self.assertRaises(KeyError):
            ev(self.T, {"q": arr(1.0)})

    def test_only_the_unprefixed_selection_is_defined_for_rate(self):
        # Post-freeze revision R-3 (stage c): `rate` takes an unprefixed `where` / `index`; prefixed names stay unknown.
        Pattern({**self.T, "where": {"column": "g", "equals": "a"}})
        Pattern({**self.T, "index": [0]})
        for key in ("x_where", "condition_where", "p_index"):
            with self.assertRaisesRegex(ManifestError, "unknown key"):
                Pattern({**self.T, key: {"column": "g", "equals": "a"}})


class TestCiExcludes(unittest.TestCase):
    def test_replicates_key(self):
        reps = np.linspace(1.0, 2.0, 101)  # 95% interval [1.025, 1.975]
        t = {"pattern": "ci_excludes", "replicates": "r", "side": "above", "value": 1.0}
        self.assertEqual(ev(t, {"r": reps}), HOLDS)
        self.assertEqual(ev({**t, "value": 1.03}, {"r": reps}), FAILS)
        self.assertEqual(ev({**t, "side": "below", "value": 2.0}, {"r": reps}), HOLDS)
        self.assertEqual(ev({**t, "side": "below", "value": 1.9}, {"r": reps}), FAILS)
        self.assertEqual(ev({**t, "level": 0.5, "value": 1.2}, {"r": reps}), HOLDS)  # [1.25, 1.75]
        self.assertEqual(ev(t, {"r": np.array([1.0, NAN])}), UNDEFINED)
        self.assertEqual(ev(t, {"r": np.array([], dtype=float)}), UNDEFINED)
        with self.assertRaises(KeyError):
            ev(t, {})

    def test_internal_bootstrap_is_a_pure_function_of_the_data(self):
        rng = np.random.default_rng(1)
        x = rng.normal(2.0, 0.5, 30)
        t = {"pattern": "ci_excludes", "x": "x", "stat": "mean", "side": "above", "value": 1.0}
        pattern = Pattern(t)
        rec1, rec2, rec3 = {}, {}, {}
        self.assertEqual(pattern.evaluate({"x": x}, rec1), HOLDS)
        pattern.evaluate({"x": x.copy()}, rec2)
        pattern.evaluate({"x": rng.permutation(x)}, rec3)  # independent of row order (sorted values)
        self.assertEqual(rec1, rec2)
        self.assertEqual(rec1, rec3)
        lo, hi = rec1[""][1]["ci_lo"], rec1[""][1]["ci_hi"]
        self.assertTrue(lo < float(np.mean(x)) < hi)
        self.assertEqual(ev({**t, "value": 5.0}, {"x": x}), FAILS)
        self.assertEqual(ev({**t, "side": "below", "value": 5.0}, {"x": x}), HOLDS)

    def test_internal_bootstrap_matches_a_direct_recomputation(self):
        x = np.array([3.0, 1.0, 2.0, 5.0, 4.0, 2.5, 3.5, 1.5])
        rec = {}
        Pattern({"pattern": "ci_excludes", "x": "x", "stat": "median", "side": "above", "value": 0.0, "B": 500,
                 "seed": 7, "level": 0.9}).evaluate({"x": x}, rec)
        rng = np.random.default_rng(7)
        s = np.sort(x)
        idx = rng.integers(0, s.size, size=(500, s.size))
        lo, hi = np.quantile(np.median(s[idx], axis=1), [0.05, 0.95])
        self.assertEqual(rec[""][1], {"ci_lo": float(lo), "ci_hi": float(hi)})

    def test_difference_of_means_unpaired_and_paired(self):
        a = np.array([5.0, 6.0, 7.0, 6.5, 5.5])
        b = np.array([1.0, 2.0, 1.5, 2.5, 3.0])
        t = {"pattern": "ci_excludes", "a": "a", "b": "b", "side": "above", "value": 1.0}
        self.assertEqual(ev(t, {"a": a, "b": b}), HOLDS)
        self.assertEqual(ev({**t, "paired": True}, {"a": a, "b": b}), HOLDS)
        self.assertEqual(ev({**t, "value": 10.0}, {"a": a, "b": b}), FAILS)
        self.assertEqual(ev({**t, "paired": True}, {"a": a, "b": b[:3]}), UNDEFINED)

    def test_paired_bootstrap_resamples_pairs_sorted_lexicographically(self):
        a, b = np.array([3.0, 1.0, 2.0, 2.0]), np.array([1.0, 1.0, 5.0, 0.0])
        t = Pattern({"pattern": "ci_excludes", "a": "a", "b": "b", "paired": True, "side": "above", "value": 0.0, "B": 200})
        r1, r2 = {}, {}
        t.evaluate({"a": a, "b": b}, r1)
        order = np.array([2, 3, 1, 0])  # any reordering of the rows
        t.evaluate({"a": a[order], "b": b[order]}, r2)
        self.assertEqual(r1, r2)

    def test_undefined_conditions(self):
        t = {"pattern": "ci_excludes", "x": "x", "stat": "mean", "side": "above", "value": 0.0}
        self.assertEqual(ev(t, {"x": arr(1.0, NAN)}), UNDEFINED)
        self.assertEqual(ev(t, {"x": arr("a", "b")}), UNDEFINED)
        self.assertEqual(ev(t, {"x": np.array([], dtype=float)}), UNDEFINED)
        self.assertEqual(ev({**t, "stat": "std"}, {"x": arr(1.0)}), UNDEFINED)
        with self.assertRaises(KeyError):
            ev(t, {"y": arr(1.0)})

    def test_argument_combinations(self):
        for bad in ({"replicates": "r", "x": "x"}, {"x": "x"}, {"a": "a"}, {"x": "x", "stat": "mean", "a": "a"},
                    {"a": "a", "b": "b", "stat": "mean"}, {"replicates": "r", "B": 10}, {}):
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError):
                    Pattern({"pattern": "ci_excludes", "side": "above", "value": 0.0, **bad})
        with self.assertRaisesRegex(ManifestError, "side"):
            Pattern({"pattern": "ci_excludes", "replicates": "r", "side": "left", "value": 0.0})
        with self.assertRaisesRegex(ManifestError, "level"):
            Pattern({"pattern": "ci_excludes", "replicates": "r", "side": "above", "value": 0.0, "level": 1.0})


class TestLargestTrue(unittest.TestCase):
    GRID = [1, 2, 3, 4]

    def make(self, **kw):
        return {"pattern": "largest_true", "grid": self.GRID, "y": "y", "op": ">=", "threshold": 0.5,
                "compare_to": {"value": 3}, "cmp": "==", **kw}

    def test_value_reference(self):
        y = arr(0.9, 0.8, 0.6, 0.1)  # largest grid value with y >= 0.5 is 3
        self.assertEqual(ev(self.make(), {"y": y}), HOLDS)
        self.assertEqual(ev(self.make(compare_to={"value": 4}), {"y": y}), FAILS)
        self.assertEqual(ev(self.make(compare_to={"value": 4}, cmp="<="), {"y": y}), HOLDS)
        self.assertEqual(ev(self.make(compare_to={"value": 2}, cmp=">="), {"y": y}), HOLDS)
        self.assertEqual(ev(self.make(compare_to={"value": 4}, cmp=">="), {"y": y}), FAILS)

    def test_second_curve(self):
        t = self.make(compare_to={"y": "z", "op": ">=", "threshold": 0.5})
        self.assertEqual(ev(t, {"y": arr(0.9, 0.8, 0.6, 0.1), "z": arr(0.9, 0.7, 0.6, 0.0)}), HOLDS)
        self.assertEqual(ev(t, {"y": arr(0.9, 0.8, 0.6, 0.1), "z": arr(0.9, 0.7, 0.2, 0.0)}), FAILS)
        with self.assertRaises(KeyError):
            ev(t, {"y": arr(0.9, 0.8, 0.6, 0.1)})

    def test_undefined_when_a_side_has_no_qualifying_value(self):
        self.assertEqual(ev(self.make(), {"y": arr(0.1, 0.1, 0.1, 0.1)}), UNDEFINED)  # a vacuous 0 = 0 cannot hold
        t = self.make(compare_to={"y": "z", "op": ">=", "threshold": 0.5})
        self.assertEqual(ev(t, {"y": arr(0.9, 0.9, 0.9, 0.9), "z": arr(0.0, 0.0, 0.0, 0.0)}), UNDEFINED)
        self.assertEqual(ev(t, {"y": arr(0.0, 0.0, 0.0, 0.0), "z": arr(0.0, 0.0, 0.0, 0.0)}), UNDEFINED)

    def test_undefined_for_length_mismatch_and_non_finite(self):
        self.assertEqual(ev(self.make(), {"y": arr(0.9, 0.8, 0.6)}), UNDEFINED)
        self.assertEqual(ev(self.make(), {"y": arr(0.9, 0.8, 0.6, NAN)}), UNDEFINED)  # any non-finite y value
        self.assertEqual(ev(self.make(), {"y": arr("a", "b", "c", "d")}), UNDEFINED)

    def test_op_variants_and_unsorted_grid(self):
        t = self.make(grid=[3, 1, 4, 2], op="<", threshold=0.5, compare_to={"value": 4})
        self.assertEqual(ev(t, {"y": arr(0.9, 0.9, 0.1, 0.9)}), HOLDS)  # y at grid value 4 is 0.1

    def test_grid_is_a_literal_list_of_finite_numbers(self):
        for bad in ("y", [], [1, "a"], [1, float("nan")], [True]):
            with self.subTest(grid=bad):
                with self.assertRaises(ManifestError):
                    Pattern(self.make(grid=bad))

    def test_cmp_and_compare_to_are_required_and_exclusive(self):
        t = self.make()
        with self.assertRaisesRegex(ManifestError, "cmp"):
            Pattern({k: v for k, v in t.items() if k != "cmp"})
        with self.assertRaisesRegex(ManifestError, "cmp"):
            Pattern(self.make(cmp=">"))
        with self.assertRaises(ManifestError):
            Pattern(self.make(compare_to={"value": 3, "y": "z"}))

    def test_selection_on_y(self):
        t = self.make(grid=[1, 2], y_index=[0, 1], compare_to={"value": 2})
        self.assertEqual(ev(t, {"y": arr(0.9, 0.8, 0.0)}), HOLDS)


class TestMonotone(unittest.TestCase):
    def make(self, **kw):
        return {"pattern": "monotone", "x": "x", "y": "y", "direction": "increasing", **kw}

    def test_truth_table(self):
        self.assertEqual(ev(self.make(), {"x": arr(1.0, 2.0, 3.0), "y": arr(1.0, 2.0, 3.0)}), HOLDS)
        self.assertEqual(ev(self.make(), {"x": arr(1.0, 2.0, 3.0), "y": arr(1.0, 3.0, 2.0)}), FAILS)
        self.assertEqual(ev(self.make(direction="decreasing"), {"x": arr(1.0, 2.0, 3.0), "y": arr(3.0, 2.0, 1.0)}), HOLDS)
        self.assertEqual(ev(self.make(direction="decreasing"), {"x": arr(1.0, 2.0, 3.0), "y": arr(1.0, 2.0, 3.0)}), FAILS)

    def test_y_is_ordered_by_x(self):
        self.assertEqual(ev(self.make(), {"x": arr(3.0, 1.0, 2.0), "y": arr(30.0, 10.0, 20.0)}), HOLDS)
        self.assertEqual(ev(self.make(), {"x": arr(3.0, 1.0, 2.0), "y": arr(10.0, 30.0, 20.0)}), FAILS)

    def test_ties_in_x_are_ordered_against_the_direction_and_row_order_does_not_matter(self):
        """R-30 (audit F6): y inside a tie is taken against `direction`, so a dip inside a tie always counts."""
        x = arr(1.0, 2.0, 2.0, 3.0)
        for direction, base in (("increasing", (0.0, 5.0, 7.0, 9.0)), ("decreasing", (9.0, 7.0, 5.0, 0.0))):
            for strict in (False, True):
                with self.subTest(direction=direction, strict=strict):
                    flipped = (base[0], base[2], base[1], base[3])  # the same rows, the tie in the other row order
                    outcomes = {ev(self.make(direction=direction, strict=strict), {"x": x, "y": arr(*row)})
                                for row in (base, flipped)}
                    self.assertEqual(len(outcomes), 1)  # the same outcome in both row orders
        # increasing: the tie (5, 7) read as 7 then 5 is a step of 2 against the direction
        data = {"x": arr(1.0, 2.0, 2.0, 3.0), "y": arr(0.0, 5.0, 7.0, 9.0)}
        self.assertEqual(ev(self.make(), data), FAILS)
        self.assertEqual(ev(self.make(tol=2.0), data), HOLDS)
        self.assertEqual(ev(self.make(tol=1.9), data), FAILS)
        # decreasing: the tie (7, 5) read as 5 then 7 is a step of 2 against the direction
        data = {"x": arr(1.0, 2.0, 2.0, 3.0), "y": arr(9.0, 7.0, 5.0, 0.0)}
        self.assertEqual(ev(self.make(direction="decreasing"), data), FAILS)
        self.assertEqual(ev(self.make(direction="decreasing", tol=2.0), data), HOLDS)
        # equal y inside a tie is a step of zero
        self.assertEqual(ev(self.make(), {"x": arr(1.0, 2.0, 2.0), "y": arr(1.0, 2.0, 2.0)}), HOLDS)

    def test_strict_and_tolerance(self):
        flat ={"x": arr(1.0, 2.0, 3.0), "y": arr(1.0, 1.0, 2.0)}
        self.assertEqual(ev(self.make(), flat), HOLDS)
        self.assertEqual(ev(self.make(strict=True), flat), FAILS)
        dip = {"x": arr(1.0, 2.0, 3.0), "y": arr(1.0, 0.5, 2.0)}  # one step of 0.5 against the direction
        self.assertEqual(ev(self.make(), dip), FAILS)
        self.assertEqual(ev(self.make(tol=0.5), dip), HOLDS)  # a step of up to tol against the direction is allowed
        self.assertEqual(ev(self.make(tol=0.5, strict=True), dip), FAILS)  # strict: the step must stay inside tol
        self.assertEqual(ev(self.make(tol=0.75, strict=True), dip), HOLDS)
        self.assertEqual(ev(self.make(tol=0.25), dip), FAILS)

    def test_undefined_conditions(self):
        self.assertEqual(ev(self.make(), {"x": arr(1.0, 2.0), "y": arr(1.0)}), UNDEFINED)  # length mismatch
        self.assertEqual(ev(self.make(), {"x": arr(1.0), "y": arr(1.0)}), UNDEFINED)  # no step
        self.assertEqual(ev(self.make(), {"x": arr(1.0, 2.0), "y": arr(1.0, NAN)}), UNDEFINED)
        self.assertEqual(ev(self.make(), {"x": arr("a", "b"), "y": arr(1.0, 2.0)}), UNDEFINED)
        with self.assertRaises(KeyError):
            ev(self.make(), {"x": arr(1.0, 2.0)})

    def test_direction_is_validated(self):
        with self.assertRaisesRegex(ManifestError, "direction"):
            Pattern(self.make(direction="up"))


class TestKleeneCombinators(unittest.TestCase):
    """all_of / any_of follow Kleene logic; a missing key anywhere raises before anything is evaluated."""

    DATA = {"good": arr(1.0), "bad": arr(-1.0), "txt": arr("s")}
    PART = {HOLDS: "good", FAILS: "bad", UNDEFINED: "txt"}

    def part(self, outcome):
        return {"pattern": "threshold", "x": self.PART[outcome], "stat": "mean", "op": ">", "value": 0.0}

    @staticmethod
    def kleene_all(outcomes):
        if FAILS in outcomes:
            return FAILS
        return UNDEFINED if UNDEFINED in outcomes else HOLDS

    @staticmethod
    def kleene_any(outcomes):
        if HOLDS in outcomes:
            return HOLDS
        return UNDEFINED if UNDEFINED in outcomes else FAILS

    def test_parts_alone(self):
        for outcome in (HOLDS, FAILS, UNDEFINED):
            self.assertEqual(ev(self.part(outcome), self.DATA), outcome)

    def test_truth_tables(self):
        for combinator, expected in (("all_of", self.kleene_all), ("any_of", self.kleene_any)):
            for size in (1, 2, 3):
                for combo in itertools.product((HOLDS, FAILS, UNDEFINED), repeat=size):
                    with self.subTest(combinator=combinator, combo=combo):
                        table = {"pattern": combinator, "of": [self.part(o) for o in combo]}
                        self.assertEqual(ev(table, self.DATA), expected(combo))

    def test_explicit_corner_cases(self):
        self.assertEqual(ev({"pattern": "all_of", "of": [self.part(UNDEFINED), self.part(FAILS)]}, self.DATA), FAILS)
        self.assertEqual(ev({"pattern": "any_of", "of": [self.part(UNDEFINED), self.part(HOLDS)]}, self.DATA), HOLDS)
        self.assertEqual(ev({"pattern": "all_of", "of": [self.part(UNDEFINED), self.part(HOLDS)]}, self.DATA), UNDEFINED)
        self.assertEqual(ev({"pattern": "any_of", "of": [self.part(UNDEFINED), self.part(FAILS)]}, self.DATA), UNDEFINED)

    def test_nesting(self):
        inner = {"pattern": "any_of", "of": [self.part(FAILS), self.part(HOLDS)]}
        outer = {"pattern": "all_of", "of": [inner, self.part(HOLDS)]}
        self.assertEqual(ev(outer, self.DATA), HOLDS)
        pattern = Pattern(outer)
        self.assertEqual([path for path, _ in pattern.leaves()], ["0.0", "0.1", "1"])  # position paths

    def test_a_missing_key_inside_any_of_makes_the_whole_criterion_raise(self):
        missing = {"pattern": "threshold", "x": "nope", "stat": "mean", "op": ">", "value": 0.0}
        table = {"pattern": "any_of", "of": [self.part(HOLDS), missing]}  # the first part alone would HOLD
        with self.assertRaises(KeyError):
            ev(table, self.DATA)
        with self.assertRaises(KeyError):
            ev({"pattern": "all_of", "of": [self.part(FAILS), missing]}, self.DATA)
        nested = {"pattern": "any_of", "of": [self.part(HOLDS), {"pattern": "all_of", "of": [missing]}]}
        with self.assertRaises(KeyError):
            ev(nested, self.DATA)

    def test_empty_or_malformed_of(self):
        for bad in ({"pattern": "all_of", "of": []}, {"pattern": "any_of"}, {"pattern": "all_of", "of": "x"},
                    {"pattern": "all_of", "of": [1]}, {"pattern": "any_of", "of": [{"pattern": "nope"}]}):
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError):
                    Pattern(bad)


class TestKeysAndReadRecording(unittest.TestCase):
    def test_every_referenced_key_is_looked_up_so_read_recording_sees_it(self):
        table = {"pattern": "any_of", "of": [
            {"pattern": "threshold", "x": "a", "x_where": {"column": "g", "equals": "u"}, "stat": "mean", "op": ">",
             "value": 0.0},
            {"pattern": "difference", "a": "b", "b": "c", "stat": "mean", "op": ">", "value": 0.0},
        ]}
        pattern = Pattern(table)
        self.assertEqual(sorted(pattern.keys), ["a", "b", "c", "g"])
        data = RecordingDict({"a": arr(1.0), "g": arr("u"), "b": arr(1.0), "c": arr(0.0), "unused": arr(1.0)})
        pattern.evaluate(data)
        self.assertEqual(data.read, {"a", "g", "b", "c"})
        self.assertFalse(data.all_read)

    def test_fn_uses_the_zero_point_three_convention(self):
        p = Pattern({"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 0.0})
        self.assertIs(p.fn({"x": arr(1.0)}), True)
        self.assertIs(p.fn({"x": arr(-1.0)}), False)
        self.assertIsNone(p.fn({"x": arr("s")}))


class TestPatternValidation(unittest.TestCase):
    def test_unknown_pattern_key_and_missing_arguments(self):
        good = {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}
        Pattern(good)
        with self.assertRaisesRegex(ManifestError, "pattern.zzz"):
            Pattern({**good, "zzz": 1})
        for key in ("x", "stat", "op", "value"):
            with self.subTest(missing=key):
                with self.assertRaisesRegex(ManifestError, key):
                    Pattern({k: v for k, v in good.items() if k != key})
        with self.assertRaisesRegex(ManifestError, "pattern.pattern"):
            Pattern({"pattern": "nope"})
        with self.assertRaisesRegex(ManifestError, "stat"):
            Pattern({**good, "stat": "mode"})
        with self.assertRaisesRegex(ManifestError, "op"):
            Pattern({**good, "op": "!="})
        with self.assertRaisesRegex(ManifestError, "value"):
            Pattern({**good, "value": "1"})
        with self.assertRaisesRegex(ManifestError, "value"):
            Pattern({**good, "value": True})
        with self.assertRaisesRegex(ManifestError, "value"):
            Pattern({**good, "value": float("inf")})

    def test_selection_validation(self):
        good = {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}
        for bad in ({"x_where": {"column": "g"}}, {"x_where": {"column": "g", "equals": 1}},
                    {"x_where": {"column": "g", "equals": "a", "op": ">", "value": 1}},
                    {"x_where": {"column": "g", "op": ">"}}, {"x_where": {"equals": "a"}}, {"x_where": "g"},
                    {"x_index": []}, {"x_index": [-1]}, {"x_index": [1.5]}, {"x_index": [0], "x_where": {"column": "g", "equals": "a"}},
                    {"y_where": {"column": "g", "equals": "a"}}):
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError):
                    Pattern({**good, **bad})

    def test_pattern_error_names_the_manifest_path(self):
        with self.assertRaisesRegex(ManifestError, r"criteria\[2\]\.value"):
            Pattern({"pattern": "threshold", "x": "x", "stat": "mean", "op": ">"}, "criteria[2]")
        with self.assertRaisesRegex(ManifestError, r"criteria\[0\]\.of\[1\]\.stat"):
            Pattern({"pattern": "all_of", "of": [
                {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1},
                {"pattern": "threshold", "x": "x", "stat": "bad", "op": ">", "value": 1}]}, "criteria[0]")


if __name__ == "__main__":
    unittest.main()
