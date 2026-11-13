"""Individual checks K1-K5 and the verdict mapping on synthetic outcome counts (spec section 5)."""

import unittest

import _helpers  # noqa: F401
from kapi.checks import (
    CAPPING_FLAGS, MANDATORY_FLAGS, STUDY_LEVEL_FLAGS, Context, StreamStats, check_high_rate, check_k1,
    check_k2, check_k3, check_k4, check_k5, component_verdict, study_verdict,
)

N = 100
CTX = Context(deterministic=False, a=0.005, power=0.8, size=0.05)
DET = Context(deterministic=True, a=0.0, power=0.8, size=0.05)


def S(holds, undefined=0, n=N, hard=0):
    return StreamStats(holds, undefined, n, hard)


ALL, NONE = S(N), S(0)
HOLDS_D, FAILS_D, UNDEF_D = S(1, 0, 1), S(0, 0, 1), S(0, 1, 1)


class TestK1(unittest.TestCase):
    """K1 as a failure rule (spec 0.7 section 2.1); the abstention boundaries are in test_spec07.py."""

    def test_flags_hard_undefined_on_plus_minus_null(self):
        # Every UNDEFINED outcome of 0.4.1 was a hard one for this rule: the 0.4.1 behaviour is kept for failures.
        self.assertEqual(check_k1({"world:plus": S(90, 10, hard=10), "world:minus": NONE}), ["K1_UNDEFINED"])
        self.assertEqual(check_k1({"world:plus": ALL, "world:minus": S(0, 1, hard=1)}), ["K1_UNDEFINED"])
        self.assertEqual(check_k1({"world:plus": ALL, "world:minus": NONE, "world:null": S(0, 3, hard=3)}),
                         ["K1_UNDEFINED"])

    def test_abstentions_are_information_not_a_failure(self):
        self.assertEqual(check_k1({"world:plus": S(90, 10), "world:minus": NONE}), ["K1_ABSTAINED:world:plus"])
        self.assertEqual(check_k1({"world:plus": ALL, "world:minus": S(0, 1)}), ["K1_ABSTAINED:world:minus"])

    def test_clean_and_other_streams_ignored(self):
        self.assertEqual(check_k1({"world:plus": ALL, "world:minus": NONE, "probe:noise": S(0, 100)}), [])


