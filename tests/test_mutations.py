"""Mutation library (spec 0.6, section 6): shapes, row alignment, dtype rules, no-op validation, seeded determinism."""

import copy
import unittest

import numpy as np

import _helpers  # noqa: F401  (puts the repository root on sys.path)
from truth_gate.common import ManifestError, NotApplicable
from truth_gate.mutations import (
    OPS, MutationSet, apply_mutations, declaration_rng, needs_row_keys, validate_mutations,
)

ROWS = ("g", "y", "w")


def sample():
    return {
        "g": np.array(["a", "b", "a", "b", "a", "b"]),
        "y": np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]),
        "w": np.array([10, 20, 30, 40, 50, 60]),
        "flag": np.array([True, False, True, False, True, False]),
        "m": np.arange(12.0).reshape(6, 2),
        "scalar": np.array(2.5),
    }


def run(mutation, data=None, seed=0, rows=ROWS):
    data = sample() if data is None else data
    return apply_mutations(data, validate_mutations([mutation], "m"), np.random.default_rng(seed), rows)


class TestValidation(unittest.TestCase):
    def test_every_op_has_a_valid_example(self):
        examples = {
            "shuffle": {"op": "shuffle", "column": "y"},
            "swap": {"op": "swap", "a": "y", "b": "w"},
            "scale": {"op": "scale", "column": "y", "factor": 2},
            "offset": {"op": "offset", "column": "y", "value": 1},
            "constant": {"op": "constant", "column": "y", "value": 0},
            "noise": {"op": "noise", "column": "y", "sd": 0.1},
            "subsample": {"op": "subsample", "fraction": 0.5},
            "null_effect": {"op": "null_effect", "outcome": "y", "group": "g", "reference": "a"},
            "reverse": {"op": "reverse", "column": "y"},
            "sign_flip": {"op": "sign_flip", "column": "y"},
            "permute_rows": {"op": "permute_rows"},
        }
        self.assertEqual(sorted(examples), sorted(OPS))
        for op, example in examples.items():
            with self.subTest(op=op):
                self.assertEqual(validate_mutations([example], "m")[0]["op"], op)

    def test_no_op_parameters_are_validation_errors(self):
        for bad, key in (({"op": "scale", "column": "y", "factor": 1}, "factor"),
                         ({"op": "scale", "column": "y", "factor": 1.0}, "factor"),
                         ({"op": "offset", "column": "y", "value": 0}, "value"),
                         ({"op": "offset", "column": "y", "value": 0.0}, "value"),
                         ({"op": "subsample", "fraction": 1}, "fraction"),
                         ({"op": "subsample", "fraction": 1.0}, "fraction"),
                         ({"op": "noise", "column": "y", "sd": 0}, "sd"),
                         ({"op": "noise", "column": "y", "rel_sd": 0}, "rel_sd")):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ManifestError, key):
                    validate_mutations([bad], "m")

    def test_other_validation_errors_name_the_key(self):
        cases = [
            ({"op": "nope"}, "m[0].op"),
            ({"column": "y"}, "m[0].op"),
            ({"op": "shuffle"}, "m[0]"),
            ({"op": "shuffle", "column": "y", "columns": ["y"]}, "m[0]"),
            ({"op": "shuffle", "columns": []}, "columns"),
            ({"op": "shuffle", "columns": ["y", "y"]}, "columns"),
            ({"op": "swap", "a": "y", "b": "y"}, "m[0]"),
            ({"op": "scale", "column": "y"}, "factor"),
            ({"op": "scale", "column": "y", "factor": "2"}, "factor"),
            ({"op": "scale", "column": "y", "factor": float("inf")}, "factor"),
            ({"op": "scale", "column": "y", "factor": 2, "zzz": 1}, "zzz"),
            ({"op": "constant", "column": "y"}, "m[0]"),
            ({"op": "constant", "column": "y", "value": 1, "stat": "mean"}, "m[0]"),
            ({"op": "constant", "column": "y", "stat": "mode"}, "stat"),
            ({"op": "noise", "column": "y", "sd": 1, "rel_sd": 1}, "m[0]"),
            ({"op": "noise", "column": "y", "sd": -1}, "sd"),
            ({"op": "subsample", "fraction": 0}, "fraction"),
            ({"op": "subsample", "fraction": 1.5}, "fraction"),
            ({"op": "null_effect", "outcome": "y", "group": "g", "reference": 1.5}, "reference"),
            ({"op": "permute_rows", "column": "y"}, "column"),
            ({"op": "reverse", "column": "y", "where": {"column": "g", "equals": "a"}}, "where"),  # not a dagger op
            ({"op": "swap", "a": "y", "b": "w", "where": {"column": "g", "equals": "a"}}, "where"),
        ]
        for bad, needle in cases:
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError) as caught:
                    validate_mutations([bad], "m")
                self.assertIn(needle, str(caught.exception))

    def test_list_must_be_non_empty_list_of_tables(self):
        for bad in ([], {}, "shuffle", [1]):
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError):
                    validate_mutations(bad, "m")

    def test_ambiguous_combinations_are_rejected_not_guessed(self):
        sel = {"column": "g", "equals": "a"}
        with self.assertRaisesRegex(ManifestError, "stat"):  # statistic over all rows or over the selected rows?
            validate_mutations([{"op": "constant", "column": "y", "stat": "mean", "where": sel}], "m")
        with self.assertRaisesRegex(ManifestError, "rel_sd"):
            validate_mutations([{"op": "noise", "column": "y", "rel_sd": 0.5, "where": sel}], "m")

    def test_row_operations_are_listed(self):
        ms = validate_mutations([{"op": "shuffle", "column": "y"}, {"op": "scale", "column": "y", "factor": 2},
                                 {"op": "permute_rows"}], "m")
        self.assertEqual(needs_row_keys(ms), ["shuffle", "permute_rows"])


