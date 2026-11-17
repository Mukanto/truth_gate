import json
import math
import os
import tempfile
import unittest
from statistics import NormalDist
from unittest import mock

import common
import toy_case
import clean_pass_class as cpc
from assemble import assemble
from structure_stat import import_truth_gate, load_study_module

SEED = 20261117


def body_returning(expr):
    return f"import numpy as np\n\n\ndef criterion(d):\n    return {expr}\n"


# On the toy's minus world with phi = 0 (x and y iid N(0,1)):
#   y[0] > 0       holds in 50% of the minus, noise and control samples;
#   y[0] > 1.6449  holds in 5% of the minus (and noise) samples, and in 23% of the control samples (the control permutes
#                  the plus y, whose variance is 5);
#   y[0] > 4       holds in about 3e-5 of the minus samples.
ABOVE = 'bool(d["y"][0] > 0.0)'
INCLUDES = 'bool(d["y"][0] > 1.6449)'
BELOW = 'bool(d["y"][0] > 4.0)'


def make_study(test, fixed_expr, reference_edit=None):
    """The assembled fixed study of a phi = 0 toy case, loaded as a module."""
    ref = toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": 0.0}
    if reference_edit:
        ref = reference_edit(ref)
    src = assemble(ref, body_returning(fixed_expr))
    return load_study_module(src, "fixed_study.py", "t"), src


def cert(verdict, flags, counts=None, bounds=None, study_flags=(), load_error=None):
    """A certificate body with one component (only the fields the tool reads)."""
    if load_error is not None:
        return {"verdict": "UNDEFINED", "components": [], "load_error": load_error, "study_flags": []}
    comp = {"id": "C", "flags": list(flags),
            "counts": {s: {"holds": h, "undefined": 0, "hard_undefined": 0, "n": n} for s, (h, n) in (counts or {}).items()},
            "bounds": {s: {"lower": lo, "upper": up} for s, (lo, up) in (bounds or {}).items()}}
    return {"verdict": verdict, "load_error": None, "components": [comp], "study_flags": list(study_flags)}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)

    def classify(self, module, body, **kw):
        return cpc.classify_clean_pass(module, body, common.PKG, **kw)


class WilsonTests(Base):
    def test_interval_is_the_95_percent_two_sided_wilson(self):
        z = NormalDist().inv_cdf(0.975)

        def wilson(k, n):
            p = k / n
            den = 1 + z * z / n
            centre = (p + z * z / (2 * n)) / den
            half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
            return centre - half, centre + half

        for k in (1, 37, 50, 64, 500, 999):
            lo, hi = cpc.wilson_interval(k, 1000)
            self.assertAlmostEqual(lo, wilson(k, 1000)[0], places=9)
            self.assertAlmostEqual(hi, wilson(k, 1000)[1], places=9)
        lo, hi = cpc.wilson_interval(0, 1000)  # the gate sets the lower bound to exactly 0 at k = 0
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, z * z / (1000 + z * z), places=9)

    def test_relation(self):
        self.assertEqual(cpc.relation(0.06, 0.09, 0.05), "above")
        self.assertEqual(cpc.relation(0.05, 0.09, 0.05), "includes")  # the closed interval includes its end point
        self.assertEqual(cpc.relation(0.03, 0.05, 0.05), "includes")
        self.assertEqual(cpc.relation(0.0, 0.0499, 0.05), "below")
        self.assertEqual(cpc.relation(0.03, 0.07, 0.05), "includes")


