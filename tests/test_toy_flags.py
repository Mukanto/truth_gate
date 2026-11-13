"""Reachability on toy studies (spec section 11): every verdict, every flag raised and not raised.

Every flag of spec section 5 (plus BAD_RETURN from section 3) has one test that raises it on a toy
study and one test that shows it is not raised on another toy.  Test names:
``test_raised__<FLAG>`` and ``test_not_raised__<FLAG>``.
"""

import unittest

import _helpers
from _helpers import body, component, raised

# flag -> (toy that raises it, toy that does not).  ``PREFIX:*`` denotes a flag family.
FLAG_TOYS = {
    "K1_UNDEFINED": ("toy_undefined_none", "toy_good"),
    "K2_HOLDS_UNREACHABLE": ("toy_holds_unreachable", "toy_good"),
    "K2_FAILS_UNREACHABLE": ("toy_fails_unreachable", "toy_good"),
    "K2_NO_SEPARATION": ("toy_no_separation_distinct", "toy_good"),  # spec 0.5 delta 1.1/1.5: toy_no_separation has an identical minus
    "K2_UNRESOLVABLE": ("toy_unresolvable_tol", "toy_good"),
    "K2_LOW_POWER": ("toy_lowpower", "toy_good"),
    "K2_HIGH_SIZE": ("toy_highsize", "toy_good"),
    "HIGH_RATE:*": ("toy_high_rate", "toy_good"),
    "K3_PREMISE_NOT_TESTED": ("toy_not_tested_premise", "toy_good"),
    "K3_INCONCLUSIVE": ("toy_inconclusive_premise", "toy_good"),
    "K4_NO_CONTROL": ("toy_no_control", "toy_good"),
    "K4_WAIVED": ("toy_waived", "toy_good"),
    "K4_CONTROL_ALSO_HOLDS": ("toy_control_also_holds", "toy_good"),
    "K4_INCONCLUSIVE": ("toy_inconclusive_control", "toy_good"),
    "K5_HOLDS_ON_NOISE": ("toy_noise", "toy_good"),
    "K5_HOLDS_ON_DEGENERATE": ("toy_degenerate", "toy_good"),
    "K5_HOLDS_ON_NULL": ("toy_null_holds", "toy_good"),
    "K5_HOLDS_ON_SHUFFLE": ("toy_shuffle_bad", "toy_shuffle_good"),
    "K5_INCONCLUSIVE:*": ("toy_inconclusive_probe", "toy_good"),
    "K6_LEAK_ATTEMPT": ("toy_leak_open", "toy_allowed_file"),
    "K6_NONREPRODUCIBLE": ("toy_nonreproducible", "toy_good"),
    "K7_REGIME_UNCOVERED": ("toy_regime_uncovered", "toy_regime_covered"),
    "K7_COMPONENT_MISMATCH": ("toy_components_mismatch", "toy_components_ok"),
    "NONDETERMINISTIC": ("toy_nondeterministic", "toy_good_det"),
    "BAD_RETURN": ("toy_bad_return", "toy_good"),
}


def _make_tests():
    ns = {}
    for flag, (raising, clean) in FLAG_TOYS.items():
        label = flag.replace(":*", "").replace(":", "_")

        def raises_test(self, flag=flag, raising=raising):
            self.assertTrue(raised(raising, flag), f"{raising} should raise {flag}")

        def clean_test(self, flag=flag, clean=clean):
            self.assertFalse(raised(clean, flag), f"{clean} should not raise {flag}")

        ns[f"test_raised__{label}"] = raises_test
        ns[f"test_not_raised__{label}"] = clean_test
    return ns


TestFlagReachability = type("TestFlagReachability", (unittest.TestCase,), _make_tests())


class TestVerdictReachability(unittest.TestCase):
    """Each of the four verdicts is produced by at least one toy (spec section 11)."""

    def test_falsifiable(self):
        self.assertEqual(body("toy_good")["verdict"], "FALSIFIABLE")
        self.assertEqual(body("toy_good_det")["verdict"], "FALSIFIABLE")

    def test_weak(self):
        for toy in ("toy_lowpower", "toy_waived", "toy_inconclusive_premise",
                    "toy_inconclusive_control", "toy_inconclusive_probe", "toy_det_waived"):
            self.assertEqual(body(toy)["verdict"], "WEAK", toy)

    def test_not_falsifiable(self):
        for toy in ("toy_no_control", "toy_not_tested_premise", "toy_unresolvable_tol", "toy_noise",
                    "toy_regime_uncovered", "toy_nonreproducible", "toy_leak_listdir", "toy_det_always_true",
                    "toy_highsize", "toy_high_rate"):  # the last two were WEAK before v0.2 delta 1
            self.assertEqual(body(toy)["verdict"], "NOT_FALSIFIABLE", toy)

    def test_undefined(self):
        for toy in ("toy_undefined_none", "toy_undefined_exc", "toy_bad_return", "toy_dup_ids", "toy_no_study",
                    "toy_components_mismatch", "toy_det_undefined", "toy_import_leak", "toy_leak_open"):
            self.assertEqual(body(toy)["verdict"], "UNDEFINED", toy)


