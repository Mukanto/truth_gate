"""Truth_Gate 0.5.0 (spec 0.7): the tests of section 5 that are not the two (G) tests of ``test_spec07_gaming.py``.

* one test per row of the soft/hard classification of section 1, in stochastic and in deterministic mode;
* the K1 boundaries of section 2.1 in integers (full mode 100 vs 101 of 200, quick mode 10 vs 11 of 20);
* K8 with abstentions (the limitation of 2.2, asserted as recorded) and the deterministic ``minus`` abstention;
* an identical ``minus`` with abstentions; the compatibility statement of section 4 on hand-built studies;
* certificate fields and validation (2.4), ``explain`` and the documentation (2.5), the renamed texts (3).

Studies are built in the tests (``make_study``): the data are constants, and the *tag* array decides what the criterion
does, so every row has an exactly known count.  The tag is a ``str`` array, which the generic probes leave unchanged.
"""

import contextlib
import copy
import dataclasses
import io
import itertools
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

import _helpers
from test_external import Base as ExternalBase
from test_external import WORLD_PY
from test_k8 import K8Case
from truth_gate import Budget, Control, Criterion, Study, World, certificate, checks, ci, cli, explain, guard, minus
from truth_gate.k8 import BUILTIN_ID
from truth_gate.patterns import Pattern
from truth_gate.sampling import stream_rng
from truth_gate.study import StudyError, load_study

ROOT = _helpers.ROOT
SEED = Budget().base_seed
SPEC07_FIXTURES = os.path.join(ROOT, "tests", "toy_studies_spec07")


def read(path):
    with open(os.path.join(ROOT, path), "r", encoding="utf-8") as handle:
        return handle.read()


# --------------------------------------------------------------------------
# Studies built from tags
# --------------------------------------------------------------------------

def behave(d):
    """The criterion: what it does is decided by the ``tag`` of the sample."""
    tag = str(d["tag"][0])
    if tag == "ok":
        holds = bool(np.mean(d["x"]) > 2.0)
        return holds
    if tag == "okc":  # the same for a criterion with components a and b
        holds = bool(np.mean(d["x"]) > 2.0)
        return {"a": holds, "b": holds}
    if tag == "none":
        return None
    if tag == "false":  # the None = False twin of "none"
        return False
    if tag == "raise":
        raise ValueError("boom")
    if tag == "nan":
        return float("nan")
    if tag == "one":
        return 1
    if tag == "str":
        return "HOLDS"
    if tag == "array":
        return np.array([True])
    if tag == "cnone":  # components: the whole return is None
        return None
    if tag == "cdict":  # components: one value None, the other FAILS
        return {"a": None, "b": False}
    if tag == "cmissing":  # components: b is missing from the dict
        return {"a": False}
    if tag == "cnondict":  # components: not a dict
        return True
    if tag == "cnan":  # components: a wrong type inside the dict
        return {"a": float("nan"), "b": False}
    raise AssertionError(tag)


def world(x, tag="ok", length=20):
    """A world of constant data; ``tag`` may be a function of the generator (drawn first, so counts are exact)."""
    def generate(rng):
        value = tag(rng) if callable(tag) else tag
        return {"x": np.full(length, float(x)), "tag": np.array([value])}
    return generate


def raising(rng):
    raise RuntimeError("the world cannot be generated")


def not_a_dict(rng):
    return [1, 2, 3]


def abstaining_on(stream: str, n: int, k: int, tag="none", otherwise="ok"):
    """A tag function that gives ``tag`` on exactly ``k`` of the first ``n`` samples of ``stream`` (a function of the
    first draw of the sample's own generator, as ``world`` makes it)."""
    draws = sorted(float(stream_rng(SEED, stream, i).random()) for i in range(n))
    bound = draws[k - 1] if k else -1.0

    def pick(rng):
        return tag if float(rng.random()) <= bound else otherwise
    return pick


def make_study(*, plus_tag=None, minus_tag=None, null_tag=None, plus_gen=None, minus_gen=None, null_gen=None,
               components=None, det=False, samples=40, fn=behave, control=True):
    ok = "okc" if components else "ok"  # a criterion with components returns a dict where it is defined
    plus_tag, minus_tag = plus_tag or ok, minus_tag or ok
    worlds = {
        "plus": World(plus_gen or world(5.0, plus_tag)),
        "minus": World(minus_gen or world(0.0, minus_tag), derived_from="plus", change="x 5 -> 0"),
    }
    if null_tag is not None or null_gen is not None:
        worlds["null"] = World(null_gen or world(0.0, null_tag), derived_from="plus", change="no effect")
    controls = [Control("negate", ["C"], transform=lambda d, rng: {"x": -d["x"], "tag": d["tag"]})] if control else []
    return Study(name="spec07", criteria=[Criterion("C", fn, components=components)], worlds=worlds, controls=controls,
                 deterministic=det, budget=Budget(samples=samples))


def run(study, quick=False):
    """``{component id: record}`` of one evaluation (no guard, one pass)."""
    return {c["id"]: c for c in checks.evaluate(study, quick)["components"]}


def counts(comp, stream):
    c = comp["counts"][stream]
    return c["holds"], c["undefined"], c["hard_undefined"], c["n"]


MODES = (("stochastic", False), ("deterministic", True))


class Assertions:
    def assertAbstention(self, comp, stream, n):
        """The stream is all soft UNDEFINED: abstentions, no failure."""
        self.assertEqual(counts(comp, stream), (0, n, 0, n))
        self.assertEqual(comp["errors"].get(stream, {}), {})
        self.assertNotIn("K1_UNDEFINED", comp["flags"])

    def assertFailure(self, comp, stream, n, causes):
        """The stream is all hard UNDEFINED, with the given cause counts; K1 makes the component UNDEFINED."""
        self.assertEqual(counts(comp, stream), (0, n, n, n))
        self.assertEqual(comp["errors"][stream], causes)
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "UNDEFINED")
        self.assertFalse([f for f in comp["flags"] if f.startswith("K1_ABSTAINED")])


class Spec07Case(Assertions, unittest.TestCase):
    pass


# --------------------------------------------------------------------------
# Section 1: the classification, one test per row, in both modes
# --------------------------------------------------------------------------