class AttritionTests(Base):
    def setUp(self):
        self.module, _ = make_study(self, ABOVE)

    def test_load_error(self):
        r = self.classify(self.module, cert(None, [], load_error={"type": "SyntaxError", "message": "x"}))
        self.assertEqual(r["class"], "e")
        self.assertEqual(r["causes"], ["load error: SyntaxError"])
        self.assertEqual(r["label"], "attrition or no verdict")

    def test_k1_undefined(self):
        r = self.classify(self.module, cert("UNDEFINED", ["K1_UNDEFINED", "K2_NO_SEPARATION"]))
        self.assertEqual((r["class"], r["causes"]), ("e", ["K1_UNDEFINED"]))

    def test_untested(self):
        r = self.classify(self.module, cert("UNTESTED", ["K2_MINUS_IDENTICAL"]))
        self.assertEqual((r["class"], r["causes"]), ("e", ["UNTESTED"]))

    def test_timeout_needs_no_certificate(self):
        r = self.classify(self.module, None, timeout=True)
        self.assertEqual((r["class"], r["causes"]), ("e", ["timeout"]))

    def test_timeout_and_a_certificate_list_both_causes(self):
        r = self.classify(self.module, cert("UNDEFINED", ["K1_UNDEFINED"]), timeout=True)
        self.assertEqual(r["causes"], ["timeout", "K1_UNDEFINED"])

    def test_attrition_wins_over_a_rate_flag(self):
        r = self.classify(self.module, cert("UNDEFINED", ["K1_UNDEFINED", "K2_HIGH_SIZE"]))
        self.assertEqual(r["class"], "e")
        self.assertEqual(r["streams"], [])  # no fresh samples were drawn

    def test_missing_certificate_without_timeout_is_an_error(self):
        with self.assertRaises(cpc.ClassifyError):
            self.classify(self.module, None)

    def test_a_clean_pass_has_no_class(self):
        for verdict in ("FALSIFIABLE", "WEAK"):
            r = self.classify(self.module, cert(verdict, ["K2_LOW_POWER"] if verdict == "WEAK" else []))
            self.assertIsNone(r["class"])
            self.assertIn("clean pass", r["reasons"][0])