class TestNoInPlaceChange(unittest.TestCase):
    def test_no_op_changes_its_input(self):
        sel = {"column": "g", "equals": "a"}
        mutations = [
            {"op": "shuffle", "columns": ["g", "y"]}, {"op": "swap", "a": "y", "b": "w"},
            {"op": "scale", "column": "y", "factor": 2.5}, {"op": "scale", "column": "w", "factor": 3, "where": sel},
            {"op": "offset", "column": "y", "value": 0.5}, {"op": "constant", "column": "y", "value": 9.0},
            {"op": "constant", "column": "g", "value": "zzzzzzzz"}, {"op": "noise", "column": "y", "sd": 1.0},
            {"op": "subsample", "fraction": 0.5}, {"op": "null_effect", "outcome": "y", "group": "g", "reference": "a"},
            {"op": "reverse", "column": "y"}, {"op": "sign_flip", "column": "w"}, {"op": "permute_rows"},
        ]
        for m in mutations:
            with self.subTest(op=m["op"]):
                data = sample()
                before = copy.deepcopy(data)
                out = run(m, data)
                for key in before:
                    np.testing.assert_array_equal(data[key], before[key])
                    self.assertEqual(data[key].dtype, before[key].dtype)
                for key in out:  # the result never aliases the input
                    self.assertFalse(np.shares_memory(out[key], data[key]), key)


class TestShuffle(unittest.TestCase):
    def test_permutes_the_first_axis_jointly_relative_to_all_others(self):
        out = run({"op": "shuffle", "columns": ["y", "w"]}, seed=3)
        self.assertEqual(sorted(out["y"]), sorted(sample()["y"]))
        self.assertTrue(np.array_equal(out["y"], out["w"] / 10.0))  # y and w moved together (w = 10 y)
        self.assertFalse(np.array_equal(out["y"], sample()["y"]))
        np.testing.assert_array_equal(out["g"], sample()["g"])  # the others stay
        self.assertEqual(out["w"].dtype, sample()["w"].dtype)

    def test_uses_one_rng_permutation_call(self):  # the A2 equivalence with example 01 relies on this
        out = run({"op": "shuffle", "column": "y"}, seed=11)
        perm = np.random.default_rng(11).permutation(6)
        np.testing.assert_array_equal(out["y"], sample()["y"][perm])

    def test_n_dimensional_arrays_keep_their_shape(self):
        out = run({"op": "shuffle", "column": "m"})
        self.assertEqual(out["m"].shape, (6, 2))
        self.assertTrue(np.array_equal(np.sort(out["m"][:, 0]), sample()["m"][:, 0]))

    def test_errors(self):
        with self.assertRaises(KeyError):
            run({"op": "shuffle", "column": "nope"})
        with self.assertRaises(NotApplicable):
            run({"op": "shuffle", "column": "scalar"})
        data = sample()
        data["short"] = np.arange(3.0)
        with self.assertRaises(NotApplicable):
            run({"op": "shuffle", "columns": ["y", "short"]}, data)


