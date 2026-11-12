"""Kapi v0.2 (spec 0.4): declared alpha is mandatory (delta 1) and cascade suppression (delta 2)."""

import unittest

import _helpers
from _helpers import body, component, toy_path
import kapi
from kapi.checks import (
    CAPPING_FLAGS, MANDATORY_FLAGS, MANDATORY_PREFIXES, SUPPRESSIBLE_FLAGS, StreamStats, apply_cascade_suppression,
    component_verdict, evaluate, is_capping, is_mandatory, study_verdict,
)
from kapi.study import load_study

CASCADE_NAMES = [
    "K2_LOW_POWER", "K2_NO_SEPARATION", "K3_PREMISE_NOT_TESTED", "K4_CONTROL_ALSO_HOLDS",
    "K5_HOLDS_ON_DEGENERATE", "K5_HOLDS_ON_NOISE", "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE",
]


class TestClassification(unittest.TestCase):
    def test_high_size_and_high_rate_are_mandatory(self):
        self.assertIn("K2_HIGH_SIZE", MANDATORY_FLAGS)
        self.assertTrue(is_mandatory("HIGH_RATE:control:c"))
        self.assertTrue(is_mandatory("HIGH_RATE:probe:noise"))
        self.assertFalse(is_capping("HIGH_RATE:control:c"))
        self.assertFalse(is_capping("K2_HIGH_SIZE"))
        self.assertEqual(MANDATORY_PREFIXES, ("HIGH_RATE:",))

    def test_low_power_stays_capping(self):
        self.assertIn("K2_LOW_POWER", CAPPING_FLAGS)
        self.assertEqual(CAPPING_FLAGS, {"K2_LOW_POWER", "K3_INCONCLUSIVE", "K4_WAIVED", "K4_INCONCLUSIVE"})
        self.assertEqual(component_verdict(["K2_LOW_POWER"]), "WEAK")
        self.assertEqual(component_verdict(["K2_HIGH_SIZE"]), "NOT_FALSIFIABLE")
        self.assertEqual(component_verdict(["HIGH_RATE:world:null"]), "NOT_FALSIFIABLE")

    def test_k5_inconclusive_still_capping(self):
        self.assertEqual(component_verdict(["K5_INCONCLUSIVE:noise"]), "WEAK")