class FreshSampleClassTests(Base):
    """Classes (1) and (2): the fresh estimate decides, not the certificate's count."""

    def test_class_1_fixed_not_clean(self):
        module, _ = make_study(self, ABOVE)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]))
        self.assertEqual(r["class"], "1")
        s = r["streams"][0]
        self.assertEqual((s["stream"], s["flags"], s["n"], s["relation"]), ("world:minus", ["K2_HIGH_SIZE"], 1000, "above"))
        self.assertAlmostEqual(s["rate"], 0.5, delta=0.05)
        self.assertGreater(s["interval"][0], 0.05)
        self.assertEqual((r["size"], r["seed"], r["samples"]), (0.05, SEED, 1000))

    def test_class_2_possible_false_alarm(self):
        module, _ = make_study(self, INCLUDES)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]))
        s = r["streams"][0]
        self.assertEqual(r["class"], "2", s)
        self.assertLessEqual(s["interval"][0], 0.05)
        self.assertGreaterEqual(s["interval"][1], 0.05)

    def test_one_stream_above_makes_class_1_even_if_another_includes(self):
        module, _ = make_study(self, INCLUDES)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:control:permute_y"]))
        rel = {s["stream"]: s["relation"] for s in r["streams"]}
        self.assertEqual(rel, {"control:permute_y": "above", "world:minus": "includes"})
        self.assertEqual(r["class"], "1")

    def test_class_2_needs_every_stream_to_include_the_size(self):
        module, _ = make_study(self, 'bool(d["y"][0] > 1.59)')  # 58 and 39 holds of 1000 on minus and noise (seed 20261117)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:probe:noise"]))
        self.assertEqual({s["relation"] for s in r["streams"]}, {"includes"})
        self.assertEqual(r["class"], "2")

    def test_an_interval_below_the_size_is_class_2(self):
        # T3-1: class (2) is "no flagged rate stream has a fresh interval above the size"
        module, _ = make_study(self, BELOW)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]))
        s = r["streams"][0]
        self.assertEqual((s["relation"], s["holds"]), ("below", 0))
        self.assertLess(s["interval"][1], 0.05)
        self.assertEqual(r["class"], "2")

    def test_includes_and_below_together_are_class_2_and_each_relation_is_recorded(self):
        module, _ = make_study(self, INCLUDES)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:probe:zeros"]))
        rel = {s["stream"]: s["relation"] for s in r["streams"]}
        self.assertEqual(rel, {"world:minus": "includes", "probe:zeros": "below"})
        self.assertEqual(r["class"], "2")

    def test_the_three_relations_are_recorded_and_one_above_makes_class_1(self):
        module, _ = make_study(self, INCLUDES)
        r = self.classify(module, cert("NOT_FALSIFIABLE",
                                       ["K2_HIGH_SIZE", "HIGH_RATE:probe:zeros", "HIGH_RATE:control:permute_y"]))
        rel = {s["stream"]: s["relation"] for s in r["streams"]}
        self.assertEqual(rel, {"world:minus": "includes", "probe:zeros": "below", "control:permute_y": "above"})
        self.assertEqual(r["class"], "1")

    def test_a_relative_flag_on_the_same_stream_as_an_unconfirmed_rate_flag_is_class_3(self):
        # D-R4-6 (R3-5): the clause "whose stream carries no rate flag" is dropped
        module, _ = make_study(self, BELOW)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["HIGH_RATE:probe:noise", "K5_HOLDS_ON_NOISE"]))
        self.assertEqual(r["streams"][0]["relation"], "below")
        self.assertEqual(r["class"], "3")
        self.assertEqual(r["unconfirmed_rate_flags"],
                         [{"stream": "probe:noise", "flags": ["HIGH_RATE:probe:noise"], "relation": "below"}])

    def test_rate_flags_of_each_stream_kind(self):
        def edit(ref):
            ref = ref.replace('        "plus": World(plus),\n', '        "plus": World(plus),\n        "null": World(minus),\n')
            return ref.replace("    controls=[", '    relational=[("x", "y")],\n    controls=[')
        module, _ = make_study(self, ABOVE, reference_edit=edit)
        flags = ["K2_HIGH_SIZE", "HIGH_RATE:world:null", "HIGH_RATE:control:permute_y", "HIGH_RATE:probe:noise",
                 "HIGH_RATE:probe:zeros", "HIGH_RATE:probe:shuffle:x,y"]
        r = self.classify(module, cert("NOT_FALSIFIABLE", flags), samples=200)
        got = {s["stream"]: s["relation"] for s in r["streams"]}
        self.assertEqual(sorted(got), sorted(["world:minus", "world:null", "control:permute_y", "probe:noise", "probe:zeros",
                                              "probe:shuffle:x,y"]))
        self.assertEqual(got["probe:zeros"], "below")  # the zeros probe: y[0] = 0 is not > 0
        self.assertEqual({got[k] for k in got if k != "probe:zeros"}, {"above"})
        self.assertEqual(r["class"], "1")

    def test_a_flagged_stream_the_study_lacks_is_an_error(self):
        module, _ = make_study(self, ABOVE)
        with self.assertRaises(cpc.ClassifyError):
            self.classify(module, cert("NOT_FALSIFIABLE", ["HIGH_RATE:world:null"]))

    def test_samples_and_seed_are_the_arguments(self):
        module, _ = make_study(self, ABOVE)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]), samples=50, seed=7)
        self.assertEqual((r["samples"], r["seed"], r["streams"][0]["n"]), (50, 7, 50))