class TestK2(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(check_k2(ALL, NONE, CTX, False), [])

    def test_holds_unreachable(self):
        self.assertIn("K2_HOLDS_UNREACHABLE", check_k2(NONE, NONE, CTX, False))

    def test_fails_unreachable(self):
        self.assertIn("K2_FAILS_UNREACHABLE", check_k2(ALL, ALL, CTX, False))
        self.assertNotIn("K2_FAILS_UNREACHABLE", check_k2(ALL, S(99), CTX, False))

    def test_undefined_in_minus_counts_as_fails_reachable(self):
        self.assertNotIn("K2_FAILS_UNREACHABLE", check_k2(ALL, S(0, 100), CTX, False))

    def test_no_separation(self):
        self.assertIn("K2_NO_SEPARATION", check_k2(S(50), S(50), CTX, False))
        self.assertNotIn("K2_NO_SEPARATION", check_k2(S(95), S(2), CTX, False))

    def test_unresolvable_flag_passthrough(self):
        self.assertIn("K2_UNRESOLVABLE", check_k2(ALL, NONE, CTX, True))

    def test_low_power_and_high_size_are_significance_based(self):
        self.assertIn("K2_LOW_POWER", check_k2(S(50), NONE, CTX, False))
        # 75/100: upper bound is above 0.8, so the miss is not significant
        self.assertNotIn("K2_LOW_POWER", check_k2(S(75), NONE, CTX, False))
        self.assertIn("K2_HIGH_SIZE", check_k2(ALL, S(25), CTX, False))
        self.assertNotIn("K2_HIGH_SIZE", check_k2(ALL, S(8), CTX, False))

    def test_deterministic_mode(self):
        self.assertEqual(check_k2(HOLDS_D, FAILS_D, DET, False), [])
        self.assertEqual(check_k2(FAILS_D, FAILS_D, DET, False), ["K2_HOLDS_UNREACHABLE", "K2_NO_SEPARATION"])
        self.assertEqual(check_k2(HOLDS_D, HOLDS_D, DET, False), ["K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION"])
        self.assertEqual(check_k2(UNDEF_D, FAILS_D, DET, False), ["K2_HOLDS_UNREACHABLE", "K2_NO_SEPARATION"])
        self.assertEqual(check_k2(HOLDS_D, UNDEF_D, DET, False), [])  # UNDEFINED in minus counts as not-HOLDS

    def test_high_rate(self):
        streams = {"control:c": S(30), "probe:noise": S(2), "world:null": NONE}
        self.assertEqual(check_high_rate(streams, CTX), ["HIGH_RATE:control:c"])
        self.assertEqual(check_high_rate({"control:c": ALL}, DET), [])  # skipped in deterministic mode


class TestK3(unittest.TestCase):
    def test_tested_premise_must_be_significantly_lower(self):
        self.assertEqual(check_k3(ALL, NONE, "tested", False, CTX), [])
        self.assertEqual(check_k3(ALL, S(90), "tested", False, CTX), ["K3_PREMISE_NOT_TESTED"])

    def test_assumed_premise_has_no_requirement(self):
        self.assertEqual(check_k3(ALL, S(90), "assumed", False, CTX), [])

    def test_inconclusive_replaces_not_tested(self):
        self.assertEqual(check_k3(ALL, S(0, 51), "tested", False, CTX), ["K3_INCONCLUSIVE"])
        self.assertEqual(check_k3(ALL, S(40, 50), "tested", False, CTX), [])  # exactly 50% is not "more than"

    def test_unresolvable_tested_premise_fails_k3(self):
        self.assertEqual(check_k3(ALL, NONE, "tested", True, CTX), ["K3_PREMISE_NOT_TESTED"])
        self.assertEqual(check_k3(ALL, NONE, "assumed", True, CTX), [])

    def test_deterministic(self):
        self.assertEqual(check_k3(HOLDS_D, FAILS_D, "tested", False, DET), [])
        self.assertEqual(check_k3(HOLDS_D, HOLDS_D, "tested", False, DET), ["K3_PREMISE_NOT_TESTED"])
        self.assertEqual(check_k3(HOLDS_D, UNDEF_D, "tested", False, DET), ["K3_INCONCLUSIVE"])


class TestK4(unittest.TestCase):
    def test_no_control_no_waiver(self):
        self.assertEqual(check_k4(ALL, {}, False, CTX), ["K4_NO_CONTROL"])

    def test_waiver(self):
        self.assertEqual(check_k4(ALL, {}, True, CTX), ["K4_WAIVED"])

    def test_control_must_be_significantly_lower(self):
        self.assertEqual(check_k4(ALL, {"control:c": NONE}, False, CTX), [])
        self.assertEqual(check_k4(ALL, {"control:c": S(95)}, False, CTX), ["K4_CONTROL_ALSO_HOLDS"])

    def test_inconclusive_control(self):
        self.assertEqual(check_k4(ALL, {"control:c": S(0, 60)}, False, CTX), ["K4_INCONCLUSIVE"])

    def test_deterministic(self):
        self.assertEqual(check_k4(HOLDS_D, {"control:c": FAILS_D}, False, DET), [])
        self.assertEqual(check_k4(HOLDS_D, {"control:c": HOLDS_D}, False, DET), ["K4_CONTROL_ALSO_HOLDS"])


class TestK5(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(check_k5(ALL, NONE, NONE, NONE, {"shuffle:a,b": NONE}, CTX), [])

    def test_each_probe_flag(self):
        self.assertEqual(check_k5(ALL, ALL, NONE, None, {}, CTX), ["K5_HOLDS_ON_NOISE"])
        self.assertEqual(check_k5(ALL, NONE, ALL, None, {}, CTX), ["K5_HOLDS_ON_DEGENERATE"])
        self.assertEqual(check_k5(ALL, NONE, NONE, ALL, {}, CTX), ["K5_HOLDS_ON_NULL"])
        self.assertEqual(check_k5(ALL, NONE, NONE, None, {"shuffle:a,b": ALL}, CTX), ["K5_HOLDS_ON_SHUFFLE"])

    def test_null_only_checked_when_declared(self):
        self.assertEqual(check_k5(ALL, NONE, NONE, None, {}, CTX), [])

    def test_inconclusive_probes(self):
        self.assertEqual(check_k5(ALL, S(0, 60), NONE, None, {}, CTX), ["K5_INCONCLUSIVE:noise"])
        self.assertEqual(check_k5(ALL, NONE, S(0, 100), None, {}, CTX), ["K5_INCONCLUSIVE:zeros"])
        self.assertEqual(check_k5(ALL, NONE, NONE, None, {"shuffle:a,b": S(0, 99)}, CTX), ["K5_INCONCLUSIVE:shuffle:a,b"])

    def test_deterministic(self):
        self.assertEqual(check_k5(HOLDS_D, FAILS_D, FAILS_D, FAILS_D, {}, DET), [])
        self.assertEqual(check_k5(HOLDS_D, HOLDS_D, FAILS_D, None, {}, DET), ["K5_HOLDS_ON_NOISE"])


class TestVerdictMapping(unittest.TestCase):
    def test_component_mapping(self):
        self.assertEqual(component_verdict([]), "FALSIFIABLE")
        self.assertEqual(component_verdict(["BAD_RETURN"]), "FALSIFIABLE")  # informational only
        self.assertEqual(component_verdict(["K2_LOW_POWER"]), "WEAK")
        self.assertEqual(component_verdict(["HIGH_RATE:control:c"]), "NOT_FALSIFIABLE")  # v0.2 delta 1 (was WEAK)
        self.assertEqual(component_verdict(["K2_HIGH_SIZE"]), "NOT_FALSIFIABLE")  # v0.2 delta 1 (was WEAK)
        self.assertEqual(component_verdict(["K5_INCONCLUSIVE:noise"]), "WEAK")
        self.assertEqual(component_verdict(["K2_LOW_POWER", "K4_NO_CONTROL"]), "NOT_FALSIFIABLE")
        self.assertEqual(component_verdict(["K1_UNDEFINED", "K4_NO_CONTROL"]), "UNDEFINED")

    def test_every_mandatory_flag_gives_not_falsifiable(self):
        for flag in MANDATORY_FLAGS:
            self.assertEqual(component_verdict([flag]), "NOT_FALSIFIABLE", flag)

    def test_every_capping_flag_gives_weak(self):
        for flag in CAPPING_FLAGS:
            self.assertEqual(component_verdict([flag]), "WEAK", flag)

    def test_flag_sets_match_spec_counts(self):
        self.assertEqual(len(MANDATORY_FLAGS), 12)
        self.assertEqual(len(CAPPING_FLAGS), 4)
        self.assertEqual(len(STUDY_LEVEL_FLAGS), 5)

    def test_study_verdict_is_worst_component(self):
        self.assertEqual(study_verdict(["FALSIFIABLE", "WEAK"], []), "WEAK")
        self.assertEqual(study_verdict(["FALSIFIABLE", "NOT_FALSIFIABLE", "WEAK"], []), "NOT_FALSIFIABLE")
        self.assertEqual(study_verdict(["WEAK", "UNDEFINED"], []), "UNDEFINED")

    def test_study_flags_raise_to_at_least_not_falsifiable(self):
        for flag in STUDY_LEVEL_FLAGS:
            self.assertEqual(study_verdict(["FALSIFIABLE"], [flag]), "NOT_FALSIFIABLE", flag)
        self.assertEqual(study_verdict(["UNDEFINED"], ["K6_LEAK_ATTEMPT"]), "UNDEFINED")


if __name__ == "__main__":
    unittest.main()