class TestSwap(unittest.TestCase):
    def test_exchanges_two_arrays(self):
        out = run({"op": "swap", "a": "y", "b": "w"})
        np.testing.assert_array_equal(out["y"], sample()["w"])
        np.testing.assert_array_equal(out["w"], sample()["y"])
        self.assertEqual(out["y"].dtype, sample()["w"].dtype)  # dtypes travel with the arrays

    def test_shapes_must_match(self):
        with self.assertRaises(NotApplicable):
            run({"op": "swap", "a": "y", "b": "m"})
        with self.assertRaises(KeyError):
            run({"op": "swap", "a": "y", "b": "nope"})


class TestScaleOffsetSignFlip(unittest.TestCase):
    def test_values_and_dtype_rules(self):
        # an integer factor / value keeps an int column int; otherwise the column becomes float64
        self.assertEqual(run({"op": "scale", "column": "w", "factor": 2})["w"].dtype, np.dtype(np.int64))
        np.testing.assert_array_equal(run({"op": "scale", "column": "w", "factor": 2})["w"], sample()["w"] * 2)
        self.assertEqual(run({"op": "scale", "column": "w", "factor": 2.0})["w"].dtype, np.dtype(np.float64))
        self.assertEqual(run({"op": "scale", "column": "w", "factor": 0.5})["w"].dtype, np.dtype(np.float64))
        np.testing.assert_array_equal(run({"op": "scale", "column": "w", "factor": 0.5})["w"], sample()["w"] * 0.5)
        self.assertEqual(run({"op": "offset", "column": "w", "value": 3})["w"].dtype, np.dtype(np.int64))
        self.assertEqual(run({"op": "offset", "column": "w", "value": 0.5})["w"].dtype, np.dtype(np.float64))
        self.assertEqual(run({"op": "sign_flip", "column": "w"})["w"].dtype, np.dtype(np.int64))
        np.testing.assert_array_equal(run({"op": "sign_flip", "column": "w"})["w"], -sample()["w"])
        for op in ({"op": "scale", "column": "y", "factor": 2}, {"op": "offset", "column": "y", "value": 1},
                   {"op": "sign_flip", "column": "y"}):
            self.assertEqual(run(op)["y"].dtype, np.dtype(np.float64))
        np.testing.assert_array_equal(run({"op": "offset", "column": "y", "value": -3.0})["y"], sample()["y"] - 3.0)

    def test_shape_and_other_columns_are_kept(self):
        out = run({"op": "scale", "column": "m", "factor": 3})
        self.assertEqual(out["m"].shape, (6, 2))
        np.testing.assert_array_equal(out["y"], sample()["y"])

    def test_where_limits_the_rows(self):
        out = run({"op": "scale", "column": "y", "factor": 10, "where": {"column": "g", "equals": "a"}})
        np.testing.assert_array_equal(out["y"], [10.0, 2.0, 30.0, 4.0, 50.0, 6.0])
        out = run({"op": "offset", "column": "y", "value": 100, "where": {"column": "w", "op": ">", "value": 35}})
        np.testing.assert_array_equal(out["y"], [1.0, 2.0, 3.0, 104.0, 105.0, 106.0])
        out = run({"op": "sign_flip", "column": "w", "where": {"column": "flag", "equals": True}})
        np.testing.assert_array_equal(out["w"], [-10, 20, -30, 40, -50, 60])
        self.assertEqual(out["w"].dtype, np.dtype(np.int64))
        out = run({"op": "scale", "column": "w", "factor": 0.5, "where": {"column": "g", "equals": "a"}})
        self.assertEqual(out["w"].dtype, np.dtype(np.float64))  # int column + float factor: float64 for the whole column
        np.testing.assert_array_equal(out["w"], [5.0, 20.0, 15.0, 40.0, 25.0, 60.0])

    def test_errors(self):
        for op in ({"op": "scale", "column": "g", "factor": 2}, {"op": "offset", "column": "flag", "value": 1},
                   {"op": "sign_flip", "column": "g"}):
            with self.subTest(op=op):
                with self.assertRaises(NotApplicable):
                    run(op)
        with self.assertRaises(KeyError):
            run({"op": "scale", "column": "nope", "factor": 2})
        with self.assertRaises(KeyError):
            run({"op": "scale", "column": "y", "factor": 2, "where": {"column": "nope", "equals": "a"}})
        with self.assertRaises(NotApplicable):  # the selection column has the wrong length for the target
            run({"op": "scale", "column": "y", "factor": 2, "where": {"column": "g", "equals": "a"}},
                {**sample(), "g": np.array(["a", "b"])})