class RateFlagWithOtherFlagsTests(Base):
    """D-R4-6 (R3-5, R3-14): a rate flag that the fresh samples did not confirm, together with other failure flags."""

    def setUp(self):
        self.includes, _ = make_study(self, INCLUDES)  # minus: 54 of 1000 holds, the interval includes the size

    def test_the_rate_flag_alone_is_class_2(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]))
        self.assertEqual(r["class"], "2")
        self.assertEqual([(u["stream"], u["relation"]) for u in r["unconfirmed_rate_flags"]], [("world:minus", "includes")])

    def test_with_k2_no_separation_it_is_class_3(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "K2_NO_SEPARATION"]))
        self.assertEqual(r["class"], "3", r["reasons"])
        self.assertEqual(r["unconfirmed_rate_flags"][0]["flags"], ["K2_HIGH_SIZE"])

    def test_with_the_other_listed_flags_it_is_class_3(self):
        for extra in (["K2_HOLDS_UNREACHABLE"], ["K2_LOW_POWER", "K2_NO_SEPARATION"], ["K4_CONTROL_ALSO_HOLDS"],
                      ["K5_HOLDS_ON_NULL"], ["K5_HOLDS_ON_DEGENERATE"], ["K5_HOLDS_ON_SHUFFLE"],
                      ["K5_HOLDS_ON_NOISE", "K4_CONTROL_ALSO_HOLDS"]):
            with self.subTest(extra):
                r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"] + extra), samples=100)
                self.assertEqual(r["class"], "3", (extra, r["reasons"]))

    def test_with_k5_holds_on_noise_on_the_same_stream_as_the_rate_flag_it_is_class_3(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["HIGH_RATE:probe:noise", "K5_HOLDS_ON_NOISE"]), samples=100)
        self.assertEqual(r["streams"][0]["stream"], "probe:noise")
        self.assertNotEqual(r["streams"][0]["relation"], "above")
        self.assertEqual(r["class"], "3")

    def test_with_k4_no_control_it_is_class_4(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "K4_NO_CONTROL"]))
        self.assertEqual(r["class"], "4")
        self.assertEqual(r["unconfirmed_rate_flags"][0]["stream"], "world:minus")

    def test_with_a_study_level_flag_it_is_class_4(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], study_flags=["K7_REGIME_UNCOVERED"]))
        self.assertEqual(r["class"], "4")
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "K2_NO_SEPARATION"], study_flags=["NONDETERMINISTIC"]))
        self.assertEqual(r["class"], "4")

    def test_with_another_mandatory_flag_it_is_class_4(self):
        for extra in ("K2_UNRESOLVABLE", "K3_PREMISE_NOT_TESTED", "K2_FAILS_UNREACHABLE", "K8_NOT_INVARIANT"):
            with self.subTest(extra):
                r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", extra]), samples=100)
                self.assertEqual(r["class"], "4", (extra, r["reasons"]))

    def test_a_confirmed_rate_flag_is_class_1_whatever_else_is_flagged(self):
        above, _ = make_study(self, ABOVE)
        for extra in ([], ["K2_NO_SEPARATION"], ["K4_NO_CONTROL"], ["K2_UNRESOLVABLE"]):
            with self.subTest(extra):
                r = self.classify(above, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"] + extra), samples=100)
                self.assertEqual(r["class"], "1")
                self.assertEqual(r["unconfirmed_rate_flags"], [])  # recorded only when the class is not (1)

    def test_no_rate_flag_no_unconfirmed_list(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_NO_SEPARATION"]))
        self.assertEqual((r["class"], r["unconfirmed_rate_flags"], r["streams"]), ("3", [], []))

    def test_unconfirmed_streams_are_listed_with_their_relations(self):
        r = self.classify(self.includes, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:probe:zeros", "K2_NO_SEPARATION"]),
                          samples=100)
        got = {u["stream"]: u["relation"] for u in r["unconfirmed_rate_flags"]}
        self.assertEqual(got["probe:zeros"], "below")
        self.assertEqual(set(got), {"world:minus", "probe:zeros"})
        self.assertEqual(r["class"], "3")


class AttritionOptionTests(Base):
    """D-R4-6: ``--attrition CAUSE`` for an invalid skeleton, a part-B "no" or any other cause."""

    def test_attrition_needs_no_certificate_and_no_study(self):
        r = cpc.classify_clean_pass(None, None, common.PKG, attrition="invalid skeleton")
        self.assertEqual((r["class"], r["causes"]), ("e", ["invalid skeleton"]))

    def test_attrition_with_other_causes_lists_all(self):
        module, _ = make_study(self, ABOVE)
        r = self.classify(module, cert("UNDEFINED", ["K1_UNDEFINED"]), attrition="part-B no", timeout=True)
        self.assertEqual(r["causes"], ["part-B no", "timeout", "K1_UNDEFINED"])

    def test_attrition_wins_over_a_certificate_with_rate_flags(self):
        module, _ = make_study(self, ABOVE)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]), attrition="part-B no")
        self.assertEqual(r["class"], "e")
        self.assertEqual(r["streams"], [])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "o.json")
            r = common.run_tool("clean_pass_class.py", "--attrition", "invalid skeleton", "--package-root", common.PKG, "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["causes"], ["invalid skeleton"])
            self.assertEqual(common.run_tool("clean_pass_class.py", "--package-root", common.PKG).returncode, 2)


class MirrorTests(Base):
    """The fresh samples are the gate's own stream construction under the stream names ``classify:<stream>``."""

    def test_world_stream_equals_a_direct_recomputation(self):
        from truth_gate.sampling import stream_rng
        module, _ = make_study(self, INCLUDES)
        n = 300
        direct = sum(bool(module.STUDY.worlds["minus"].generate(stream_rng(SEED, "classify:world:minus", i))["y"][0] > 1.6449)
                     for i in range(n))
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]), samples=n)
        self.assertEqual(r["streams"][0]["holds"], direct)

    def test_derived_streams_equal_a_direct_recomputation(self):
        from truth_gate import probes
        from truth_gate.sampling import copy_data, stream_rng
        module, _ = make_study(self, INCLUDES)
        n = 300
        ctrl = noise = 0
        for i in range(n):
            plus = module.STUDY.worlds["plus"].generate(stream_rng(SEED, "classify:world:plus", i))
            c = module.STUDY.controls[0].transform(copy_data(plus), stream_rng(SEED, "classify:control:permute_y", i))
            ctrl += bool(c["y"][0] > 1.6449)
            nz = probes.noise_probe(copy_data(plus), stream_rng(SEED, "classify:probe:noise", i))
            noise += bool(nz["y"][0] > 1.6449)
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["HIGH_RATE:control:permute_y", "HIGH_RATE:probe:noise"]), samples=n)
        got = {s["stream"]: s["holds"] for s in r["streams"]}
        self.assertEqual(got, {"control:permute_y": ctrl, "probe:noise": noise})

    def test_stream_names_and_seed(self):
        from truth_gate import sampling
        module, _ = make_study(self, ABOVE)
        real = sampling.stream_rng
        seen = set()

        def spy(seed, stream, i):
            seen.add((seed, stream))
            return real(seed, stream, i)

        with mock.patch.object(sampling, "stream_rng", spy):
            self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:control:permute_y", "HIGH_RATE:probe:noise"]),
                          samples=5)
        self.assertEqual(seen, {(SEED, "classify:world:plus"), (SEED, "classify:world:minus"),
                                (SEED, "classify:control:permute_y"), (SEED, "classify:probe:noise")})
        self.assertEqual({s for _, s in seen} & {"world:plus", "world:minus", "probe:noise", "control:permute_y"}, set())

    def test_the_gates_stream_function_is_restored(self):
        from truth_gate import checks
        module, _ = make_study(self, ABOVE)
        before = checks.stream_rng
        self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]), samples=5)
        self.assertIs(checks.stream_rng, before)
        with self.assertRaises(cpc.ClassifyError):
            self.classify(module, cert("NOT_FALSIFIABLE", ["HIGH_RATE:world:null"]), samples=5)
        self.assertIs(checks.stream_rng, before)

    def test_uses_the_gates_make_sample(self):
        # the tool must not carry its own copy of the stream construction
        with open(cpc.__file__, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("checks.make_sample(", src)
        self.assertIn("checks.build_plan(", src)
        self.assertIn("checks.evaluate_detailed(", src)

    def test_a_none_return_is_not_holds(self):
        module, _ = make_study(self, "None")
        r = self.classify(module, cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]), samples=20)
        self.assertEqual((r["streams"][0]["holds"], r["streams"][0]["undefined"]), (0, 20))


