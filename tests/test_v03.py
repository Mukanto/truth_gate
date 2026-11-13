"""Kapi v0.3 (spec 0.5 delta): identical-minus check, UNTESTED, minus_check and suppressed_minus.

Toy studies only.  Most tests build a ``Study`` in memory and call ``checks.evaluate`` (pure, no file, no guard); the
gate-level tests (certificate, exit code 6, K6 reproducibility) use the files ``tests/toy_studies/toy_v03_*.py``.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

import numpy as np

import _helpers
from _helpers import body, component, raised, toy_path
from kapi import Budget, Control, Criterion, Study, World, certificate
from kapi import minus as minus_mod
from kapi.checks import (
    VERDICTS, component_verdict, evaluate, is_capping, is_mandatory, study_verdict,
)
from kapi.cli import EXIT_CODES, format_table, main


# --------------------------------------------------------------------------
# helpers: in-memory studies
# --------------------------------------------------------------------------

def mean_gt_1(d):
    return bool(np.mean(d["x"]) > 1.0)


def plus_x(rng):
    return {"x": rng.normal(2.0, 1.0, 40)}


def minus_x(rng):
    return {"x": rng.normal(0.0, 1.0, 40)}


def make_study(plus=plus_x, minus=minus_x, fn=mean_gt_1, deterministic=False, samples=100, controls=True, **extra):
    kwargs = dict(
        name="mem",
        criteria=[Criterion("c", fn)],
        worlds={"plus": World(plus), "minus": World(minus, derived_from="plus", change="test")},
        controls=[Control("negate", ["c"], transform=lambda d, rng: {k: -v for k, v in d.items()})] if controls else [],
        deterministic=deterministic,
        budget=Budget(samples=samples),
    )
    kwargs.update(extra)
    return Study(**kwargs)


def comp(study, quick=False):
    result = evaluate(study, quick)
    assert len(result["components"]) == 1
    return result["components"][0]


def det_world(**arrays):
    return lambda rng: {k: np.array(v, copy=True) for k, v in arrays.items()}


class Uncomparable:
    """A value whose == raises."""

    def __eq__(self, other):
        raise RuntimeError("no comparison")

    __hash__ = None


class ArrayEq:
    """A value whose == returns an array (not a plain bool)."""

    def __eq__(self, other):
        return np.array([True, True])

    __hash__ = None


class Plain:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, Plain) and self.v == other.v

    __hash__ = None


# --------------------------------------------------------------------------
# delta 1.2: exact recursive equality
# --------------------------------------------------------------------------

class TestValuesEqual(unittest.TestCase):
    def test_arrays_equal_and_not_equal(self):
        a = np.array([1.0, 2.0, 3.0])
        self.assertTrue(minus_mod.values_equal(a, a.copy()))
        self.assertFalse(minus_mod.values_equal(a, a + np.array([0, 0, 1e-12])))
        self.assertTrue(minus_mod.values_equal(np.array([0.0]), np.array([-0.0])))  # == semantics: no sign distinction

    def test_one_ulp_is_a_difference(self):
        a = np.array([1.0])
        self.assertFalse(minus_mod.values_equal(a, np.nextafter(a, 2.0)))

    def test_nan_equals_nan_for_float_and_complex(self):
        self.assertTrue(minus_mod.values_equal(np.array([1.0, np.nan]), np.array([1.0, np.nan])))
        self.assertTrue(minus_mod.values_equal(np.array([complex(np.nan, 1.0)]), np.array([complex(np.nan, 1.0)])))
        self.assertTrue(minus_mod.values_equal(float("nan"), float("nan")))
        self.assertFalse(minus_mod.values_equal(np.array([np.nan]), np.array([1.0])))

    def test_nat_is_not_equal_to_nat(self):
        nat = np.array(["NaT"], dtype="datetime64[s]")
        self.assertFalse(minus_mod.values_equal(nat, nat.copy()))  # equal_nan is applied to float and complex only

    def test_dtype_difference(self):
        self.assertFalse(minus_mod.values_equal(np.array([1.0], dtype=np.float32), np.array([1.0], dtype=np.float64)))
        self.assertFalse(minus_mod.values_equal(np.array([1]), np.array([1.0])))
        self.assertFalse(minus_mod.values_equal(np.array([True]), np.array([1])))

    def test_shape_difference(self):
        self.assertFalse(minus_mod.values_equal(np.zeros(3), np.zeros(4)))
        self.assertFalse(minus_mod.values_equal(np.zeros((2, 3)), np.zeros((3, 2))))
        self.assertFalse(minus_mod.values_equal(np.zeros(3), np.zeros((1, 3))))
        self.assertTrue(minus_mod.values_equal(np.zeros((2, 3)), np.zeros((2, 3))))

    def test_python_numbers_are_converted(self):
        self.assertTrue(minus_mod.values_equal(1, 1))
        self.assertTrue(minus_mod.values_equal(2.5, np.float64(2.5)))
        self.assertFalse(minus_mod.values_equal(1, 1.0))  # int64 vs float64
        self.assertFalse(minus_mod.values_equal(1, 2))
        self.assertTrue(minus_mod.values_equal(np.array(3.0), 3.0))  # 0-d array vs number

    def test_dict_recursion(self):
        a = {"p": np.arange(3), "q": {"r": [1, 2.0, "s"]}}
        b = {"p": np.arange(3), "q": {"r": [1, 2.0, "s"]}}
        self.assertTrue(minus_mod.values_equal(a, b))
        b["q"]["r"][1] = 2.5
        self.assertFalse(minus_mod.values_equal(a, b))
        self.assertFalse(minus_mod.values_equal({"p": 1}, {"p": 1, "extra": 2}))
        self.assertFalse(minus_mod.values_equal({"p": 1}, {"other": 1}))

    def test_list_and_tuple(self):
        self.assertTrue(minus_mod.values_equal([1, 2, [3, np.array([4.0])]], [1, 2, [3, np.array([4.0])]]))
        self.assertFalse(minus_mod.values_equal([1, 2], [1, 2, 3]))
        self.assertFalse(minus_mod.values_equal([1, 2], [1, 3]))
        self.assertTrue(minus_mod.values_equal((1, np.array([np.nan])), (1, np.array([np.nan]))))
        self.assertFalse(minus_mod.values_equal([1, 2], (1, 2)))  # interpretation: the container type must match

    def test_anything_else_uses_eq(self):
        self.assertTrue(minus_mod.values_equal("abc", "abc"))
        self.assertFalse(minus_mod.values_equal("abc", "abd"))
        self.assertTrue(minus_mod.values_equal(None, None))
        self.assertTrue(minus_mod.values_equal(Plain(1), Plain(1)))
        self.assertFalse(minus_mod.values_equal(Plain(1), Plain(2)))

    def test_eq_that_raises_counts_as_not_equal(self):
        self.assertFalse(minus_mod.values_equal(Uncomparable(), Uncomparable()))
        self.assertFalse(minus_mod.values_equal({"k": Uncomparable()}, {"k": Uncomparable()}))
        self.assertFalse(minus_mod.values_equal([Uncomparable()], [Uncomparable()]))

    def test_eq_that_does_not_return_a_plain_bool_counts_as_not_equal(self):
        self.assertFalse(minus_mod.values_equal(ArrayEq(), ArrayEq()))
        self.assertFalse(minus_mod.values_equal({"k": ArrayEq()}, {"k": ArrayEq()}))

    def test_object_arrays(self):
        a = np.empty(2, dtype=object)
        a[0], a[1] = {"u": 1}, [2, 3]
        b = np.empty(2, dtype=object)
        b[0], b[1] = {"u": 1}, [2, 3]
        self.assertTrue(minus_mod.values_equal(a, b))
        b[1] = [2, 4]
        self.assertFalse(minus_mod.values_equal(a, b))
        raising = np.empty(1, dtype=object)
        raising[0] = Uncomparable()
        self.assertFalse(minus_mod.values_equal(raising, raising.copy()))

    def test_samples_identical_and_changed_keys(self):
        a = {"x": np.arange(3.0), "y": np.ones(2)}
        b = {"x": np.arange(3.0), "y": np.ones(2)}
        self.assertTrue(minus_mod.samples_identical(a, b))
        self.assertEqual(minus_mod.changed_keys(a, b), [])
        b["y"] = np.zeros(2)
        self.assertFalse(minus_mod.samples_identical(a, b))
        self.assertEqual(minus_mod.changed_keys(a, b), ["y"])
        b["z"] = np.zeros(1)  # key only in one sample
        self.assertFalse(minus_mod.samples_identical(a, b))
        self.assertEqual(minus_mod.changed_keys(a, b), ["y", "z"])
        self.assertEqual(minus_mod.changed_keys(b, a), ["y", "z"])
        self.assertFalse(minus_mod.samples_identical({"x": np.zeros(1)}, {"w": np.zeros(1)}))
        self.assertEqual(minus_mod.changed_keys({"x": np.zeros(1)}, {"w": np.zeros(1)}), ["w", "x"])

    def test_empty_samples_are_identical(self):
        self.assertTrue(minus_mod.samples_identical({}, {}))


# --------------------------------------------------------------------------
# delta 1.3: read-key recording
# --------------------------------------------------------------------------

DATA = {"a": np.arange(3.0), "b": np.ones(2), "c": np.zeros(1)}


def recorded(fn):
    return minus_mod.record_read_keys(Criterion("c", fn), DATA)


class TestRecordingDict(unittest.TestCase):
    def test_getitem(self):
        self.assertEqual(recorded(lambda d: bool(d["a"][0] == 0)), ({"a"}, False))

    def test_get(self):
        self.assertEqual(recorded(lambda d: d.get("b") is not None), ({"b"}, False))
        self.assertEqual(recorded(lambda d: d.get("missing", 0) == 0), ({"missing"}, False))

    def test_contains(self):
        self.assertEqual(recorded(lambda d: "c" in d), ({"c"}, False))
        self.assertEqual(recorded(lambda d: "nope" not in d), ({"nope"}, False))

    def test_several_keys_and_repeats(self):
        self.assertEqual(recorded(lambda d: bool(d["a"][0] + d["a"][1] + d["b"][0])), ({"a", "b"}, False))

    def test_reads_nothing(self):
        self.assertEqual(recorded(lambda d: True), (set(), False))

    def test_whole_mapping_access_marks_all_keys(self):
        cases = {
            "iter": lambda d: [k for k in d],
            "list": lambda d: list(d),
            "keys": lambda d: list(d.keys()),
            "items": lambda d: list(d.items()),
            "values": lambda d: list(d.values()),
            "copy": lambda d: d.copy(),
            "len": lambda d: len(d),
            "bool": lambda d: bool(d),
            "dict()": lambda d: dict(d),
            "**d": lambda d: (lambda **kw: kw)(**d),
            "{**d}": lambda d: {**d},
            "==": lambda d: d == {},
            "!=": lambda d: d != {},
            "sorted": lambda d: sorted(d),
            "repr": lambda d: repr(d),
            "pop": lambda d: d.pop("a"),
            "setitem": lambda d: d.__setitem__("a", 1),
            "update": lambda d: d.update({"a": 1}),
        }
        for name, fn in cases.items():
            with self.subTest(access=name):
                self.assertTrue(recorded(fn)[1])

    def test_recorded_keys_are_kept_when_all_keys_read(self):
        keys, whole = recorded(lambda d: (d["a"], list(d.keys())))
        self.assertEqual((keys, whole), ({"a"}, True))

    def test_a_raising_call_counts_as_all_keys_read_and_keeps_keys(self):
        def fn(d):
            d["a"]
            raise ValueError("boom")

        self.assertEqual(recorded(fn), ({"a"}, True))

    def test_recording_call_does_not_mutate_the_data(self):
        before = {k: v.copy() for k, v in DATA.items()}
        recorded(lambda d: d["a"].__setitem__(0, 99.0))
        for k in DATA:
            np.testing.assert_array_equal(DATA[k], before[k])

    def test_recorder_is_a_dict_subclass_only_on_recording_calls(self):
        seen = []

        def fn(d):
            seen.append(type(d))
            return True

        minus_mod.record_read_keys(Criterion("c", fn), DATA)
        self.assertTrue(issubclass(seen[0], dict) and seen[0] is not dict)
        seen.clear()
        s = make_study(fn=fn, samples=5)
        evaluate(s, False)
        counted = seen[: -2]  # the last two calls are the recording calls of delta 1.3
        self.assertTrue(counted)
        self.assertTrue(all(t is dict for t in counted))
        self.assertTrue(all(t is not dict for t in seen[-2:]))


# --------------------------------------------------------------------------
# delta 1.1 / 1.4: the check inside the evaluation
# --------------------------------------------------------------------------

class TestIdenticalMinusStochastic(unittest.TestCase):
    def test_identical_by_pairing(self):
        c = comp(make_study(minus=plus_x))
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertEqual(c["verdict"], "UNTESTED")
        self.assertEqual(c["minus_check"], {"identical": True, "read_keys": ["x"], "changed_keys": [], "paired": True})

    def test_not_identical_when_the_world_changes(self):
        c = comp(make_study())
        self.assertNotIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertFalse(c["minus_check"]["identical"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["x"])

    def test_one_changed_key_among_several(self):
        plus = lambda rng: {"x": rng.normal(2.0, 1.0, 40), "y": rng.normal(0.0, 1.0, 10)}
        minus = lambda rng: {"x": rng.normal(2.0, 1.0, 40), "y": rng.normal(3.0, 1.0, 10)}
        c = comp(make_study(plus=plus, minus=minus))
        self.assertFalse(c["minus_check"]["identical"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["y"])
        self.assertNotIn("K2_MINUS_IDENTICAL", c["flags"])

    def test_changed_unread_key_is_not_identical(self):
        plus = lambda rng: {"x": rng.normal(2.0, 1.0, 40), "u": rng.normal(0.0, 1.0, 5)}
        minus = lambda rng: {"x": rng.normal(2.0, 1.0, 40), "u": rng.normal(9.0, 1.0, 5)}
        c = comp(make_study(plus=plus, minus=minus))
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")
        self.assertIn("K2_MINUS_UNREAD", c["flags"])
        self.assertEqual(c["minus_check"]["read_keys"], ["x"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["u"])

    def test_key_present_in_only_one_sample(self):
        plus = lambda rng: {"x": rng.normal(2.0, 1.0, 40)}
        minus = lambda rng: {"x": rng.normal(2.0, 1.0, 40), "extra": np.zeros(1)}
        c = comp(make_study(plus=plus, minus=minus))
        self.assertFalse(c["minus_check"]["identical"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["extra"])

    def test_nan_in_both_is_still_identical(self):
        def plus(rng):
            x = rng.normal(2.0, 1.0, 40)
            x[0] = np.nan
            return {"x": x}

        c = comp(make_study(plus=plus, minus=plus, fn=lambda d: bool(np.nanmean(d["x"]) > 1.0)))
        self.assertTrue(c["minus_check"]["identical"])

    def test_nan_in_one_is_not_identical(self):
        def minus(rng):
            x = rng.normal(2.0, 1.0, 40)
            x[0] = np.nan
            return {"x": x}

        c = comp(make_study(minus=minus, fn=lambda d: bool(np.nanmean(d["x"]) > 1.0)))
        self.assertFalse(c["minus_check"]["identical"])

    def test_dtype_difference_is_not_identical(self):
        minus = lambda rng: {"x": rng.normal(2.0, 1.0, 40).astype(np.float32)}
        c = comp(make_study(minus=minus))
        self.assertFalse(c["minus_check"]["identical"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["x"])

    def test_shape_difference_is_not_identical(self):
        minus = lambda rng: {"x": rng.normal(2.0, 1.0, 41)}
        self.assertFalse(comp(make_study(minus=minus))["minus_check"]["identical"])

    def test_nested_containers_in_object_arrays(self):
        def world(rng):
            x = np.empty(2, dtype=object)
            x[0], x[1] = {"v": [1, 2]}, [rng.integers(0, 3)]
            return {"x": x}

        fn = lambda d: True
        self.assertTrue(comp(make_study(plus=world, minus=world, fn=fn))["minus_check"]["identical"])

        def other(rng):
            x = np.empty(2, dtype=object)
            x[0], x[1] = {"v": [1, 3]}, [rng.integers(0, 3)]
            return {"x": x}

        self.assertFalse(comp(make_study(plus=world, minus=other, fn=fn))["minus_check"]["identical"])

    def test_value_whose_eq_raises_is_not_identical(self):
        def world(rng):
            x = np.empty(1, dtype=object)
            x[0] = Uncomparable()
            return {"x": x}

        c = comp(make_study(plus=world, minus=world, fn=lambda d: True))
        self.assertFalse(c["minus_check"]["identical"])
        self.assertNotIn("K2_MINUS_IDENTICAL", c["flags"])

    def test_a_minus_that_consumes_the_generator_differently_is_not_detected(self):
        def minus(rng):
            rng.random()  # same declared distribution, different consumption of the generator
            return {"x": rng.normal(2.0, 1.0, 40)}

        c = comp(make_study(minus=minus))
        self.assertFalse(c["minus_check"]["identical"])  # known weakness (spec 0.5 delta 5)

    def test_paired_draw_uses_the_plus_generator_and_is_not_counted(self):
        plus_first, minus_first, calls = [], [], {"minus": 0}

        def plus(rng):
            plus_first.append(rng.random())
            return {"x": np.array([2.0])}

        def minus(rng):
            calls["minus"] += 1
            minus_first.append(rng.random())
            return {"x": np.array([0.0])}

        c = comp(make_study(plus=plus, minus=minus, fn=lambda d: bool(d["x"][0] > 1.0), samples=7))
        self.assertEqual(calls["minus"], 8)  # 7 counted samples + 1 paired draw
        self.assertEqual(minus_first[-1], plus_first[0])  # the paired draw used the generator of world:plus, i = 0
        self.assertNotEqual(minus_first[0], plus_first[0])  # the counted minus sample uses its own stream
        self.assertEqual(c["counts"]["world:minus"]["n"], 7)

    def test_counted_results_do_not_depend_on_the_check(self):
        s = make_study()
        c = comp(s)
        # the extra draw and the recording calls come after the counted samples, so the counts equal those of a run
        # in which the criterion never sees a recorder: compare against the numbers of the unchanged toy_good logic
        self.assertEqual(c["counts"]["world:plus"], {"holds": 100, "undefined": 0, "n": 100})
        self.assertEqual(c["counts"]["world:minus"]["holds"], 0)

    def test_quick_mode_also_checks(self):
        c = comp(make_study(minus=plus_x), quick=True)
        self.assertTrue(c["minus_check"]["identical"])
        self.assertEqual(c["counts"]["world:plus"]["n"], 20)

    def test_failed_paired_draw_is_not_identical_and_raises_nothing(self):
        state = {"calls": 0}

        def minus(rng):
            state["calls"] += 1
            if state["calls"] > 10:
                raise RuntimeError("only the extra draw fails")
            return {"x": rng.normal(2.0, 1.0, 40)}

        c = comp(make_study(minus=minus, samples=10))
        self.assertEqual(c["minus_check"], {"identical": False, "read_keys": [], "changed_keys": [], "paired": True})
        self.assertNotIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])


class TestIdenticalMinusDeterministic(unittest.TestCase):
    def fn(self, d):
        return bool(abs(float(d["v"][0]) - 3.0) < 0.5)

    def test_identical(self):
        s = make_study(plus=det_world(v=[3.0]), minus=det_world(v=[3.0]), fn=self.fn, deterministic=True)
        c = comp(s)
        self.assertEqual(c["minus_check"], {"identical": True, "read_keys": ["v"], "changed_keys": [], "paired": False})
        self.assertEqual(c["verdict"], "UNTESTED")

    def test_not_identical(self):
        s = make_study(plus=det_world(v=[3.0]), minus=det_world(v=[-3.0]), fn=self.fn, deterministic=True)
        c = comp(s)
        self.assertFalse(c["minus_check"]["identical"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["v"])
        self.assertNotIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertEqual(c["verdict"], "FALSIFIABLE")

    def test_the_already_generated_samples_are_compared_without_an_extra_draw(self):
        calls = {"minus": 0}

        def minus(rng):
            calls["minus"] += 1
            return {"v": np.array([3.0])}

        evaluate(make_study(plus=det_world(v=[3.0]), minus=minus, fn=self.fn, deterministic=True), False)
        self.assertEqual(calls["minus"], 3)  # indices 0, 1, 2 (determinism check) and nothing more

    def test_float32_versus_float64(self):
        s = make_study(plus=det_world(v=np.array([3.0])), minus=lambda rng: {"v": np.array([3.0], dtype=np.float32)},
                       fn=self.fn, deterministic=True)
        self.assertFalse(comp(s)["minus_check"]["identical"])

    def test_nan_data_deterministic(self):
        s = make_study(plus=det_world(v=[np.nan]), minus=det_world(v=[np.nan]), fn=lambda d: True, deterministic=True)
        self.assertTrue(comp(s)["minus_check"]["identical"])

    def test_nondeterministic_study_still_gets_the_check(self):
        counter = {"n": 0}

        def minus(rng):
            counter["n"] += 1
            return {"v": np.array([float(counter["n"])])}

        result = evaluate(make_study(plus=det_world(v=[5.0]), minus=minus, fn=self.fn, deterministic=True), False)
        self.assertIn("NONDETERMINISTIC", result["study_flags"])
        self.assertFalse(result["components"][0]["minus_check"]["identical"])  # the stored i = 0 sample was used


# --------------------------------------------------------------------------
# delta 1.3 / 1.4 at evaluation level: K2_MINUS_UNREAD
# --------------------------------------------------------------------------

def two_key(rng, b_mean=0.0):
    return {"a": rng.normal(2.0, 1.0, 40), "b": rng.normal(b_mean, 1.0, 10)}


class TestMinusUnread(unittest.TestCase):
    def study(self, fn, b_mean=5.0):
        return make_study(plus=two_key, minus=lambda rng: two_key(rng, b_mean), fn=fn)

    def test_raised_when_only_unread_keys_changed(self):
        c = comp(self.study(lambda d: bool(np.mean(d["a"]) > 1.0)))
        self.assertIn("K2_MINUS_UNREAD", c["flags"])
        self.assertEqual(c["minus_check"]["read_keys"], ["a"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["b"])

    def test_raised_for_get_and_in(self):
        self.assertIn("K2_MINUS_UNREAD", comp(self.study(lambda d: bool(np.mean(d.get("a")) > 1.0)))["flags"])
        self.assertIn("K2_MINUS_UNREAD", comp(self.study(lambda d: "a" in d))["flags"])

    def test_not_raised_when_a_read_key_changed(self):
        c = comp(self.study(lambda d: bool(np.mean(d["a"]) > 1.0 and np.mean(d["b"]) < 1.0)))
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])
        self.assertEqual(c["minus_check"]["read_keys"], ["a", "b"])

    def test_not_raised_when_the_changed_key_is_the_only_one_read(self):
        c = comp(self.study(lambda d: bool(np.mean(d["b"]) < 1.0)))
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])
        self.assertEqual(c["minus_check"]["read_keys"], ["b"])

    def test_whole_mapping_access_gives_all_and_no_flag(self):
        c = comp(self.study(lambda d: len(d) == 2 and bool(np.mean(d["a"]) > 1.0)))
        self.assertEqual(c["minus_check"]["read_keys"], "ALL")
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])

    def test_iteration_gives_all(self):
        c = comp(self.study(lambda d: sorted(d) == ["a", "b"]))
        self.assertEqual(c["minus_check"]["read_keys"], "ALL")

    def test_criterion_that_reads_nothing_never_gets_the_flag(self):
        c = comp(self.study(lambda d: True))
        self.assertEqual(c["minus_check"]["read_keys"], [])
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])
        self.assertFalse(c["minus_check"]["identical"])

    def test_recording_call_that_raises_counts_as_all(self):
        def fn(d):
            if type(d) is not dict:  # only the recording calls receive a dict subclass
                raise RuntimeError("recorder")
            return bool(np.mean(d["a"]) > 1.0)

        c = comp(self.study(fn))
        self.assertEqual(c["minus_check"]["read_keys"], "ALL")
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])
        self.assertNotIn("K1_UNDEFINED", c["flags"])  # counted evaluations received plain dicts

    def test_not_raised_when_a_read_key_is_missing_in_one_sample(self):
        plus = lambda rng: {"a": rng.normal(2.0, 1.0, 40), "b": rng.normal(0.0, 1.0, 10)}
        minus = lambda rng: {"b": rng.normal(5.0, 1.0, 10)}  # "a" absent in minus

        def fn(d):
            return "a" in d and bool(np.mean(d["a"]) > 1.0)

        c = comp(make_study(plus=plus, minus=minus, fn=fn))
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])
        self.assertEqual(c["minus_check"]["changed_keys"], ["a", "b"])

    def test_not_raised_when_identical(self):
        c = comp(make_study(plus=two_key, minus=two_key, fn=lambda d: bool(np.mean(d["a"]) > 1.0)))
        self.assertTrue(c["minus_check"]["identical"])
        self.assertNotIn("K2_MINUS_UNREAD", c["flags"])

    def test_read_keys_are_a_union_over_both_samples(self):
        def fn(d):
            return bool(np.mean(d["a"]) > 1.0) if d["b"].size == 10 else bool(np.mean(d["a"]) > 5.0)

        plus = two_key
        minus = lambda rng: {"a": rng.normal(2.0, 1.0, 40), "b": rng.normal(5.0, 1.0, 11)}
        c = comp(make_study(plus=plus, minus=minus, fn=fn))
        self.assertEqual(c["minus_check"]["read_keys"], ["a", "b"])

    def test_deterministic_mode(self):
        s = make_study(plus=det_world(a=[3.0], b=[0.0]), minus=det_world(a=[3.0], b=[9.0]),
                       fn=lambda d: bool(d["a"][0] > 1.0), deterministic=True)
        c = comp(s)
        self.assertIn("K2_MINUS_UNREAD", c["flags"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")

    def test_the_flag_is_informational(self):
        self.assertFalse(is_mandatory("K2_MINUS_UNREAD"))
        self.assertFalse(is_capping("K2_MINUS_UNREAD"))
        self.assertEqual(component_verdict(["K2_MINUS_UNREAD"]), "FALSIFIABLE")
        self.assertEqual(component_verdict(["K2_MINUS_UNREAD", "K2_NO_SEPARATION"]), "NOT_FALSIFIABLE")
        self.assertEqual(component_verdict(["K2_MINUS_UNREAD", "K2_LOW_POWER"]), "WEAK")


# --------------------------------------------------------------------------
# delta 1.5: suppression
# --------------------------------------------------------------------------

class TestSuppressionWhenIdentical(unittest.TestCase):
    def test_flags_are_suppressed_and_listed(self):
        c = comp(make_study(minus=plus_x))  # the criterion holds in plus and in the counted minus samples
        self.assertEqual(c["suppressed_minus"], ["K2_FAILS_UNREACHABLE", "K2_HIGH_SIZE", "K2_NO_SEPARATION"])
        for flag in c["suppressed_minus"]:
            self.assertNotIn(flag, c["flags"])
        self.assertEqual(c["flags"], ["K2_MINUS_IDENTICAL"])
        self.assertEqual(c["verdict"], "UNTESTED")
        self.assertNotIn("suppressed", c)  # the 0.4 delta 2 fields are independent
        self.assertNotIn("suppressed_by", c)

    def test_only_flags_that_would_have_been_raised_are_listed(self):
        # the criterion fails in the counted minus samples (they use their own stream), so only some flags would exist
        plus = lambda rng: {"x": rng.normal(1.0, 1.0, 40)}
        fn = lambda d: bool(np.mean(d["x"]) > 1.0)
        c = comp(make_study(plus=plus, minus=plus, fn=fn))
        self.assertTrue(c["minus_check"]["identical"])
        self.assertTrue(set(c.get("suppressed_minus", [])) <= {"K2_FAILS_UNREACHABLE", "K2_HIGH_SIZE", "K2_NO_SEPARATION"})
        if "suppressed_minus" in c:
            self.assertEqual(c["suppressed_minus"], sorted(c["suppressed_minus"]))

    def test_nothing_suppressed_and_no_field_when_not_identical(self):
        c = comp(make_study())
        self.assertNotIn("suppressed_minus", c)

    def test_other_flags_are_kept(self):
        c = comp(make_study(minus=plus_x, controls=False))
        self.assertIn("K4_NO_CONTROL", c["flags"])
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")  # step 2 before UNTESTED

    def test_high_rate_and_k5_flags_are_not_suppressed(self):
        c = comp(make_study(minus=plus_x, fn=lambda d: True))
        self.assertIn("K5_HOLDS_ON_NOISE", c["flags"])
        self.assertTrue(any(f.startswith("HIGH_RATE:") for f in c["flags"]))
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")

    def test_suppression_with_k2_holds_unreachable(self):
        c = comp(make_study(minus=plus_x, fn=lambda d: False))
        self.assertIn("K2_HOLDS_UNREACHABLE", c["flags"])
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")  # K2_HOLDS_UNREACHABLE is mandatory
        # both suppressions apply to K2_NO_SEPARATION and are filled independently
        self.assertEqual(c["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertIn("K2_NO_SEPARATION", c["suppressed"])
        self.assertEqual(c["suppressed_minus"], ["K2_NO_SEPARATION"])
        self.assertNotIn("K2_NO_SEPARATION", c["flags"])

    def test_suppression_without_k2_holds_unreachable(self):
        c = comp(make_study(minus=plus_x))
        self.assertNotIn("K2_HOLDS_UNREACHABLE", c["flags"])
        self.assertNotIn("suppressed_by", c)
        self.assertTrue(c["suppressed_minus"])

    def test_independent_fields_when_only_the_cascade_applies(self):
        c = comp(make_study(fn=lambda d: False))  # minus is distinct, plus never holds
        self.assertEqual(c["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertNotIn("suppressed_minus", c)

    def test_deterministic_suppression(self):
        s = make_study(plus=det_world(v=[3.0]), minus=det_world(v=[3.0]), fn=lambda d: bool(abs(d["v"][0] - 3.0) < 0.5),
                       deterministic=True)
        c = comp(s)
        self.assertEqual(c["suppressed_minus"], ["K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION"])  # no HIGH_SIZE in det mode
        self.assertEqual(c["verdict"], "UNTESTED")

    def test_deterministic_with_holds_unreachable(self):
        s = make_study(plus=det_world(v=[3.0]), minus=det_world(v=[3.0]), fn=lambda d: False, deterministic=True)
        c = comp(s)
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(c["suppressed_minus"], ["K2_NO_SEPARATION"])
        self.assertIn("K2_NO_SEPARATION", c["suppressed"])

    def test_cascade_switch_does_not_change_the_minus_suppression(self):
        s = make_study(minus=plus_x, fn=lambda d: False)
        on = evaluate(s, False)["components"][0]
        off = evaluate(s, False, suppress_cascade=False)["components"][0]
        self.assertEqual(on["suppressed_minus"], off["suppressed_minus"])
        self.assertEqual(on["verdict"], off["verdict"])
        self.assertNotIn("suppressed_by", off)
        self.assertNotIn("K2_NO_SEPARATION", off["flags"])


# --------------------------------------------------------------------------
# delta 2: verdict order and severity
# --------------------------------------------------------------------------

class TestVerdictOrder(unittest.TestCase):
    def test_verdict_tuple(self):
        self.assertEqual(VERDICTS, ("FALSIFIABLE", "WEAK", "UNTESTED", "NOT_FALSIFIABLE", "UNDEFINED"))

    def test_untested_alone(self):
        self.assertEqual(component_verdict(["K2_MINUS_IDENTICAL"]), "UNTESTED")
        self.assertEqual(component_verdict({"K2_MINUS_IDENTICAL", "K2_MINUS_UNREAD", "BAD_RETURN"}), "UNTESTED")

    def test_untested_beats_capping(self):
        for flag in ("K2_LOW_POWER", "K3_INCONCLUSIVE", "K4_WAIVED", "K4_INCONCLUSIVE", "K5_INCONCLUSIVE:noise"):
            self.assertEqual(component_verdict(["K2_MINUS_IDENTICAL", flag]), "UNTESTED", flag)

    def test_mandatory_beats_untested(self):
        for flag in ("K2_HOLDS_UNREACHABLE", "K5_HOLDS_ON_NOISE", "K4_NO_CONTROL", "K2_UNRESOLVABLE", "HIGH_RATE:probe:noise",
                     "K2_HIGH_SIZE"):
            self.assertEqual(component_verdict(["K2_MINUS_IDENTICAL", flag]), "NOT_FALSIFIABLE", flag)

    def test_k1_beats_everything(self):
        self.assertEqual(component_verdict(["K2_MINUS_IDENTICAL", "K1_UNDEFINED"]), "UNDEFINED")
        self.assertEqual(component_verdict(["K2_MINUS_IDENTICAL", "K1_UNDEFINED", "K4_NO_CONTROL"]), "UNDEFINED")

    def test_untested_flag_is_not_mandatory_or_capping(self):
        self.assertFalse(is_mandatory("K2_MINUS_IDENTICAL"))
        self.assertFalse(is_capping("K2_MINUS_IDENTICAL"))

    def test_study_verdict_severity(self):
        self.assertEqual(study_verdict(["FALSIFIABLE", "UNTESTED"], []), "UNTESTED")
        self.assertEqual(study_verdict(["WEAK", "UNTESTED"], []), "UNTESTED")
        self.assertEqual(study_verdict(["UNTESTED", "WEAK", "FALSIFIABLE"], []), "UNTESTED")
        self.assertEqual(study_verdict(["UNTESTED", "NOT_FALSIFIABLE"], []), "NOT_FALSIFIABLE")
        self.assertEqual(study_verdict(["UNTESTED", "UNDEFINED"], []), "UNDEFINED")
        self.assertEqual(study_verdict(["UNTESTED"], []), "UNTESTED")
        self.assertEqual(study_verdict(["WEAK"], []), "WEAK")
        self.assertEqual(study_verdict(["FALSIFIABLE"], []), "FALSIFIABLE")

    def test_study_flags_raise_untested_to_not_falsifiable(self):
        self.assertEqual(study_verdict(["UNTESTED"], ["K7_REGIME_UNCOVERED"]), "NOT_FALSIFIABLE")
        self.assertEqual(study_verdict(["UNTESTED"], ["K6_LEAK_ATTEMPT"]), "NOT_FALSIFIABLE")
        self.assertEqual(study_verdict(["UNDEFINED"], ["K6_LEAK_ATTEMPT"]), "UNDEFINED")

    def test_untested_versus_mandatory_flag_on_a_study(self):
        c = comp(make_study(minus=plus_x, fn=lambda d: True))  # vacuous criterion: holds on noise
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertIn("K5_HOLDS_ON_NOISE", c["flags"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")

    def test_untested_versus_k1_on_a_study(self):
        c = comp(make_study(minus=plus_x, fn=lambda d: None))
        self.assertIn("K1_UNDEFINED", c["flags"])
        self.assertEqual(c["verdict"], "UNDEFINED")

    def test_untested_versus_capping_on_a_study(self):
        plus = lambda rng: {"x": rng.normal(1.0, 1.0, 40)}  # mean(x) > 1 holds in about half of the samples
        c = comp(make_study(plus=plus, minus=plus))
        self.assertIn("K2_LOW_POWER", c["flags"])
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertEqual(c["verdict"], "UNTESTED")

    def test_study_level_verdict_of_an_untested_component(self):
        result = evaluate(make_study(minus=plus_x), False)
        self.assertEqual([c["verdict"] for c in result["components"]], ["UNTESTED"])
        self.assertEqual(result["study_flags"], [])
        self.assertEqual(study_verdict([c["verdict"] for c in result["components"]], result["study_flags"]), "UNTESTED")

    def test_several_components_take_the_most_severe(self):
        study = Study(
            name="two",
            criteria=[Criterion("good", mean_gt_1), Criterion("bad", lambda d: True)],
            worlds={"plus": World(plus_x), "minus": World(plus_x, derived_from="plus", change="none")},
            controls=[Control("negate", ["good", "bad"], transform=lambda d, rng: {"x": -d["x"]})],
            budget=Budget(samples=60),
        )
        verdicts = {c["id"]: c["verdict"] for c in evaluate(study, False)["components"]}
        self.assertEqual(verdicts, {"good": "UNTESTED", "bad": "NOT_FALSIFIABLE"})


# --------------------------------------------------------------------------
# gate level: certificate, exit code 6, reproducibility
# --------------------------------------------------------------------------

class TestCertificateFields(unittest.TestCase):
    def test_versions(self):
        b = body("toy_good")
        self.assertEqual(b["tool_version"], "0.4.1")
        self.assertEqual(b["spec_version"], "0.6")

    def test_minus_check_is_always_present(self):
        for toy in ("toy_good", "toy_good_det", "toy_v03_untested", "toy_v03_unread", "toy_waived", "toy_components_ok"):
            for comp_ in body(toy)["components"]:
                with self.subTest(toy=toy, component=comp_["id"]):
                    self.assertEqual(set(comp_["minus_check"]), {"identical", "read_keys", "changed_keys", "paired"})
                    self.assertIsInstance(comp_["minus_check"]["identical"], bool)
                    self.assertIsInstance(comp_["minus_check"]["paired"], bool)
                    self.assertTrue(comp_["minus_check"]["read_keys"] == "ALL"
                                    or isinstance(comp_["minus_check"]["read_keys"], list))
                    self.assertEqual(comp_["minus_check"]["changed_keys"], sorted(comp_["minus_check"]["changed_keys"]))

    def test_paired_follows_the_mode(self):
        self.assertTrue(component("toy_good")["minus_check"]["paired"])
        self.assertFalse(component("toy_good_det")["minus_check"]["paired"])

    def test_read_keys_are_sorted(self):
        self.assertEqual(component("toy_good")["minus_check"]["read_keys"], ["x"])

    def test_suppressed_minus_only_when_non_empty(self):
        self.assertNotIn("suppressed_minus", component("toy_good"))
        self.assertNotIn("suppressed_minus", component("toy_good_det"))
        self.assertEqual(component("toy_v03_untested")["suppressed_minus"],
                         ["K2_FAILS_UNREACHABLE", "K2_HIGH_SIZE", "K2_NO_SEPARATION"])
        self.assertEqual(component("toy_v03_untested_det")["suppressed_minus"],
                         ["K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION"])

    def test_components_of_one_criterion_share_the_result(self):
        comps = body("toy_components_ok")["components"]
        self.assertGreater(len(comps), 1)
        self.assertEqual(len({json.dumps(c["minus_check"], sort_keys=True) for c in comps}), 1)

    def test_known_limitations_state_the_delta_5_limits(self):
        text = " ".join(body("toy_good")["known_limitations"])
        for phrase in ("exact identity", "pairing", "top-level keys", "UNTESTED can hide a criterion defect"):
            self.assertIn(phrase, text)
        self.assertEqual(len(body("toy_good")["known_limitations"]), 5)  # spec 0.6 section 11 adds two (revision R-1)

    def test_untested_certificate_validates_and_round_trips(self):
        env = _helpers.run_toy("toy_v03_untested")
        self.assertEqual(certificate.validate_envelope(env), [])
        loaded = json.loads(json.dumps(env, ensure_ascii=False))
        self.assertEqual(certificate.body_sha256(loaded["body"]), env["body_sha256"])
        self.assertEqual(loaded["body"]["verdict"], "UNTESTED")

    def test_toy_verdicts(self):
        self.assertEqual(body("toy_v03_untested")["verdict"], "UNTESTED")
        self.assertEqual(body("toy_v03_untested_det")["verdict"], "UNTESTED")
        self.assertEqual(body("toy_v03_trap")["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(body("toy_v03_unread")["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(body("toy_good")["verdict"], "FALSIFIABLE")
        self.assertEqual(body("toy_good_det")["verdict"], "FALSIFIABLE")

    def test_flag_reachability(self):
        self.assertTrue(raised("toy_v03_untested", "K2_MINUS_IDENTICAL"))
        self.assertTrue(raised("toy_v03_untested_det", "K2_MINUS_IDENTICAL"))
        self.assertTrue(raised("toy_v03_trap", "K2_MINUS_IDENTICAL"))
        self.assertFalse(raised("toy_good", "K2_MINUS_IDENTICAL"))
        self.assertFalse(raised("toy_good_det", "K2_MINUS_IDENTICAL"))
        self.assertFalse(raised("toy_v03_unread", "K2_MINUS_IDENTICAL"))
        self.assertTrue(raised("toy_v03_unread", "K2_MINUS_UNREAD"))
        self.assertFalse(raised("toy_good", "K2_MINUS_UNREAD"))
        self.assertFalse(raised("toy_v03_untested", "K2_MINUS_UNREAD"))

    def test_trap_keeps_the_other_mandatory_flags(self):
        c = component("toy_v03_trap")
        self.assertIn("K5_HOLDS_ON_NOISE", c["flags"])
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertEqual(c["minus_check"]["read_keys"], [])  # the criterion reads nothing

    def test_replacement_no_separation_toy_raises_the_flag_without_an_identical_minus(self):
        self.assertTrue(raised("toy_no_separation_distinct", "K2_NO_SEPARATION"))
        self.assertFalse(raised("toy_no_separation_distinct", "K2_MINUS_IDENTICAL"))
        self.assertFalse(raised("toy_good", "K2_NO_SEPARATION"))

    def test_old_no_separation_toy_is_now_identical_by_pairing(self):
        # spec 0.5 delta 1.1: minus.generate with the plus generator reproduces plus when minus equals plus in law
        c = component("toy_no_separation")
        self.assertIn("K2_MINUS_IDENTICAL", c["flags"])
        self.assertNotIn("K2_NO_SEPARATION", c["flags"])  # suppressed by delta 1.5
        self.assertIn("K2_NO_SEPARATION", c["suppressed_minus"])
        self.assertTrue(c["minus_check"]["identical"] and c["minus_check"]["paired"])
        # The verdict is NOT_FALSIFIABLE, not UNTESTED: this toy's criterion also holds on noise, and the other
        # mandatory flags (K5_HOLDS_ON_NOISE, K4_CONTROL_ALSO_HOLDS, HIGH_RATE:*) are kept (delta 2, step 2 before step 3).
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")
        self.assertIn("K5_HOLDS_ON_NOISE", c["flags"])


class TestExitCode6(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="kapi_v03_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue()

    def test_exit_code_table(self):
        self.assertEqual(EXIT_CODES, {"FALSIFIABLE": 0, "WEAK": 1, "NOT_FALSIFIABLE": 2, "UNDEFINED": 3, "UNTESTED": 6})

    def test_untested_exits_6(self):
        for toy in ("toy_v03_untested", "toy_v03_untested_det"):
            with self.subTest(toy=toy):
                out = os.path.join(self.tmp, toy + ".json")
                code, stdout = self.run_cli("check", toy_path(toy), "--out", out)
                self.assertEqual(code, 6)
                self.assertIn("UNTESTED", stdout)
                self.assertIn("K2_MINUS_IDENTICAL", stdout)

    def test_other_codes_are_unchanged(self):
        for toy, code in (("toy_good", 0), ("toy_lowpower", 1), ("toy_no_control", 2), ("toy_v03_trap", 2),
                          ("toy_v03_unread", 2), ("toy_undefined_none", 3)):
            with self.subTest(toy=toy):
                out = os.path.join(self.tmp, toy + ".json")
                self.assertEqual(self.run_cli("check", toy_path(toy), "--out", out)[0], code)

    def test_usage_error_is_still_4_and_verify_codes_are_unchanged(self):
        self.assertEqual(self.run_cli("check")[0], 4)
        out = os.path.join(self.tmp, "u.json")
        self.run_cli("check", toy_path("toy_v03_untested"), "--out", out)
        self.assertEqual(self.run_cli("verify", out, toy_path("toy_v03_untested"))[0], 0)
        with open(out, encoding="utf-8") as fh:
            env = json.load(fh)
        env["body"]["verdict"] = "FALSIFIABLE"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(env, fh)
        self.assertEqual(self.run_cli("verify", out, toy_path("toy_v03_untested"))[0], 5)

    def test_table_lists_the_new_verdict_and_flag(self):
        table = format_table(body("toy_v03_untested"))
        self.assertIn("UNTESTED", table)
        self.assertIn("K2_MINUS_IDENTICAL", table)


class TestReproducibility(unittest.TestCase):
    def test_k6_is_unaffected_by_the_extra_calls(self):
        for toy in ("toy_good", "toy_good_det", "toy_v03_untested", "toy_v03_untested_det", "toy_v03_unread", "toy_v03_trap"):
            with self.subTest(toy=toy):
                self.assertFalse(raised(toy, "K6_NONREPRODUCIBLE"))
                self.assertFalse(raised(toy, "NONDETERMINISTIC"))

    def test_hash_is_reproducible(self):
        import kapi

        for toy in ("toy_v03_untested", "toy_v03_unread"):
            with self.subTest(toy=toy):
                again = kapi.run_gate(toy_path(toy))
                self.assertEqual(again["body_sha256"], _helpers.run_toy(toy)["body_sha256"])

    def test_nonreproducible_toy_is_still_flagged(self):
        self.assertTrue(raised("toy_nonreproducible", "K6_NONREPRODUCIBLE"))
        self.assertTrue(raised("toy_nondeterministic", "NONDETERMINISTIC"))

    def test_quick_and_full_differ_but_both_carry_the_check(self):
        quick = body("toy_good", quick=True)["components"][0]["minus_check"]
        full = body("toy_good")["components"][0]["minus_check"]
        self.assertEqual(quick, full)

    def test_evaluation_twice_gives_identical_results(self):
        s = make_study(minus=plus_x)
        self.assertEqual(json.dumps(certificate.jsonable(evaluate(s, False)), sort_keys=True),
                         json.dumps(certificate.jsonable(evaluate(s, False)), sort_keys=True))

    def test_counted_numbers_are_those_of_the_previous_version_for_a_sound_study(self):
        c = component("toy_good")
        self.assertEqual(c["counts"]["world:plus"], {"holds": 100, "undefined": 0, "n": 100})
        self.assertEqual(c["verdict"], "FALSIFIABLE")
        self.assertEqual(c["flags"], [])


if __name__ == "__main__":
    unittest.main()