class TestConstant(unittest.TestCase):
    def test_value_and_dtype(self):
        np.testing.assert_array_equal(run({"op": "constant", "column": "y", "value": 7})["y"], np.full(6, 7.0))
        self.assertEqual(run({"op": "constant", "column": "y", "value": 7})["y"].dtype, np.dtype(np.float64))
        self.assertEqual(run({"op": "constant", "column": "w", "value": 7})["w"].dtype, np.dtype(np.int64))
        self.assertEqual(run({"op": "constant", "column": "flag", "value": True})["flag"].dtype, np.dtype(bool))
        self.assertEqual(run({"op": "constant", "column": "m", "value": 1.0})["m"].shape, (6, 2))
        self.assertEqual(run({"op": "constant", "column": "scalar", "value": 1.0})["scalar"].shape, ())
        out = run({"op": "constant", "column": "g", "value": "much-longer-than-the-column-width"})
        self.assertTrue(np.all(out["g"] == "much-longer-than-the-column-width"))  # widened, not truncated

    def test_stat(self):
        self.assertEqual(float(run({"op": "constant", "column": "y", "stat": "mean"})["y"][0]), 3.5)
        self.assertEqual(float(run({"op": "constant", "column": "y", "stat": "median"})["y"][0]), 3.5)
        self.assertEqual(float(run({"op": "constant", "column": "y", "stat": "first"})["y"][0]), 1.0)
        self.assertEqual(run({"op": "constant", "column": "g", "stat": "first"})["g"][0], "a")
        self.assertEqual(int(run({"op": "constant", "column": "w", "stat": "first"})["w"][0]), 10)

    def test_where(self):
        out = run({"op": "constant", "column": "y", "value": 0.0, "where": {"column": "g", "equals": "b"}})
        np.testing.assert_array_equal(out["y"], [1.0, 0.0, 3.0, 0.0, 5.0, 0.0])

    def test_value_must_fit_the_column(self):
        for op in ({"op": "constant", "column": "w", "value": 1.5},  # the dtype is kept
                   {"op": "constant", "column": "flag", "value": 1}, {"op": "constant", "column": "y", "value": "x"},
                   {"op": "constant", "column": "g", "value": 1}, {"op": "constant", "column": "g", "stat": "mean"}):
            with self.subTest(op=op):
                with self.assertRaises(NotApplicable):
                    run(op)

    def test_mean_and_median_of_an_int_column_give_float64_whatever_the_data(self):
        """R-29 (audit F5): never depends on whether the statistic happens to be an integer."""
        integral = run({"op": "constant", "column": "w", "stat": "mean"})["w"]  # mean 35
        self.assertEqual(integral.dtype, np.dtype(np.float64))
        np.testing.assert_array_equal(integral, np.full(6, 35.0))
        data = sample()
        data["w"] = np.array([1, 2, 3, 4, 5, 7])  # mean 3.666...: not an integer
        for stat, expected in (("mean", 22 / 6), ("median", 3.5)):
            with self.subTest(stat=stat):
                out = run({"op": "constant", "column": "w", "stat": stat}, data)["w"]
                self.assertEqual(out.dtype, np.dtype(np.float64))
                np.testing.assert_array_equal(out, np.full(6, expected))
        first = run({"op": "constant", "column": "w", "stat": "first"}, data)["w"]
        self.assertEqual(first.dtype, np.dtype(np.int64))  # `first` is a value of the column: the dtype is kept
        self.assertEqual(data["w"].dtype, np.dtype(np.int64))  # the input is not changed