class WeakInPlusAndOtherTests(Base):
    def setUp(self):
        self.module, _ = make_study(self, ABOVE)
        self.counts = {"world:plus": (180, 200), "probe:noise": (170, 200), "control:permute_y": (2, 200),
                       "control:other": (172, 200)}
        self.bounds = {"world:plus": (0.84, 0.94), "probe:noise": (0.79, 0.89), "control:permute_y": (0.0, 0.05),
                       "control:other": (0.8, 0.9)}

    def cls(self, flags, study_flags=(), verdict="NOT_FALSIFIABLE"):
        r = self.classify(self.module, cert(verdict, flags, self.counts, self.bounds, study_flags))
        self.assertEqual(r["streams"], [])  # none of these needs fresh samples
        return r

    def test_class_3_from_each_listed_flag(self):
        for flags in (["K2_NO_SEPARATION"], ["K2_HOLDS_UNREACHABLE"], ["K2_HOLDS_UNREACHABLE", "K2_NO_SEPARATION"],
                      ["K2_NO_SEPARATION", "K2_LOW_POWER"], ["K5_HOLDS_ON_NOISE"], ["K5_HOLDS_ON_DEGENERATE"],
                      ["K5_HOLDS_ON_NULL"], ["K5_HOLDS_ON_SHUFFLE"], ["K4_CONTROL_ALSO_HOLDS"],
                      ["K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE", "K2_NO_SEPARATION", "K3_INCONCLUSIVE"]):
            with self.subTest(flags):
                r = self.cls(flags)
                self.assertEqual(r["class"], "3", r["reasons"])
                self.assertEqual(r["label"], "fixed weak in plus")

    def test_a_rate_flag_rules_class_3_out(self):
        r = self.classify(make_study(self, ABOVE)[0], cert("NOT_FALSIFIABLE", ["K2_NO_SEPARATION", "K2_HIGH_SIZE"]))
        self.assertEqual(r["class"], "1")  # decided by the fresh estimate, not (3)

    def test_other_mandatory_flags_make_class_4(self):
        for flags in (["K2_UNRESOLVABLE"], ["K3_PREMISE_NOT_TESTED"], ["K4_NO_CONTROL"], ["K2_NO_SEPARATION", "K2_UNRESOLVABLE"],
                      ["K2_FAILS_UNREACHABLE"], ["K8_NOT_INVARIANT"], ["K2_LOW_POWER", "K3_PREMISE_NOT_TESTED"]):
            with self.subTest(flags):
                r = self.cls(flags)
                self.assertEqual(r["class"], "4", r["reasons"])
                self.assertEqual(r["label"], "other")

    def test_a_study_level_flag_makes_class_4(self):
        r = self.cls(["K2_NO_SEPARATION"], study_flags=["K7_REGIME_UNCOVERED"])
        self.assertEqual(r["class"], "4")
        self.assertIn("K7_REGIME_UNCOVERED", r["reasons"][-1])

    def test_class_4_lists_its_flags(self):
        r = self.cls(["K2_UNRESOLVABLE", "K2_LOW_POWER", "BAD_RETURN"])
        self.assertEqual(r["class"], "4")
        self.assertEqual(r["flags"], ["K2_UNRESOLVABLE", "K2_LOW_POWER", "BAD_RETURN"])
        self.assertEqual(r["failure_flags"], ["K2_UNRESOLVABLE"])  # mandatory flags only

    def test_relative_flag_streams(self):
        f = cpc.relative_flag_streams
        self.assertEqual(f("K4_CONTROL_ALSO_HOLDS", {k: 1 for k in self.counts}, {k: dict(zip(("lower", "upper"), v))
                                                                                   for k, v in self.bounds.items()}),
                         ["control:other"])
        self.assertEqual(f("K5_HOLDS_ON_NOISE", {}, {}), ["probe:noise"])
        self.assertEqual(f("K5_HOLDS_ON_DEGENERATE", {}, {}), ["probe:zeros"])
        self.assertEqual(f("K5_HOLDS_ON_NULL", {}, {}), ["world:null"])
        self.assertEqual(f("K5_HOLDS_ON_SOMETHING_NEW", {}, {}), [])  # exactly the K5_HOLDS_ON_* family (T3-2)
        for flag in ("K2_HIGH_SIZE", "HIGH_RATE:probe:noise", "K4_NO_CONTROL", "K4_WAIVED", "K4_INCONCLUSIVE",
                     "K2_NO_SEPARATION", "K5_INCONCLUSIVE:noise"):
            self.assertIsNone(f(flag, {}, {}))
        self.assertEqual(cpc.rate_flag_streams(["K2_HIGH_SIZE", "HIGH_RATE:control:a", "K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"]),
                         {"world:minus": ["K2_HIGH_SIZE"], "control:a": ["HIGH_RATE:control:a"],
                          "probe:noise": ["HIGH_RATE:probe:noise"]})

    def test_order_of_the_classes(self):
        # (e) before (1): a load error with rate flags is attrition; (1) before (3): a rate flag with K2_NO_SEPARATION
        self.assertEqual(self.classify(self.module, cert("UNDEFINED", ["K2_HIGH_SIZE", "K1_UNDEFINED"]))["class"], "e")