class TestWeakFlagsAreOnlyCapping(unittest.TestCase):
    """Capping flags alone give WEAK, not NOT_FALSIFIABLE (spec section 5.8)."""

    def test_lowpower_has_only_the_target_flag(self):
        self.assertEqual(component("toy_lowpower")["flags"], ["K2_LOW_POWER"])

    def test_highsize_has_only_the_target_flag(self):
        self.assertEqual(component("toy_highsize")["flags"], ["K2_HIGH_SIZE"])

    def test_high_rate_names_the_stream(self):
        self.assertEqual(component("toy_high_rate")["flags"], ["HIGH_RATE:control:leaky"])

    def test_waiver_flag_only(self):
        self.assertEqual(component("toy_waived")["flags"], ["K4_WAIVED"])

    def test_probe_inconclusive_names_probes(self):
        self.assertEqual(component("toy_inconclusive_probe")["flags"],
                         ["K5_INCONCLUSIVE:noise", "K5_INCONCLUSIVE:zeros"])

    def test_inconclusive_premise_does_not_also_say_not_tested(self):
        self.assertEqual(component("toy_inconclusive_premise")["flags"], ["K3_INCONCLUSIVE"])
        self.assertEqual(component("toy_inconclusive_control")["flags"], ["K4_INCONCLUSIVE"])


class TestMandatoryFlagDetails(unittest.TestCase):
    def test_unresolvable_tolerance_only(self):
        c = component("toy_unresolvable_tol")
        self.assertEqual(c["flags"], ["K2_UNRESOLVABLE"])
        self.assertEqual(c["unresolvable"], ["tolerance:eps"])

    def test_unresolvable_premise_also_fails_k3_even_though_it_flips(self):
        c = component("toy_unresolvable_premise")
        self.assertEqual(c["flags"], ["K2_UNRESOLVABLE", "K3_PREMISE_NOT_TESTED"])
        self.assertEqual(c["unresolvable"], ["premise:shift"])
        self.assertEqual(c["counts"]["premise:shift"]["holds"], 0)  # the mutation does flip the outcome

    def test_no_control_flag(self):
        self.assertEqual(component("toy_no_control")["flags"], ["K4_NO_CONTROL"])

    def test_waiver_with_control_still_flagged(self):
        self.assertEqual(component("toy_waived_with_control")["flags"], ["K4_WAIVED"])

    def test_control_as_world_works(self):
        self.assertEqual(body("toy_control_world")["verdict"], "FALSIFIABLE")
        self.assertIn("control:decoy", component("toy_control_world")["counts"])

    def test_assumed_premise_has_no_requirement_but_is_mapped(self):
        self.assertEqual(body("toy_assumed_premise")["verdict"], "FALSIFIABLE")
        self.assertEqual(body("toy_assumed_premise")["premise_map"], {"scale_free": {"mean_gt_1": 0.0}})

    def test_not_tested_premise_keeps_other_checks_clean(self):
        self.assertIn("K3_PREMISE_NOT_TESTED", component("toy_not_tested_premise")["flags"])
        self.assertNotIn("K2_NO_SEPARATION", component("toy_not_tested_premise")["flags"])

    def test_noise_and_degenerate_are_distinct(self):
        self.assertFalse(raised("toy_noise", "K5_HOLDS_ON_DEGENERATE"))
        self.assertFalse(raised("toy_degenerate", "K5_HOLDS_ON_NOISE"))

    def test_null_flag_requires_declared_null(self):
        self.assertNotIn("world:null", component("toy_noise")["counts"])
        self.assertFalse(raised("toy_noise", "K5_HOLDS_ON_NULL"))


class TestK1AndErrors(unittest.TestCase):
    def test_k1_makes_verdict_undefined_and_records_exception_type_only(self):
        c = component("toy_undefined_exc")
        self.assertEqual(c["verdict"], "UNDEFINED")
        self.assertEqual(c["errors"]["world:plus"], {"ValueError": 30})
        self.assertNotIn("secret-detail-12345", repr(body("toy_undefined_exc")))

    def test_counts_record_undefined(self):
        self.assertEqual(component("toy_undefined_none")["counts"]["world:plus"],
                         {"holds": 0, "undefined": 30, "hard_undefined": 0, "n": 30})

    def test_exception_inside_premise_is_recorded(self):
        self.assertEqual(component("toy_inconclusive_premise")["errors"]["premise:broken"], {"RuntimeError": 100})

    def test_exception_inside_control_is_recorded(self):
        self.assertEqual(component("toy_inconclusive_control")["errors"]["control:broken"], {"ArithmeticError": 100})

    def test_load_failures_are_undefined(self):
        self.assertEqual(body("toy_dup_ids")["load_error"]["type"], "StudyError")
        self.assertIn("duplicate", body("toy_dup_ids")["load_error"]["message"])
        self.assertEqual(body("toy_no_study")["load_error"]["type"], "StudyError")
        self.assertEqual(body("toy_dup_ids")["components"], [])


class TestComponents(unittest.TestCase):
    def test_each_component_is_a_separate_subcriterion(self):
        ids = [c["id"] for c in body("toy_components_ok")["components"]]
        self.assertEqual(ids, ["pair:lo", "pair:hi"])
        self.assertEqual(set(body("toy_components_ok")["premise_map"]["shift"]), {"pair:lo", "pair:hi"})

    def test_mismatch_makes_missing_component_undefined(self):
        self.assertEqual(component("toy_components_mismatch", "pair:lo")["verdict"], "FALSIFIABLE")
        self.assertEqual(component("toy_components_mismatch", "pair:hi")["verdict"], "UNDEFINED")
        self.assertEqual(body("toy_components_mismatch")["study_flag_details"]["K7_COMPONENT_MISMATCH"], ["pair"])

    def test_regime_detail(self):
        self.assertEqual(body("toy_regime_uncovered")["study_flag_details"]["K7_REGIME_UNCOVERED"], ["regime_b"])


class TestSeverityOrder(unittest.TestCase):
    def test_study_flag_raises_falsifiable_components(self):
        b = body("toy_regime_uncovered")
        self.assertEqual([c["verdict"] for c in b["components"]], ["FALSIFIABLE"])
        self.assertEqual(b["verdict"], "NOT_FALSIFIABLE")


if __name__ == "__main__":
    unittest.main()