class TestNoise(unittest.TestCase):
    def test_sd_adds_normal_noise(self):
        out = run({"op": "noise", "column": "y", "sd": 0.5}, seed=4)
        expected = sample()["y"] + np.random.default_rng(4).normal(0.0, 0.5, size=6)
        np.testing.assert_array_equal(out["y"], expected)

    def test_rel_sd_is_relative_to_the_column_standard_deviation(self):
        out = run({"op": "noise", "column": "y", "rel_sd": 0.5}, seed=4)
        sd = 0.5 * float(np.std(sample()["y"], ddof=1))
        np.testing.assert_array_equal(out["y"], sample()["y"] + np.random.default_rng(4).normal(0.0, sd, size=6))

    def test_dtype_rule_and_shape(self):
        out = run({"op": "noise", "column": "w", "sd": 1.0})
        self.assertEqual(out["w"].dtype, np.dtype(np.float64))  # an int column becomes float64
        self.assertEqual(run({"op": "noise", "column": "m", "sd": 1.0})["m"].shape, (6, 2))
        self.assertEqual(run({"op": "noise", "column": "y", "sd": 1.0})["y"].dtype, np.dtype(np.float64))

    def test_where_adds_noise_to_the_selected_rows_only(self):
        out = run({"op": "noise", "column": "y", "sd": 1.0, "where": {"column": "g", "equals": "a"}}, seed=2)
        keep = sample()["g"] == "b"
        np.testing.assert_array_equal(out["y"][keep], sample()["y"][keep])
        self.assertTrue(np.all(out["y"][~keep] != sample()["y"][~keep]))

    def test_errors(self):
        with self.assertRaises(NotApplicable):
            run({"op": "noise", "column": "g", "sd": 1.0})
        with self.assertRaises(NotApplicable):  # rel_sd of a constant column gives a zero scale
            run({"op": "noise", "column": "y", "rel_sd": 0.5}, {**sample(), "y": np.ones(6)})
        with self.assertRaises(NotApplicable):
            run({"op": "noise", "column": "scalar", "rel_sd": 0.5})


class TestRowOperations(unittest.TestCase):
    def test_subsample_keeps_rows_aligned_without_replacement(self):
        out = run({"op": "subsample", "fraction": 0.5}, seed=1)
        self.assertEqual({k: out[k].shape[0] for k in ROWS}, {"g": 3, "y": 3, "w": 3})  # round(0.5 * 6)
        self.assertEqual(len(set(out["y"])), 3)  # without replacement
        for i in range(3):  # row alignment: y and w and g still belong together
            j = int(out["y"][i]) - 1
            self.assertEqual((out["w"][i], out["g"][i]), (sample()["w"][j], sample()["g"][j]))
        self.assertTrue(np.all(np.diff(out["y"]) > 0))  # kept in table order
        self.assertEqual(out["m"].shape, (6, 2))  # a key that is not row-aligned is untouched
        self.assertEqual(run({"op": "subsample", "fraction": 0.4})["y"].shape[0], round(0.4 * 6))

    def test_subsample_can_leave_no_rows(self):
        with self.assertRaises(NotApplicable):
            run({"op": "subsample", "fraction": 0.01})

    def test_permute_rows_keeps_associations(self):
        out = run({"op": "permute_rows"}, seed=5)
        self.assertFalse(np.array_equal(out["y"], sample()["y"]))
        for i in range(6):
            j = int(out["y"][i]) - 1
            self.assertEqual((out["w"][i], out["g"][i]), (sample()["w"][j], sample()["g"][j]))
        np.testing.assert_array_equal(out["m"], sample()["m"])
        self.assertEqual(out["w"].dtype, sample()["w"].dtype)

    def test_row_aligned_keys_are_the_context(self):
        with self.assertRaises(NotApplicable):
            run({"op": "permute_rows"}, rows=())
        with self.assertRaises(NotApplicable):
            run({"op": "subsample", "fraction": 0.5}, rows=())
        with self.assertRaises(KeyError):
            run({"op": "permute_rows"}, rows=("y", "nope"))
        with self.assertRaises(NotApplicable):  # row-aligned keys must share their first-axis length
            run({"op": "permute_rows"}, {**sample(), "w": np.arange(3)})

    def test_null_effect_draws_outcomes_from_the_reference_rows(self):
        out = run({"op": "null_effect", "outcome": "y", "group": "g", "reference": "a"}, seed=9)
        ref = sample()["y"][sample()["g"] == "a"]
        keep = sample()["g"] == "a"
        np.testing.assert_array_equal(out["y"][keep], sample()["y"][keep])  # reference rows are unchanged
        self.assertTrue(set(out["y"][~keep]) <= set(ref))  # others are drawn with replacement from the reference rows
        rng = np.random.default_rng(9)
        draws = rng.integers(0, 3, size=3)
        np.testing.assert_array_equal(out["y"][~keep], ref[draws])
        np.testing.assert_array_equal(out["g"], sample()["g"])

    def test_null_effect_reference_types_and_errors(self):
        data = {**sample(), "num": np.array([1, 2, 1, 2, 1, 2])}
        self.assertEqual(run({"op": "null_effect", "outcome": "y", "group": "num", "reference": 1}, data)["y"].shape, (6,))
        self.assertEqual(run({"op": "null_effect", "outcome": "y", "group": "flag", "reference": True})["y"].shape, (6,))
        for op in ({"op": "null_effect", "outcome": "y", "group": "g", "reference": "zzz"},  # no reference rows
                   {"op": "null_effect", "outcome": "y", "group": "g", "reference": 1},  # type does not fit
                   {"op": "null_effect", "outcome": "y", "group": "m", "reference": 1}):
            with self.subTest(op=op):
                with self.assertRaises(NotApplicable):
                    run(op)
        with self.assertRaises(KeyError):
            run({"op": "null_effect", "outcome": "nope", "group": "g", "reference": "a"})