class TestToyVerdicts(unittest.TestCase):
    def test_a_only_high_size_is_not_falsifiable(self):
        c = component("toy_highsize")
        self.assertEqual(c["flags"], ["K2_HIGH_SIZE"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")  # WEAK in v0
        self.assertEqual(body("toy_highsize")["verdict"], "NOT_FALSIFIABLE")

    def test_b_only_high_rate_is_not_falsifiable(self):
        c = component("toy_high_rate")
        self.assertEqual(c["flags"], ["HIGH_RATE:control:leaky"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")  # WEAK in v0
        self.assertEqual(body("toy_high_rate")["verdict"], "NOT_FALSIFIABLE")

    def test_c_low_power_alone_is_still_weak(self):
        self.assertEqual(component("toy_lowpower")["flags"], ["K2_LOW_POWER"])
        self.assertEqual(body("toy_lowpower")["verdict"], "WEAK")

    def test_deterministic_mode_skips_both_rate_rules(self):
        flags = component("toy_good_det")["flags"]
        self.assertFalse([f for f in flags if f == "K2_HIGH_SIZE" or f.startswith("HIGH_RATE:")])
        self.assertEqual(body("toy_good_det")["verdict"], "FALSIFIABLE")

    def test_rate_rules_unchanged(self):
        # the rule is the same, only the class moved: the clean toy raises neither
        self.assertEqual(component("toy_good")["flags"], [])


class TestSuppressionRaised(unittest.TestCase):
    def test_stochastic(self):
        c = component("toy_suppress_stoch")
        self.assertEqual(c["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertEqual(c["suppressed"], CASCADE_NAMES)
        self.assertEqual(c["suppressed"], sorted(c["suppressed"]))
        self.assertEqual(c["flags"], ["K2_HOLDS_UNREACHABLE"])
        self.assertEqual(c["counts"]["world:plus"]["holds"], 0)
        for name in CASCADE_NAMES:
            self.assertNotIn(name, c["flags"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")

    def test_stochastic_simple_toy(self):
        c = component("toy_holds_unreachable")
        self.assertEqual(c["flags"], ["K2_HOLDS_UNREACHABLE"])
        self.assertEqual(c["suppressed"], ["K2_LOW_POWER", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS",
                                           "K5_HOLDS_ON_DEGENERATE", "K5_HOLDS_ON_NOISE"])

    def test_deterministic(self):
        c = component("toy_suppress_det")
        self.assertEqual(c["counts"]["world:plus"], {"holds": 0, "undefined": 0, "n": 1})
        self.assertEqual(c["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertEqual(c["suppressed"], [n for n in CASCADE_NAMES if n != "K2_LOW_POWER"])  # skipped when deterministic
        self.assertEqual(c["flags"], ["K2_HOLDS_UNREACHABLE"])
        self.assertEqual(c["verdict"], "NOT_FALSIFIABLE")

    def test_deterministic_with_undefined_plus_outcome(self):
        c = component("toy_det_undefined")  # plus UNDEFINED is "not HOLDS"
        self.assertEqual(c["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertIn("K1_UNDEFINED", c["flags"])
        self.assertIn("K4_INCONCLUSIVE", c["flags"])  # non-SL flags are kept
        self.assertIn("K5_INCONCLUSIVE:noise", c["flags"])
        self.assertNotIn("K5_HOLDS_ON_NOISE", c["flags"])
        self.assertEqual(c["verdict"], "UNDEFINED")

    def test_non_sl_and_study_flags_are_kept(self):
        c = component("toy_undefined_none")
        for kept in ("K1_UNDEFINED", "K2_HOLDS_UNREACHABLE", "K4_INCONCLUSIVE", "K5_INCONCLUSIVE:noise"):
            self.assertIn(kept, c["flags"])
        self.assertEqual(component("toy_no_control")["flags"], ["K4_NO_CONTROL"])

    def test_high_size_and_high_rate_are_never_suppressed(self):
        flags_in = {"K2_HOLDS_UNREACHABLE", "K2_HIGH_SIZE", "HIGH_RATE:control:c", "K2_FAILS_UNREACHABLE",
                    "K4_NO_CONTROL", "K4_WAIVED", "K2_UNRESOLVABLE", "K5_INCONCLUSIVE:noise", "K1_UNDEFINED"}
        kept, suppressed = apply_cascade_suppression(flags_in, StreamStats(0, 0, 10), False)
        self.assertEqual(kept, flags_in)
        self.assertEqual(suppressed, [])


class TestSuppressionNotRaised(unittest.TestCase):
    def test_plus_holds_sometimes_stochastic(self):
        for toy in ("toy_lowpower", "toy_good", "toy_no_separation", "toy_control_also_holds", "toy_noise",
                    "toy_shuffle_bad", "toy_null_holds"):
            c = component(toy)
            self.assertGreater(c["counts"]["world:plus"]["holds"], 0, toy)
            self.assertNotIn("suppressed", c, toy)
            self.assertNotIn("suppressed_by", c, toy)

    def test_sl_flags_still_raised_when_plus_holds(self):
        # spec 0.5 delta 1.1/1.5: toy_no_separation now has an identical (paired) minus, so use the distinct-minus toy
        self.assertIn("K2_NO_SEPARATION", component("toy_no_separation_distinct")["flags"])
        self.assertIn("K4_CONTROL_ALSO_HOLDS", component("toy_control_also_holds")["flags"])
        self.assertIn("K5_HOLDS_ON_NOISE", component("toy_noise")["flags"])
        self.assertIn("K2_LOW_POWER", component("toy_lowpower")["flags"])

    def test_plus_holds_deterministic(self):
        for toy in ("toy_good_det", "toy_det_always_true", "toy_det_noise_depends"):
            c = component(toy)
            self.assertEqual(c["counts"]["world:plus"]["holds"], 1, toy)
            self.assertNotIn("suppressed", c, toy)
        self.assertIn("K5_HOLDS_ON_NOISE", component("toy_det_noise_depends")["flags"])

    def test_zero_holds_but_nothing_to_suppress_adds_no_field(self):
        kept, suppressed = apply_cascade_suppression({"K2_HOLDS_UNREACHABLE"}, StreamStats(0, 0, 10), False)
        self.assertEqual((kept, suppressed), ({"K2_HOLDS_UNREACHABLE"}, []))

    def test_unit_plus_holds_keeps_everything(self):
        flags = {"K2_NO_SEPARATION", "K2_LOW_POWER", "K5_HOLDS_ON_NOISE"}
        self.assertEqual(apply_cascade_suppression(flags, StreamStats(1, 0, 10), False), (flags, []))


class TestKeptUnresolvableMagnitude(unittest.TestCase):
    def test_k3_from_unresolvable_magnitude_is_kept(self):
        c = component("toy_suppress_unresolvable")
        self.assertEqual(c["flags"], ["K2_HOLDS_UNREACHABLE", "K2_UNRESOLVABLE", "K3_PREMISE_NOT_TESTED"])
        self.assertEqual(c["unresolvable"], ["premise:shift"])
        self.assertEqual(c["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertNotIn("K3_PREMISE_NOT_TESTED", c["suppressed"])  # kept, so it was not suppressed
        self.assertEqual(c["suppressed"], ["K2_LOW_POWER", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS",
                                           "K5_HOLDS_ON_DEGENERATE", "K5_HOLDS_ON_NOISE"])

    def test_unit(self):
        flags = {"K3_PREMISE_NOT_TESTED", "K2_NO_SEPARATION", "K2_HOLDS_UNREACHABLE"}
        kept, suppressed = apply_cascade_suppression(flags, StreamStats(0, 0, 10), True)
        self.assertEqual(kept, {"K3_PREMISE_NOT_TESTED", "K2_HOLDS_UNREACHABLE"})
        self.assertEqual(suppressed, ["K2_NO_SEPARATION"])
        kept, suppressed = apply_cascade_suppression(flags, StreamStats(0, 0, 10), False)
        self.assertEqual(kept, {"K2_HOLDS_UNREACHABLE"})
        self.assertEqual(suppressed, ["K2_NO_SEPARATION", "K3_PREMISE_NOT_TESTED"])

    def test_suppressible_set_matches_the_delta(self):
        self.assertEqual(SUPPRESSIBLE_FLAGS, set(CASCADE_NAMES) )


INVARIANCE_TOYS = (
    "toy_suppress_stoch", "toy_suppress_det", "toy_suppress_unresolvable", "toy_holds_unreachable",
    "toy_undefined_none", "toy_bad_return", "toy_det_undefined", "toy_good", "toy_good_det", "toy_lowpower",
    "toy_no_separation", "toy_noise", "toy_shuffle_bad", "toy_det_always_true", "toy_components_mismatch",
    "toy_inconclusive_probe", "toy_highsize", "toy_high_rate",
)


def evaluate_toy(name, suppress):
    path = toy_path(name)
    with open(path, "rb") as handle:
        study = load_study(path, handle.read())
    return evaluate(study, quick=False, suppress_cascade=suppress)


class TestVerdictInvariance(unittest.TestCase):
    """Suppression never changes a verdict (v0.2 delta 2)."""

    def test_verdicts_equal_with_and_without_suppression(self):
        for toy in INVARIANCE_TOYS:
            with self.subTest(toy=toy):
                on, off = evaluate_toy(toy, True), evaluate_toy(toy, False)
                self.assertEqual([c["verdict"] for c in on["components"]], [c["verdict"] for c in off["components"]])
                self.assertEqual(
                    study_verdict([c["verdict"] for c in on["components"]], on["study_flags"]),
                    study_verdict([c["verdict"] for c in off["components"]], off["study_flags"]),
                )

    def test_information_is_moved_not_deleted(self):
        for toy in INVARIANCE_TOYS:
            with self.subTest(toy=toy):
                on, off = evaluate_toy(toy, True), evaluate_toy(toy, False)
                for a, b in zip(on["components"], off["components"]):
                    self.assertNotIn("suppressed", b)
                    kept_flags = set(a["flags"])
                    restored = kept_flags | set(a.get("suppressed", []))
                    self.assertEqual(restored, set(b["flags"]))
                    self.assertTrue(kept_flags <= set(b["flags"]))

    def test_suppression_only_removes_sl_derived_flags(self):
        for toy in INVARIANCE_TOYS:
            on, off = evaluate_toy(toy, True), evaluate_toy(toy, False)
            for a, b in zip(on["components"], off["components"]):
                removed = set(b["flags"]) - set(a["flags"])
                self.assertTrue(removed <= SUPPRESSIBLE_FLAGS, (toy, removed))

    def test_certificate_verdicts_match_unsuppressed_run(self):
        for toy in ("toy_suppress_stoch", "toy_suppress_det", "toy_holds_unreachable"):
            off = evaluate_toy(toy, False)
            self.assertEqual([c["verdict"] for c in body(toy)["components"]], [c["verdict"] for c in off["components"]])


class TestVersions(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(kapi.__version__, "0.4.0")
        self.assertEqual(body("toy_good")["tool_version"], "0.4.0")
        self.assertEqual(body("toy_good")["spec_version"], "0.6")
        self.assertEqual(kapi.SPEC_VERSION, "0.6")


if __name__ == "__main__":
    unittest.main()