class CliTests(Base):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        _, src = make_study(self, ABOVE)
        self.study = os.path.join(t, "fixed_study.py")
        with open(self.study, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        self.cert = os.path.join(t, "fixed.json")
        self.out = os.path.join(t, "out.json")

    def write_cert(self, body, wrap=True):
        with open(self.cert, "w", encoding="utf-8") as f:
            json.dump({"body": body, "body_sha256": "x"} if wrap else body, f)

    def run_cli(self, *extra, with_cert=True):
        args = ["--study", self.study, "--package-root", common.PKG, "--out", self.out, *extra]
        if with_cert:
            args += ["--cert", self.cert]
        return common.run_tool("clean_pass_class.py", *args)

    def test_class_3_through_the_cli_with_a_wrapped_certificate(self):
        self.write_cert(cert("NOT_FALSIFIABLE", ["K2_NO_SEPARATION"]))
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["class"], "3")
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["class"], "3")

    def test_class_1_through_the_cli_with_a_bare_body(self):
        self.write_cert(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]), wrap=False)
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual((res["class"], res["streams"][0]["relation"]), ("1", "above"))

    def test_timeout_flag_without_a_certificate(self):
        r = self.run_cli("--timeout", with_cert=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["causes"], ["timeout"])

    def test_usage_errors(self):
        self.assertEqual(self.run_cli(with_cert=False).returncode, 2)  # no certificate, no --timeout
        self.write_cert(cert("NOT_FALSIFIABLE", ["HIGH_RATE:world:null"]))
        self.assertEqual(self.run_cli().returncode, 2)  # the study has no such stream
        r = common.run_tool("clean_pass_class.py", "--study", self.study, "--cert", self.cert, "--package-root", self.tmp.name)
        self.assertEqual(r.returncode, 2)  # not a gate
        self.assertEqual(common.run_tool("clean_pass_class.py", "--study", self.study).returncode, 2)  # no package root
        with open(self.cert, "w", encoding="utf-8") as f:
            f.write("not json")
        self.assertEqual(self.run_cli().returncode, 2)


if __name__ == "__main__":
    unittest.main()