class TestReverse(unittest.TestCase):
    def test_reverses_the_first_axis(self):
        out = run({"op": "reverse", "column": "m"})
        np.testing.assert_array_equal(out["m"], sample()["m"][::-1])
        self.assertEqual(run({"op": "reverse", "column": "g"})["g"][0], "b")
        with self.assertRaises(NotApplicable):
            run({"op": "reverse", "column": "scalar"})
        with self.assertRaises(KeyError):
            run({"op": "reverse", "column": "nope"})


class TestSeededDeterminism(unittest.TestCase):
    MUTATIONS = validate_mutations([
        {"op": "shuffle", "column": "y"}, {"op": "noise", "column": "w", "sd": 2.0},
        {"op": "null_effect", "outcome": "y", "group": "g", "reference": "a"}, {"op": "subsample", "fraction": 0.5},
    ], "m")

    def test_stochastic_mode_draws_from_the_generator_the_engine_passes(self):
        mutate = MutationSet("control:c", self.MUTATIONS, ROWS, False, 123)
        a = mutate(sample(), np.random.default_rng(1))
        b = mutate(sample(), np.random.default_rng(1))
        c = mutate(sample(), np.random.default_rng(2))
        for key in a:
            np.testing.assert_array_equal(a[key], b[key])
        self.assertFalse(all(np.array_equal(a[k], c[k]) for k in a))

    def test_deterministic_mode_ignores_the_engine_generator(self):
        mutate = MutationSet("control:c", self.MUTATIONS, ROWS, True, 123)
        a = mutate(sample(), np.random.default_rng(1))
        for seed in (2, 3, 4):  # a different "sample index" generator every time
            b = mutate(sample(), np.random.default_rng(seed))
            for key in a:
                np.testing.assert_array_equal(a[key], b[key])
        np.testing.assert_array_equal(a["y"], MutationSet("control:c", self.MUTATIONS, ROWS, True, 123)(sample(), None)["y"])

    def test_deterministic_generator_depends_on_the_base_seed_and_the_declaration(self):
        def first(seed, label):
            return declaration_rng(seed, label).random()

        self.assertEqual(first(1, "control:c"), first(1, "control:c"))
        self.assertNotEqual(first(1, "control:c"), first(2, "control:c"))
        self.assertNotEqual(first(1, "control:c"), first(1, "control:d"))
        self.assertNotEqual(first(1, "control:c"), first(1, "premise:c"))  # the kind is part of the declaration id

    def test_one_fresh_generator_per_call_so_a_declaration_is_repeatable(self):
        mutate = MutationSet("world:minus", self.MUTATIONS, ROWS, True, 7)
        first = mutate(sample(), None)
        second = mutate(sample(), None)
        for key in first:
            np.testing.assert_array_equal(first[key], second[key])


if __name__ == "__main__":
    unittest.main()