class TestClassificationOfPythonCriteria(Spec07Case):
    """Rows of section 1 for a Python criterion, observed on the ``minus`` stream (a K1 stream) in both modes."""

    def case(self, det, **kw):
        study = make_study(det=det, **kw)
        comps = run(study)
        n = 1 if det else study.budget.samples
        return comps, n

    def soft_on_minus(self, tag, components=None, ids=("C",), clean=()):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, minus_tag=tag, components=components)
                for cid in ids:
                    comp = comps[cid]
                    self.assertAbstention(comp, "world:minus", n)
                    self.assertIn("K1_ABSTAINED:world:minus", comp["flags"])
                    self.assertIn("K1_ABSTAINED_MAJORITY:world:minus", comp["flags"])  # all of minus abstains
                    self.assertEqual(comp["verdict"], "WEAK")
                for cid in clean:
                    self.assertEqual(counts(comps[cid], "world:minus"), (0, 0, 0, n))
                    self.assertFalse([f for f in comps[cid]["flags"] if f.startswith("K1_")])
                    self.assertEqual(comps[cid]["verdict"], "FALSIFIABLE")

    def hard_on_minus(self, tag, causes, components=None, ids=("C",), soft=()):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, minus_tag=tag, components=components)
                for cid in ids:
                    self.assertFailure(comps[cid], "world:minus", n, {c: n for c in causes})
                for cid in soft:
                    self.assertAbstention(comps[cid], "world:minus", n)

    # soft rows

    def test_none_is_soft(self):
        self.soft_on_minus("none")

    def test_a_whole_none_return_with_components_is_soft_for_every_component(self):
        self.soft_on_minus("cnone", components=["a", "b"], ids=("C:a", "C:b"))

    def test_a_none_dict_value_is_soft_for_that_component_only(self):
        self.soft_on_minus("cdict", components=["a", "b"], ids=("C:a",), clean=("C:b",))

    # hard rows

    def test_a_missing_declared_component_is_hard_for_that_component_only(self):
        self.hard_on_minus("cmissing", ["MISSING_COMPONENT"], components=["a", "b"], ids=("C:b",))
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, minus_tag="cmissing", components=["a", "b"])
                self.assertEqual(counts(comps["C:a"], "world:minus"), (0, 0, 0, n))  # a is FALSIFIABLE-neutral: FAILS
                self.assertFalse([f for f in comps["C:a"]["flags"] if f.startswith("K1_")])

    def test_a_missing_component_is_a_mismatch_but_not_a_bad_return(self):
        comps, _ = self.case(False, minus_tag="cmissing", components=["a", "b"])
        self.assertNotIn("BAD_RETURN", comps["C:b"]["flags"])
        result = checks.evaluate(make_study(minus_tag="cmissing", components=["a", "b"]), False)
        self.assertIn("K7_COMPONENT_MISMATCH", result["study_flags"])

    def test_nan_is_a_bad_return_and_hard(self):
        self.hard_on_minus("nan", ["BAD_RETURN"])

    def test_a_number_is_a_bad_return_and_hard(self):
        self.hard_on_minus("one", ["BAD_RETURN"])

    def test_a_string_is_a_bad_return_and_hard(self):
        self.hard_on_minus("str", ["BAD_RETURN"])

    def test_an_array_is_a_bad_return_and_hard(self):
        self.hard_on_minus("array", ["BAD_RETURN"])

    def test_a_bad_return_carries_the_information_flag(self):
        for tag in ("nan", "one", "str", "array"):
            comps, _ = self.case(False, minus_tag=tag)
            self.assertIn("BAD_RETURN", comps["C"]["flags"], tag)

    def test_a_non_dict_return_of_a_criterion_with_components_is_hard_for_every_component(self):
        self.hard_on_minus("cnondict", ["BAD_RETURN"], components=["a", "b"], ids=("C:a", "C:b"))

    def test_a_wrong_type_inside_the_dict_is_hard_for_that_component_only(self):
        self.hard_on_minus("cnan", ["BAD_RETURN"], components=["a", "b"], ids=("C:a",))

    def test_an_exception_in_fn_is_hard(self):
        self.hard_on_minus("raise", ["ValueError"])

    def test_a_failed_generate_on_minus_is_hard(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, minus_gen=raising)
                self.assertFailure(comps["C"], "world:minus", n, {"RuntimeError": n})

    def test_an_invalid_generate_output_on_minus_is_hard(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, minus_gen=not_a_dict)
                self.assertFailure(comps["C"], "world:minus", n, {"TypeError": n})

    def test_a_failed_generate_on_null_is_hard(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, null_gen=raising)
                self.assertFailure(comps["C"], "world:null", n, {"RuntimeError": n})

    def test_a_failed_generate_on_plus_is_hard_for_plus(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, plus_gen=raising)
                self.assertFailure(comps["C"], "world:plus", n, {"RuntimeError": n})

    # the other K1 streams

    def test_a_soft_row_on_plus_and_null(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, null_tag="none")
                self.assertAbstention(comps["C"], "world:null", n)
                self.assertIn("K1_ABSTAINED_MAJORITY:world:null", comps["C"]["flags"])
                comps, n = self.case(det, plus_tag="none")
                self.assertEqual(counts(comps["C"], "world:plus"), (0, n, 0, n))  # soft: all abstentions
                self.assertIn("K1_UNDEFINED", comps["C"]["flags"])  # but more than half of plus: the plus rule

    def test_a_hard_row_on_plus_and_null(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.case(det, null_tag="raise")
                self.assertFailure(comps["C"], "world:null", n, {"ValueError": n})
                comps, n = self.case(det, plus_tag="raise")
                self.assertFailure(comps["C"], "world:plus", n, {"ValueError": n})

    def test_the_error_counts_of_a_k1_stream_add_up_to_hard_undefined(self):
        for tag in ("raise", "nan", "str", "none"):
            comps, n = self.case(False, minus_tag=tag)
            comp = comps["C"]
            self.assertEqual(sum(comp["errors"].get("world:minus", {}).values()),
                             comp["counts"]["world:minus"]["hard_undefined"], tag)

    def test_the_leak_guard_error_is_hard(self):
        # tests/test_guard.py: the blocked open raises a PermissionError in the criterion, on every plus sample
        comp = _helpers.component("toy_leak_open")
        c = comp["counts"]["world:plus"]
        self.assertEqual(comp["errors"]["world:plus"], {"PermissionError": c["n"]})
        self.assertEqual(c["hard_undefined"], c["undefined"])
        self.assertEqual(c["undefined"], c["n"])
        self.assertEqual(comp["verdict"], "UNDEFINED")


class TestClassificationOfPatterns(Spec07Case):
    """Pattern rows: an empty selection, a non-finite value and types that do not fit are soft; a missing key is hard."""

    PATTERN = {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 2.0}

    def study(self, minus_data, det):
        pattern = Pattern(self.PATTERN)
        plus = lambda rng: {"x": np.full(20, 5.0)}  # noqa: E731
        minus_world = lambda rng: minus_data()  # noqa: E731
        return Study(
            name="spec07_pattern", criteria=[Criterion("C", pattern.fn)],
            worlds={"plus": World(plus), "minus": World(minus_world, derived_from="plus", change="x 5 -> 0")},
            controls=[Control("negate", ["C"], transform=lambda d, rng: {"x": -d["x"]})],
            deterministic=det, budget=Budget(samples=40),
        )

    def test_empty_selection_non_finite_and_wrong_types_are_soft(self):
        cases = {
            "empty selection": lambda: {"x": np.array([])},
            "non-finite value": lambda: {"x": np.array([np.nan, 1.0])},
            "types do not fit": lambda: {"x": np.array(["a", "b"])},
        }
        for label, minus_data in cases.items():
            for name, det in MODES:
                with self.subTest(case=label, mode=name):
                    comp = run(self.study(minus_data, det))["C"]
                    n = 1 if det else 40
                    self.assertAbstention(comp, "world:minus", n)
                    self.assertIn("K1_ABSTAINED:world:minus", comp["flags"])

    def test_a_missing_key_is_hard(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comp = run(self.study(lambda: {"y": np.array([1.0])}, det))["C"]
                self.assertFailure(comp, "world:minus", 1 if det else 40, {"KeyError": 1 if det else 40})

    def test_a_zero_denominator_is_soft(self):
        ratio = Pattern({"pattern": "ratio_band", "a": "a", "b": "b", "stat": "mean", "lo": 0.5, "hi": 2.0})
        for name, det in MODES:
            with self.subTest(mode=name):
                study = Study(
                    name="spec07_ratio", criteria=[Criterion("C", ratio.fn)],
                    worlds={
                        "plus": World(lambda rng: {"a": np.full(5, 1.0), "b": np.full(5, 1.0)}),
                        "minus": World(lambda rng: {"a": np.full(5, 1.0), "b": np.zeros(5)}, derived_from="plus",
                                       change="b 1 -> 0"),
                    },
                    controls=[Control("negate", ["C"], transform=lambda d, rng: {"a": d["a"], "b": d["b"] * 9.0})],
                    deterministic=det, budget=Budget(samples=40),
                )
                comp = run(study)["C"]
                self.assertAbstention(comp, "world:minus", 1 if det else 40)


# --------------------------------------------------------------------------
# Section 1: command criteria
# --------------------------------------------------------------------------

FAKE07 = r'''
import json
import os
import sys
import time

mode = sys.argv[1]


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    msg = json.loads(line)
    op = msg["op"]
    if op == "hello":
        send({"ok": True, "tg": "tg-line/1", "rid": msg["rid"]})
        continue
    if op == "bye":
        break
    rid = msg["rid"]
    xs = msg["data"]["x"]
    low = sum(xs) / len(xs) < 1.0  # the minus world (x = 0), the zeros probe, the control and noise
    if not low:
        send({"rid": rid, "outcome": {"a": "HOLDS", "b": "HOLDS"} if mode == "cdict" else "HOLDS"})
    elif mode == "undefined":
        send({"rid": rid, "outcome": "UNDEFINED"})
    elif mode == "error":
        send({"rid": rid, "error": "boom"})
    elif mode == "invalid":
        send({"rid": rid, "outcome": "MAYBE"})
    elif mode == "hang":
        time.sleep(30)
    elif mode == "die":
        os._exit(2)
    elif mode == "cdict":  # a is UNDEFINED, b is missing
        send({"rid": rid, "outcome": {"a": "UNDEFINED"}})
    else:
        raise SystemExit("unknown mode " + mode)
'''

CONSTANT_WORLDS = '''
import numpy as np


def plus(rng):
    return {"x": np.full(30, 2.0)}


def minus(rng):
    return {"x": np.full(30, 0.0)}
'''


class TestClassificationOfCommandCriteria(Assertions, ExternalBase):
    """Command rows: ``UNDEFINED`` is soft; an error answer, an invalid outcome string, a timeout and a death are hard;
    a command with components can have one component UNDEFINED (soft) and one missing (hard)."""

    def setUp(self):
        super().setUp()
        self.write("fake07.py", FAKE07)
        self.write("w07.py", CONSTANT_WORLDS)

    def certificate(self, mode, det, components=None, timeout=None):
        argv = [sys.executable, "fake07.py", mode]
        d = self.study(argv, {"uses": ["fake07.py"], **({"request_timeout_s": timeout} if timeout else {})})
        d["worlds"] = {"plus": {"python": "w07.py:plus"}, "minus": {"python": "w07.py:minus", "change": "x 2 -> 0"}}
        d["budget"] = {"samples": 12}
        if det:
            d["study"]["deterministic"] = True
        if components:
            d["criteria"][0]["components"] = components
        code, out, err, cert = self.check(d)
        self.assertIsNotNone(cert, out + err)
        self.assertEqual(certificate.validate_envelope(cert), [])
        return {c["id"]: c for c in cert["body"]["components"]}, 1 if det else 12

    def test_a_command_that_answers_undefined_is_soft(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.certificate("undefined", det)
                comp = comps["C"]
                self.assertAbstention(comp, "world:minus", n)
                self.assertIn("K1_ABSTAINED:world:minus", comp["flags"])
                self.assertEqual(comp["verdict"], "WEAK")

    def test_an_error_answer_is_hard(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.certificate("error", det)
                self.assertFailure(comps["C"], "world:minus", n, {"ExternalError": n})

    def test_an_invalid_outcome_string_is_hard_and_a_bad_return(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.certificate("invalid", det)
                self.assertFailure(comps["C"], "world:minus", n, {"BAD_RETURN": n})
                self.assertIn("BAD_RETURN", comps["C"]["flags"])

    def test_a_timeout_is_hard_and_so_is_every_later_request(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.certificate("hang", det, timeout=1)
                comp = comps["C"]
                self.assertEqual(comp["counts"]["world:minus"]["hard_undefined"], n)
                self.assertEqual(comp["counts"]["world:minus"]["undefined"], n)
                self.assertIn("K1_UNDEFINED", comp["flags"])
                self.assertEqual(comp["errors"]["world:minus"]["ExternalTimeout"], 1)

    def test_a_death_is_hard_and_so_is_every_later_request(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.certificate("die", det)
                comp = comps["C"]
                self.assertEqual(comp["counts"]["world:minus"]["hard_undefined"], n)
                self.assertEqual(sum(comp["errors"]["world:minus"].values()), n)
                self.assertTrue(set(comp["errors"]["world:minus"]) <= {"ExternalDied"})
                self.assertEqual(comp["verdict"], "UNDEFINED")

    def test_a_command_with_components_one_undefined_and_one_missing(self):
        for name, det in MODES:
            with self.subTest(mode=name):
                comps, n = self.certificate("cdict", det, components=["a", "b"])
                self.assertAbstention(comps["C:a"], "world:minus", n)  # UNDEFINED: soft
                self.assertIn("K1_ABSTAINED:world:minus", comps["C:a"]["flags"])
                self.assertFailure(comps["C:b"], "world:minus", n, {"MISSING_COMPONENT": n})  # missing: hard


# --------------------------------------------------------------------------
# Section 2.1: K1 in integers
# --------------------------------------------------------------------------

class TestK1Boundaries(Spec07Case):
    def abstaining(self, stream, k, n, tag="none", **kw):
        pick = abstaining_on(stream, n, k, tag=tag)
        key = {"world:plus": "plus_gen", "world:minus": "minus_gen", "world:null": "null_gen"}[stream]
        x = {"world:plus": 5.0, "world:minus": 0.0, "world:null": 0.0}[stream]
        return make_study(samples=200, **{key: world(x, pick)}, **kw)

    def test_full_mode_100_of_200_abstentions_on_plus_is_not_k1(self):
        comp = run(self.abstaining("world:plus", 100, 200))["C"]
        self.assertEqual(counts(comp, "world:plus"), (100, 100, 0, 200))
        self.assertNotIn("K1_UNDEFINED", comp["flags"])
        self.assertIn("K1_ABSTAINED:world:plus", comp["flags"])
        self.assertNotEqual(comp["verdict"], "UNDEFINED")

    def test_full_mode_101_of_200_abstentions_on_plus_is_k1(self):
        comp = run(self.abstaining("world:plus", 101, 200))["C"]
        self.assertEqual(counts(comp, "world:plus"), (99, 101, 0, 200))
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "UNDEFINED")
        self.assertFalse([f for f in comp["flags"] if f.startswith("K1_ABSTAINED")])

    def test_quick_mode_10_of_20_is_not_k1_and_11_is(self):
        for k, expected in ((10, False), (11, True)):
            comp = run(self.abstaining("world:plus", k, 20), quick=True)["C"]
            self.assertEqual(comp["counts"]["world:plus"]["n"], 20)
            self.assertEqual(comp["counts"]["world:plus"]["undefined"], k)
            self.assertEqual("K1_UNDEFINED" in comp["flags"], expected, k)
            self.assertEqual(comp["verdict"] == "UNDEFINED", expected, k)

    def test_one_hard_undefined_on_minus_is_k1(self):
        study = self.abstaining("world:minus", 1, 200, tag="raise")
        comp = run(study)["C"]
        self.assertEqual(counts(comp, "world:minus"), (0, 1, 1, 200))
        self.assertEqual(comp["errors"]["world:minus"], {"ValueError": 1})
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "UNDEFINED")

    def test_one_hard_undefined_on_plus_or_null_is_k1(self):
        for stream in ("world:plus", "world:null"):
            kw = {"null_tag": "ok"} if stream == "world:plus" else {}
            comp = run(self.abstaining(stream, 1, 200, tag="raise", **kw))["C"]
            self.assertEqual(comp["counts"][stream]["hard_undefined"], 1, stream)
            self.assertEqual(comp["verdict"], "UNDEFINED", stream)

    def test_one_abstention_on_minus_is_information_only(self):
        comp = run(self.abstaining("world:minus", 1, 200))["C"]
        self.assertEqual(counts(comp, "world:minus"), (0, 1, 0, 200))
        self.assertIn("K1_ABSTAINED:world:minus", comp["flags"])
        self.assertNotIn("K1_ABSTAINED_MAJORITY:world:minus", comp["flags"])
        self.assertNotIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "FALSIFIABLE")  # information flags never enter the verdict

    def test_majority_boundary_on_minus(self):
        at = run(self.abstaining("world:minus", 100, 200))["C"]  # 2 * a = n: absent
        self.assertIn("K1_ABSTAINED:world:minus", at["flags"])
        self.assertNotIn("K1_ABSTAINED_MAJORITY:world:minus", at["flags"])
        self.assertEqual(at["verdict"], "FALSIFIABLE")
        over = run(self.abstaining("world:minus", 101, 200))["C"]  # one more: present, capping
        self.assertIn("K1_ABSTAINED_MAJORITY:world:minus", over["flags"])
        self.assertEqual(over["verdict"], "WEAK")
        self.assertNotIn("K1_UNDEFINED", over["flags"])

    def test_majority_boundary_on_null(self):
        at = run(self.abstaining("world:null", 100, 200, null_tag="ok"))["C"]
        over = run(self.abstaining("world:null", 101, 200, null_tag="ok"))["C"]
        self.assertIn("K1_ABSTAINED:world:null", at["flags"])
        self.assertNotIn("K1_ABSTAINED_MAJORITY:world:null", at["flags"])
        self.assertIn("K1_ABSTAINED_MAJORITY:world:null", over["flags"])
        self.assertEqual(over["verdict"], "WEAK")

    def test_the_majority_flag_is_never_for_plus(self):
        comp = run(self.abstaining("world:plus", 100, 200))["C"]
        self.assertFalse([f for f in comp["flags"] if f.startswith("K1_ABSTAINED_MAJORITY")])

    def test_the_majority_flag_is_never_suppressed(self):
        # plus never holds (all FAILS): the cascade suppression of 0.2 runs, and must leave the capping flag alone
        study = make_study(plus_gen=world(0.0, "ok"), minus_gen=world(0.0, "none"))
        comp = run(study)["C"]
        self.assertIn("K2_HOLDS_UNREACHABLE", comp["flags"])
        self.assertIn("K1_ABSTAINED_MAJORITY:world:minus", comp["flags"])
        self.assertNotIn("K1_ABSTAINED_MAJORITY:world:minus", comp.get("suppressed", []))
        self.assertEqual(comp["verdict"], "NOT_FALSIFIABLE")

    def test_the_deterministic_rule_is_the_same_on_one_sample(self):
        study = make_study(det=True, minus_tag="none", null_tag="none")
        comp = run(study)["C"]
        self.assertEqual(counts(comp, "world:minus"), (0, 1, 0, 1))
        for stream in ("world:minus", "world:null"):
            self.assertIn(f"K1_ABSTAINED:{stream}", comp["flags"])
            self.assertIn(f"K1_ABSTAINED_MAJORITY:{stream}", comp["flags"])
        self.assertEqual(comp["verdict"], "WEAK")
        self.assertEqual(run(make_study(det=True, plus_tag="none"))["C"]["verdict"], "UNDEFINED")

    def test_a_hard_undefined_with_abstentions_elsewhere_is_k1_and_has_no_information_flags(self):
        study = make_study(plus_gen=world(5.0, abstaining_on("world:plus", 40, 5)), minus_tag="raise")
        comp = run(study)["C"]
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertFalse([f for f in comp["flags"] if f.startswith("K1_ABSTAINED")])

    def test_information_flags_never_enter_a_verdict_a_suppression_or_the_cascade(self):
        for flag in ("K1_ABSTAINED:world:plus", "K1_ABSTAINED:world:minus", "K1_ABSTAINED:world:null"):
            self.assertEqual(checks.component_verdict({flag}), "FALSIFIABLE")
            self.assertFalse(checks.is_mandatory(flag) or checks.is_capping(flag))
            self.assertEqual(checks.component_verdict({flag, "K2_LOW_POWER"}), "WEAK")
            self.assertEqual(checks.component_verdict({flag, "K2_NO_SEPARATION"}), "NOT_FALSIFIABLE")
            self.assertNotIn(flag, checks.SUPPRESSIBLE_FLAGS)
            self.assertFalse(flag in minus.SUPPRESSIBLE_WHEN_IDENTICAL)
        stats = checks.StreamStats(0, 0, 10)
        kept, suppressed = checks.apply_cascade_suppression({"K1_ABSTAINED:world:minus", "K2_NO_SEPARATION"}, stats, False)
        self.assertEqual((kept, suppressed), ({"K1_ABSTAINED:world:minus"}, ["K2_NO_SEPARATION"]))

    def test_the_prefix_registries(self):
        self.assertIn("K1_ABSTAINED:", checks.INFORMATIONAL_PREFIXES)
        self.assertIn("K1_ABSTAINED_MAJORITY:", checks.CAPPING_PREFIXES)
        for stream in ("world:minus", "world:null"):
            flag = f"K1_ABSTAINED_MAJORITY:{stream}"
            self.assertTrue(checks.is_capping(flag))
            self.assertFalse(checks.is_mandatory(flag))
            self.assertEqual(checks.component_verdict({flag}), "WEAK")
            self.assertEqual(checks.component_verdict({flag, "K2_LOW_POWER"}), "WEAK")
            self.assertEqual(checks.component_verdict({flag, "K2_MINUS_IDENTICAL"}), "UNTESTED")
            self.assertEqual(checks.component_verdict({flag, "K1_UNDEFINED"}), "UNDEFINED")
            self.assertEqual(checks.component_verdict({flag, "K2_NO_SEPARATION"}), "NOT_FALSIFIABLE")
            kept, suppressed = checks.apply_cascade_suppression({flag, "K2_NO_SEPARATION"}, checks.StreamStats(0, 0, 10), False)
            self.assertIn(flag, kept)
            self.assertNotIn(flag, suppressed)


# --------------------------------------------------------------------------
# Section 2.2: K8 keeps its own rule
# --------------------------------------------------------------------------

K8_WORLDS = '''
import numpy as np


def plus(rng):  # first-ten mean above 1 about nine times in ten; 40% of the samples abstain
    x = rng.normal(1.4, 1.0, 40)
    u = rng.random()
    return {"x": x, "tag": np.array(["none" if u < 0.4 else "ok"])}


def minus(rng):
    x = rng.normal(0.0, 1.0, 40)
    u = rng.random()
    return {"x": x, "tag": np.array(["none" if u < 0.4 else "ok"])}


def first_ten(d):
    if d["tag"][0] == "none":
        return None
    return bool(np.mean(d["x"][:10]) > 1.0)


def plus_det(rng):
    return {"x": np.full(40, 2.0), "tag": np.array(["ok"])}


def minus_det(rng):
    return {"x": np.full(40, 2.0), "tag": np.array(["none"])}


def mean_large(d):
    if d["tag"][0] == "none":
        return None
    return bool(np.mean(d["x"]) > 1.0)
'''


class TestK8WithAbstentions(K8Case):
    def setUp(self):
        super().setUp()
        self.write("w07.py", K8_WORLDS)

    def abstaining_samples(self, stream, mean):
        out = 0
        for i in range(200):
            rng = stream_rng(SEED, stream, i)
            rng.normal(mean, 1.0, 40)
            out += int(rng.random() < 0.4)
        return out

    def test_forty_percent_abstention_on_the_before_side_is_left_out_of_the_change_count(self):
        d = self.base(criteria=[{"id": "C", "python": "w07.py:first_ten"}])
        d["worlds"]["plus"] = {"python": "w07.py:plus"}
        d["worlds"]["minus"] = {"python": "w07.py:minus", "change": "mean 1.4 -> 0"}
        body = self.run_body(d)
        comp = self.comp(body)
        plus_abstained = self.abstaining_samples("world:plus", 1.4)
        minus_abstained = self.abstaining_samples("world:minus", 0.0)
        rec_plus = body["k8"][BUILTIN_ID]["C"]["plus"]
        rec_minus = body["k8"][BUILTIN_ID]["C"]["minus"]
        # the recorded behaviour of 0.4 is kept: a pair with an UNDEFINED side is counted apart and not as a change
        self.assertEqual((rec_plus["pairs"], rec_plus["undefined"]), (200, plus_abstained))
        self.assertEqual(rec_plus["defined"], 200 - plus_abstained)
        self.assertEqual((rec_minus["pairs"], rec_minus["undefined"]), (200, minus_abstained))
        self.assertTrue(0.3 * 200 < plus_abstained <= 0.5 * 200, plus_abstained)  # about 40%, not above one half
        self.assertGreater(rec_plus["changes"], 0)  # changes on the rest of the pairs
        self.assertLessEqual(rec_plus["changes"], rec_plus["defined"])
        # 40% is below the K8_INCONCLUSIVE rule (more than 50%), so nothing caps the verdict through K8
        self.assertNotIn("K8_INCONCLUSIVE", comp["flags"])
        self.assertIn("K8_NOT_INVARIANT", comp["flags"])
        # K1: abstentions on at most half of plus are information, not a failure
        self.assertIn("K1_ABSTAINED:world:plus", comp["flags"])
        self.assertNotIn("K1_UNDEFINED", comp["flags"])

    def test_deterministic_minus_abstention_with_an_invariance_declared_is_k8_inconclusive(self):
        d = self.base(criteria=[{"id": "C", "python": "w07.py:mean_large"}], invariances=[
            {"id": "order", "criteria": ["C"], "reason": "the rows are exchangeable",
             "mutations": [{"op": "permute_rows"}]}])
        d["study"]["deterministic"] = True
        d["worlds"]["plus"] = {"python": "w07.py:plus_det"}
        d["worlds"]["minus"] = {"python": "w07.py:minus_det", "change": "abstains"}
        body = self.run_body(d)
        comp = self.comp(body)
        self.assertEqual(counts(comp, "world:minus"), (0, 1, 0, 1))
        for flag in ("K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus", "K8_INCONCLUSIVE"):
            self.assertIn(flag, comp["flags"])
        self.assertNotIn("K1_UNDEFINED", comp["flags"])
        rec = body["k8"]["order"]["C"]["minus"]
        self.assertEqual(rec["undefined"], rec["pairs"])  # every pair of the minus world is undefined
        self.assertEqual(comp["verdict"], "WEAK")


# --------------------------------------------------------------------------
# Identical minus with abstentions
# --------------------------------------------------------------------------

class TestIdenticalMinusWithAbstentions(Spec07Case):
    def study(self):
        def same(rng):  # ignores its declared change: the same data as plus under the same generator
            tag = "none" if float(rng.random()) <= 0.1 else "ok"
            return {"x": np.full(20, 5.0), "tag": np.array([tag])}
        return make_study(plus_gen=same, minus_gen=same)

    def test_is_untested_not_undefined(self):
        comp = run(self.study())["C"]
        self.assertEqual(comp["minus_check"]["identical"], True)
        self.assertIn("K2_MINUS_IDENTICAL", comp["flags"])
        self.assertIn("K1_ABSTAINED:world:minus", comp["flags"])
        self.assertNotIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "UNTESTED")

    def test_the_identical_minus_analysis_calls_are_not_counted(self):
        comp = run(self.study())["C"]
        self.assertEqual(comp["counts"]["world:minus"]["n"], 40)
        self.assertEqual(comp["counts"]["world:plus"]["n"], 40)


# --------------------------------------------------------------------------
# Section 4: the compatibility statement, on hand-built studies
# --------------------------------------------------------------------------

class TestSection4Compatibility(Spec07Case):
    """Between 0.4.1 and 0.5.0: only components that 0.4.1 made UNDEFINED change.  The expected sets are written out from
    section 4 (the 0.4.1 flags are the flags below without the ``K1_ABSTAINED*`` ones, plus ``K1_UNDEFINED`` where 0.4.1
    gave it)."""

    def test_item_1_a_component_without_an_undefined_outcome_is_unchanged(self):
        comp = run(make_study())["C"]
        self.assertEqual(comp["flags"], [])
        self.assertEqual(comp["verdict"], "FALSIFIABLE")
        for stream, c in comp["counts"].items():
            self.assertEqual(c["undefined"], 0, stream)
            self.assertEqual(c["hard_undefined"], 0, stream)

    def test_item_2_hard_undefined_only_keeps_the_0_4_1_result(self):
        comp = run(make_study(minus_gen=world(0.0, abstaining_on("world:minus", 40, 3, tag="raise"))))["C"]
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertFalse([f for f in comp["flags"] if f.startswith("K1_ABSTAINED")])
        self.assertEqual(comp["verdict"], "UNDEFINED")
        self.assertEqual(counts(comp, "world:minus"), (0, 3, 3, 40))

    def test_item_2_a_plus_majority_keeps_the_0_4_1_result(self):
        comp = run(make_study(plus_gen=world(5.0, abstaining_on("world:plus", 40, 21))))["C"]
        self.assertEqual(counts(comp, "world:plus"), (19, 21, 0, 40))
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertFalse([f for f in comp["flags"] if f.startswith("K1_ABSTAINED")])
        self.assertEqual(comp["verdict"], "UNDEFINED")

    def test_item_3_soft_only_has_the_0_4_1_flags_without_k1_undefined_and_the_same_counts_and_bounds(self):
        soft = run(make_study(plus_gen=world(5.0, abstaining_on("world:plus", 40, 4)),
                              minus_gen=world(0.0, abstaining_on("world:minus", 40, 12))))["C"]
        twin = run(make_study(plus_gen=world(5.0, abstaining_on("world:plus", 40, 4, tag="false")),
                              minus_gen=world(0.0, abstaining_on("world:minus", 40, 12, tag="false"))))["C"]
        self.assertEqual(soft["flags"], ["K1_ABSTAINED:world:minus", "K1_ABSTAINED:world:plus"])
        self.assertEqual(soft["verdict"], "FALSIFIABLE")  # the 0.4.1 cascade for the other flags (none)
        self.assertEqual(counts(soft, "world:plus"), (36, 4, 0, 40))
        self.assertEqual(counts(soft, "world:minus"), (0, 12, 0, 40))
        # None = False for every HOLDS-based number: the twin has the same holds, n and bounds
        self.assertEqual(soft["bounds"], twin["bounds"])
        for stream, c in soft["counts"].items():
            self.assertEqual((c["holds"], c["n"]), (twin["counts"][stream]["holds"], twin["counts"][stream]["n"]), stream)

    def test_item_3_a_soft_majority_on_minus_adds_the_capping_flag(self):
        comp = run(make_study(minus_gen=world(0.0, abstaining_on("world:minus", 40, 21))))["C"]
        self.assertEqual(comp["flags"], ["K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus"])
        self.assertEqual(comp["verdict"], "WEAK")
        self.assertEqual(counts(comp, "world:minus"), (0, 21, 0, 40))

    def test_item_3_the_other_flags_are_those_of_0_4_1_and_the_cascade_gives_the_verdict(self):
        # plus never holds: 0.4.1 computed K2_HOLDS_UNREACHABLE under K1_UNDEFINED; now it decides the verdict
        comp = run(make_study(plus_gen=world(0.0, abstaining_on("world:plus", 40, 4)), minus_tag="ok"))["C"]
        self.assertIn("K2_HOLDS_UNREACHABLE", comp["flags"])
        self.assertIn("K1_ABSTAINED:world:plus", comp["flags"])
        self.assertEqual(comp["verdict"], "NOT_FALSIFIABLE")

    def test_item_4_the_study_verdict_follows_from_the_component_verdicts(self):
        study = make_study(minus_gen=world(0.0, abstaining_on("world:minus", 40, 21)))
        result = checks.evaluate(study, False)
        verdicts = [c["verdict"] for c in result["components"]]
        self.assertEqual(checks.study_verdict(verdicts, result["study_flags"]), "WEAK")


# --------------------------------------------------------------------------
# Section 2.4: certificate fields and validation
# --------------------------------------------------------------------------

LIMITATION_1 = (
    "A criterion's own UNDEFINED outcomes (None, a pattern's UNDEFINED, a command's UNDEFINED) on plus, minus and null "
    "count as no claim; K1 makes the verdict UNDEFINED only for failures (exceptions, failed generation, wrong return "
    "types, missing components, command errors) or when the criterion abstains on more than half of the plus samples."
)
LIMITATION_2 = (
    "K8 leaves pairs with an UNDEFINED side out of its change count; abstentions can therefore hide changes on up to "
    "half of the pairs."
)


class TestCertificate(Spec07Case):
    @classmethod
    def setUpClass(cls):
        cls.envelope = certificate.run_gate(os.path.join(SPEC07_FIXTURES, "abs_minus.py"))
        cls.body = cls.envelope["body"]

    def test_versions(self):
        self.assertEqual(self.body["tool_version"], "0.5.0")
        self.assertEqual(self.body["spec_version"], "0.7")
        self.assertEqual(certificate.TOOL_VERSION, "0.5.0")
        self.assertEqual(certificate.SPEC_VERSION, "0.7")

    def test_the_known_limitations_carry_the_two_sentences_verbatim(self):
        limits = self.body["known_limitations"]
        self.assertIn(LIMITATION_1, limits)
        self.assertIn(LIMITATION_2, limits)
        self.assertEqual(len(limits), 7)

    def test_every_stream_has_hard_undefined_within_undefined(self):
        for comp in self.body["components"]:
            for stream, c in comp["counts"].items():
                self.assertEqual(set(c), {"holds", "undefined", "hard_undefined", "n"}, stream)
                self.assertLessEqual(c["holds"] + c["undefined"], c["n"], stream)
                self.assertLessEqual(c["hard_undefined"], c["undefined"], stream)

    def test_the_fixture_abstains_without_failing(self):
        comp = self.body["components"][0]
        minus = comp["counts"]["world:minus"]
        self.assertGreater(minus["undefined"], 0)
        self.assertEqual(minus["hard_undefined"], 0)

    def test_the_certificate_validates(self):
        self.assertEqual(certificate.validate_envelope(self.envelope), [])

    def rehash(self, mutate):
        env = copy.deepcopy(self.envelope)
        mutate(env["body"]["components"][0]["counts"]["world:minus"])
        env["body_sha256"] = certificate.body_sha256(env["body"])
        return certificate.validate_envelope(env)

    def test_validation_checks_holds_plus_undefined_within_n(self):
        problems = self.rehash(lambda c: c.update(holds=c["n"], undefined=1))
        self.assertTrue(any("holds + undefined" in p for p in problems), problems)

    def test_validation_checks_hard_undefined_within_undefined(self):
        problems = self.rehash(lambda c: c.update(hard_undefined=c["undefined"] + 1))
        self.assertTrue(any("hard_undefined exceeds undefined" in p for p in problems), problems)

    def test_validation_requires_hard_undefined_from_spec_0_7_on(self):
        problems = self.rehash(lambda c: c.pop("hard_undefined"))
        self.assertTrue(any("hard_undefined is missing" in p for p in problems), problems)

    def test_validation_rejects_malformed_counts(self):
        problems = self.rehash(lambda c: c.update(n="many"))
        self.assertTrue(problems)

    def rehash_component(self, mutate, spec_version=None):
        env = copy.deepcopy(self.envelope)
        mutate(env["body"]["components"][0])
        if spec_version is not None:
            env["body"]["spec_version"] = spec_version
        env["body_sha256"] = certificate.body_sha256(env["body"])
        return certificate.validate_envelope(env)

    def test_a_spec_0_7_certificate_needs_a_counts_object_with_plus_and_minus(self):
        for label, mutate in (
            ("None", lambda comp: comp.update(counts=None)),
            ("a list", lambda comp: comp.update(counts=[])),
            ("empty", lambda comp: comp.update(counts={})),
            ("no minus", lambda comp: comp["counts"].pop("world:minus")),
            ("no plus", lambda comp: comp["counts"].pop("world:plus")),
            ("a stream that is not an object", lambda comp: comp["counts"].update({"world:minus": None})),
        ):
            with self.subTest(counts=label):
                problems = self.rehash_component(mutate)
                self.assertTrue(any("counts" in p for p in problems), problems)

    def test_the_two_worlds_are_named_in_the_problem(self):
        problems = self.rehash_component(lambda comp: comp.update(counts={}))
        self.assertTrue(any("'world:plus'" in p for p in problems), problems)
        self.assertTrue(any("'world:minus'" in p for p in problems), problems)

    def test_an_older_certificate_keeps_the_old_validation(self):
        for label, mutate in (("None", lambda comp: comp.update(counts=None)), ("a list", lambda comp: comp.update(counts=[])),
                              ("empty", lambda comp: comp.update(counts={})),
                              ("no minus", lambda comp: comp["counts"].pop("world:minus"))):
            with self.subTest(counts=label):
                self.assertEqual(self.rehash_component(mutate, spec_version="0.6"), [])

    def test_the_body_hash_rule_is_unchanged(self):
        self.assertEqual(self.envelope["body_sha256"], certificate.body_sha256(self.body))
        self.assertEqual(set(self.envelope), {"body", "body_sha256", "created_utc"})

    def test_the_cli_table_and_the_ci_summary_already_print_the_new_flags(self):
        flags = {"K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus"}
        body = copy.deepcopy(self.body)
        body["components"][0]["flags"] = sorted(flags)
        table = cli.format_table(body)
        summary = ci.render_summary(body, target="t", quick=False, certificate=None, sha=None, check_code=0,
                                    freeze_target=None, freeze_code=None, freeze_text="", reasons=[], exit_code=0)
        for flag in flags:
            self.assertIn(flag, table)
            self.assertIn(flag, summary)

    def test_a_version_0_4_certificate_is_not_verified(self):
        env = copy.deepcopy(self.envelope)
        env["body"]["tool_version"] = "0.4.1"
        env["body_sha256"] = certificate.body_sha256(env["body"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "old.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(env, handle)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cli.main(["verify", path, os.path.join(SPEC07_FIXTURES, "abs_minus.py")])
        self.assertEqual(code, 7)
        self.assertIn("v0.4.1", out.getvalue() + err.getvalue())

    def test_the_cli_table_prints_the_flags_of_a_real_check(self):
        text = cli.format_table(self.body)
        self.assertIn("K1_ABSTAINED:world:minus", text)


# --------------------------------------------------------------------------
# Section 3: names
# --------------------------------------------------------------------------

class TestNames(unittest.TestCase):
    def test_the_study_error_text_names_truth_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.py")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("STUDY = 3\n")
            body = certificate.run_gate(path)["body"]
        self.assertEqual(body["load_error"], {"type": "StudyError", "message": "STUDY is not a truth_gate.Study"})
        self.assertEqual(body["verdict"], "UNDEFINED")

    def test_the_leak_guard_message_names_truth_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = os.path.join(tmp, "study.py")
            secret = os.path.join(tmp, "secret.txt")
            for path in (study, secret):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("x\n")
            with guard.armed(study):
                try:
                    open(secret)
                except PermissionError as exc:
                    message = str(exc)
                else:
                    self.fail("the open was not blocked")
                guard.take_log()
        self.assertEqual(message, "truth_gate leak guard blocked open")

    def test_the_default_certificate_name_is_unchanged(self):
        self.assertEqual(cli.default_out_path("dir/study.py"), "dir/study.kapi.json")


# --------------------------------------------------------------------------
# Section 2.5: explain and documentation
# --------------------------------------------------------------------------

class TestExplain(unittest.TestCase):
    def test_k1_abstained_is_information_only(self):
        for name in ("K1_ABSTAINED", "K1_ABSTAINED:world:minus", "k1_abstained:world:null"):
            text = explain.explain(name)
            self.assertIsNotNone(text, name)
            self.assertIn("information only", text.splitlines()[0], name)
            self.assertIn("no claim", text)
        self.assertTrue(explain.explain("K1_ABSTAINED:world:minus").startswith("K1_ABSTAINED:world:minus  ["))

    def test_k1_abstained_majority_is_capping(self):
        for name in ("K1_ABSTAINED_MAJORITY", "K1_ABSTAINED_MAJORITY:world:minus", "K1_ABSTAINED_MAJORITY:world:null"):
            text = explain.explain(name)
            self.assertIsNotNone(text, name)
            self.assertIn("capping", text.splitlines()[0], name)
            self.assertIn("WEAK", text)

    def test_the_two_families_do_not_shadow_each_other(self):
        self.assertEqual(explain.lookup("K1_ABSTAINED:world:minus"), "K1_ABSTAINED:")
        self.assertEqual(explain.lookup("K1_ABSTAINED_MAJORITY:world:minus"), "K1_ABSTAINED_MAJORITY:")

    def test_k1_undefined_explains_both_causes(self):
        text = explain.explain("K1_UNDEFINED")
        self.assertIn("flag, component verdict UNDEFINED", text.splitlines()[0])
        self.assertIn("hard_undefined > 0", text)  # cause 1: a failure
        self.assertIn("more than half of the plus samples", text)  # cause 2: the plus majority
        self.assertIn("exception", text)
        self.assertIn("K1_ABSTAINED", text)  # and says what is not a cause

    def test_the_cli_explain_command_knows_the_new_names(self):
        for name in ("K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:null", "K1_UNDEFINED"):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cli.main(["explain", name])
            self.assertEqual(code, 0, name)
            self.assertIn(name.upper().split(":")[0], out.getvalue().upper())


class TestDocumentation(unittest.TestCase):
    def rows(self):
        return {m.group(1): m.group(2) for m in __import__("re").finditer(r"(?m)^\| `([^`]+)` \| ([^|]+) \|", read("docs/GATE.md"))}

    def test_gate_md_flag_table_has_the_two_new_flags_with_their_classes(self):
        rows = self.rows()
        self.assertIn("info", rows["K1_ABSTAINED:<stream>"])
        self.assertIn("capping", rows["K1_ABSTAINED_MAJORITY:<stream>"])
        self.assertIn("K1", rows["K1_UNDEFINED"])

    def test_gate_md_describes_k1_the_soft_hard_distinction_and_the_guidance(self):
        text = read("docs/GATE.md")
        for needle in ("soft", "hard", "abstention", "Return `None` when the analysis has nothing to claim",
                       "Let a genuine", "hard_undefined", "more than half of the `plus` samples",
                       "command failures are hard UNDEFINED outcomes"):
            self.assertIn(needle, text, needle)

    def test_gate_md_states_the_user_visible_change_and_the_ci_effect(self):
        text = read("docs/GATE.md")
        self.assertIn("judged by its other flags", text)
        self.assertIn("may\ntherefore pass now", text.replace("\r\n", "\n"))
        self.assertIn("mandatory flag that 0.4 had already computed", text.replace("\r\n", "\n"))

    def test_gate_md_keeps_the_external_died_note_and_the_spec_version(self):
        text = read("docs/GATE.md")
        self.assertIn("`EXTERNAL_DIED`", text)
        self.assertIn('`"0.7"` in 0.5', text)

    def test_the_known_limitation_of_k8_is_in_the_documentation(self):
        text = " ".join(read("docs/GATE.md").split())
        self.assertIn("abstentions can hide changes on up to half of the pairs", text)

    def test_manifest_md_and_the_protocol_text_state_the_rule(self):
        text = read("docs/MANIFEST.md").replace("\r\n", "\n")
        for needle in ("soft", "hard", "must answer an uncaught exception with", "never with\n`\"UNDEFINED\"`",
                       "K1_ABSTAINED:<stream>"):
            self.assertIn(needle, text, needle)
        node = read("examples/node_criterion/README.md")
        self.assertIn("Answer an uncaught exception with `error`", node)

    def test_the_changelog_has_the_0_5_0_entry(self):
        text = read("CHANGELOG.md").replace("\r\n", "\n")
        self.assertIn("## 0.5.0 (spec 0.7", text)
        section = text.split("## 0.5.0", 1)[1].split("\n## ", 1)[0]
        for needle in ("K1_ABSTAINED_MAJORITY", "hard_undefined", "may\nnow pass", "evaluation/cases/E2/E2-07_faulty.py",
                       "UNDEFINED to WEAK", "R-2", "exits 7"):
            self.assertIn(needle, section, needle)

    def test_no_evaluation_result_enters_the_documents_the_phase_c_agents_read(self):
        for path in ("docs/GATE.md", "docs/MANIFEST.md", "docs/SPEC.md"):
            text = read(path)
            for forbidden in ("Phase B", "Phase C", "B1-04", "B1-05", "E2-07", "evaluation/phase_b"):
                self.assertNotIn(forbidden, text, f"{path}: {forbidden}")

    def test_the_version_pins_are_0_5_0(self):
        self.assertIn("Version 0.5.0 (spec 0.7)", read("README.md"))
        self.assertIn("uses: Mukanto/truth_gate@v0.5.0", read("README.md"))
        self.assertIn("rev: v0.5.0", read(".pre-commit-hooks.yaml"))
        self.assertIn("Mukanto/truth_gate@v0.5.0", read("truth_gate/templates/truth-gate.yml"))
        self.assertIn('version = "0.5.0"', read("pyproject.toml"))
        for path in ("README.md", ".pre-commit-hooks.yaml", "truth_gate/templates/truth-gate.yml", "docs/GATE.md"):
            self.assertNotIn("v0.4.1", read(path), path)


# --------------------------------------------------------------------------
# Section 2.4: the error counts of a stream add up to its hard_undefined (post-freeze R-3)
# --------------------------------------------------------------------------

def error_sum_problems(components):
    """Streams where ``sum(errors[stream][component].values()) != counts[stream]['hard_undefined']``."""
    problems = []
    for comp in components:
        for stream, c in comp["counts"].items():
            found = sum(comp["errors"].get(stream, {}).values())
            if found != c["hard_undefined"]:
                problems.append((comp["id"], stream, found, c["hard_undefined"]))
    return problems


def draws_study(draws):
    """A deterministic study whose criterion acts on the i-th noise-probe draw as ``draws[i]``: ``S`` returns None,
    ``H`` raises, ``F`` returns False, ``N`` returns NaN.  The criterion is called on the noise draws in index order
    (the other streams carry constant data)."""
    calls = []

    def fn(d):
        x = d["x"]
        if np.all(x == 5.0):
            return True
        if np.all(x == 0.0) or np.all(x == -5.0):
            return False
        act = draws[len(calls)]
        calls.append(act)
        if act == "S":
            return None
        if act == "H":
            raise ValueError("a failure on this draw")
        if act == "N":
            return float("nan")
        return False

    return make_study(det=True, fn=fn)


class TestErrorsAddUpToHardUndefined(unittest.TestCase):
    """Spec 2.4: ``errors`` add up to ``hard_undefined``, on every stream, in both modes.  For a random probe of a
    deterministic study the three draws are combined, and ``errors`` follow the same rule as ``hard_undefined``."""

    def test_every_toy_study_in_both_modes(self):
        paths = []
        for folder in ("toy_studies", "toy_studies_spec07"):
            base = os.path.join(ROOT, "tests", folder)
            paths += [os.path.join(base, name) for name in sorted(os.listdir(base)) if name.endswith(".py")]
        checked = 0
        for path in paths:
            with open(path, "rb") as handle:
                source = handle.read()
            try:
                study = load_study(path, source)
            except Exception:
                continue  # a study that does not load has no components (tests/test_guard.py)
            for name, det in MODES:
                with self.subTest(study=os.path.basename(path), mode=name):
                    result = checks.evaluate(dataclasses.replace(study, deterministic=det), True)
                    self.assertEqual(error_sum_problems(result["components"]), [])
                    checked += 1
        self.assertGreater(checked, 100)

    def test_the_hand_built_studies_of_the_classification_in_both_modes(self):
        tags = ("none", "raise", "nan", "one", "str", "array")
        for tag in tags:
            for name, det in MODES:
                with self.subTest(tag=tag, mode=name):
                    result = checks.evaluate(make_study(det=det, minus_tag=tag), False)
                    self.assertEqual(error_sum_problems(result["components"]), [])
        for tag in ("cnone", "cdict", "cmissing", "cnondict", "cnan"):
            for name, det in MODES:
                with self.subTest(tag=tag, mode=name):
                    result = checks.evaluate(make_study(det=det, minus_tag=tag, components=["a", "b"]), False)
                    self.assertEqual(error_sum_problems(result["components"]), [])

    def test_every_combination_of_three_noise_draws(self):
        for draws in itertools.product("SHFN", repeat=3):
            with self.subTest(draws="".join(draws)):
                result = checks.evaluate(draws_study(draws), False)
                self.assertEqual(error_sum_problems(result["components"]), [])

    def test_audit_reproduction_soft_soft_raise_is_one_hard_failure_with_one_error_entry(self):
        comp = run(draws_study("SSH"))["C"]
        self.assertEqual(comp["probe_draws"]["probe:noise"], ["UNDEFINED"] * 3)
        self.assertEqual(comp["counts"]["probe:noise"], {"holds": 0, "undefined": 1, "hard_undefined": 1, "n": 1})
        self.assertEqual(comp["errors"]["probe:noise"], {"ValueError": 1})

    def test_audit_reproduction_raise_fails_fails_is_neither_undefined_nor_an_error(self):
        comp = run(draws_study("HFF"))["C"]
        self.assertEqual(comp["probe_draws"]["probe:noise"], ["UNDEFINED", "FAILS", "FAILS"])
        self.assertEqual(comp["counts"]["probe:noise"], {"holds": 0, "undefined": 0, "hard_undefined": 0, "n": 1})
        self.assertNotIn("probe:noise", comp["errors"])

    def test_the_entry_is_the_cause_of_the_first_hard_draw_and_only_when_the_combined_outcome_is_undefined(self):
        # draws: soft, bad return, raise -> combined UNDEFINED, first hard draw is the BAD_RETURN
        comp = run(draws_study("SNH"))["C"]
        self.assertEqual(comp["errors"]["probe:noise"], {"BAD_RETURN": 1})
        # one UNDEFINED draw only (two FAILS): the combined outcome is FAILS, no entry whatever the draw was
        for draws in ("HFF", "FHF", "FFH", "SFF"):
            comp = run(draws_study(draws))["C"]
            self.assertEqual(comp["counts"]["probe:noise"]["undefined"], 0, draws)
            self.assertNotIn("probe:noise", comp["errors"], draws)
        # two soft draws and no hard one: UNDEFINED but soft, so no entry
        comp = run(draws_study("SSF"))["C"]
        self.assertEqual(comp["counts"]["probe:noise"], {"holds": 0, "undefined": 1, "hard_undefined": 0, "n": 1})
        self.assertNotIn("probe:noise", comp["errors"])

    def test_a_probe_failing_on_every_draw_still_has_one_entry(self):
        comp = run(draws_study("HHH"))["C"]
        self.assertEqual(comp["counts"]["probe:noise"], {"holds": 0, "undefined": 1, "hard_undefined": 1, "n": 1})
        self.assertEqual(comp["errors"]["probe:noise"], {"ValueError": 1})

    def test_the_stochastic_rule_is_unchanged(self):
        comp = run(make_study(minus_tag="raise"))["C"]
        self.assertEqual(comp["errors"]["world:minus"], {"ValueError": 40})
        self.assertEqual(comp["counts"]["world:minus"]["hard_undefined"], 40)


if __name__ == "__main__":
    unittest.main()
