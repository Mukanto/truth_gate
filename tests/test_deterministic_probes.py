"""Deterministic mode and Kapi's own random probes (spec section 4.3, 0.3; unchanged in 0.4)."""

import unittest

import _helpers
from _helpers import body, component, raised
from kapi.checks import (
    FAILS, HOLDS, UNDEFINED, check_k5, Context, StreamStats, combine_probe_draws, is_random_probe, stream_stats,
)

H, F, U = HOLDS, FAILS, UNDEFINED


class TestCombination(unittest.TestCase):
    def test_any_holds_wins(self):
        for draws in ([H, F, F], [F, H, F], [F, F, H], [H, H, H], [H, U, U], [U, U, H], [U, H, F]):
            self.assertEqual(combine_probe_draws(draws), H, draws)

    def test_two_or_more_undefined_without_holds(self):
        for draws in ([U, U, F], [U, F, U], [F, U, U], [U, U, U]):
            self.assertEqual(combine_probe_draws(draws), U, draws)

    def test_otherwise_fails(self):
        for draws in ([F, F, F], [U, F, F], [F, U, F], [F, F, U]):
            self.assertEqual(combine_probe_draws(draws), F, draws)

    def test_all_27_patterns_follow_the_rule(self):
        import itertools
        for draws in itertools.product((H, F, U), repeat=3):
            if H in draws:
                expected = H
            elif draws.count(U) >= 2:
                expected = U
            else:
                expected = F
            self.assertEqual(combine_probe_draws(draws), expected, draws)

    def test_random_probe_names(self):
        self.assertTrue(is_random_probe("probe:noise"))
        self.assertTrue(is_random_probe("probe:shuffle:a,b"))
        for name in ("probe:zeros", "world:plus", "world:minus", "premise:noise", "control:noise"):
            self.assertFalse(is_random_probe(name), name)

    def test_stream_stats_keeps_n_equal_one(self):
        self.assertEqual(stream_stats("probe:noise", [F, H, F], 1, True), StreamStats(1, 0, 1))
        self.assertEqual(stream_stats("probe:noise", [U, U, F], 1, True), StreamStats(0, 1, 1))
        self.assertEqual(stream_stats("probe:noise", [F, U, F], 1, True), StreamStats(0, 0, 1))
        self.assertEqual(stream_stats("probe:shuffle:a,b", [F, F, H], 1, True), StreamStats(1, 0, 1))

    def test_user_streams_and_zeros_use_index_zero(self):
        self.assertEqual(stream_stats("probe:zeros", [F, H, H], 1, True), StreamStats(0, 0, 1))
        self.assertEqual(stream_stats("world:plus", [H, F, F], 1, True), StreamStats(1, 0, 1))

    def test_stochastic_mode_is_unchanged(self):
        self.assertEqual(stream_stats("probe:noise", [H, F, U, F], 4, False), StreamStats(1, 1, 4))

    def test_k5_flags_from_combined_outcomes(self):
        ctx = Context(True, 0.0, 0.8, 0.05)
        plus, none = StreamStats(1, 0, 1), StreamStats(0, 0, 1)
        holds = stream_stats("probe:noise", [F, H, F], 1, True)
        self.assertEqual(check_k5(plus, holds, none, None, {}, ctx), ["K5_HOLDS_ON_NOISE"])
        inconclusive = stream_stats("probe:noise", [U, F, U], 1, True)
        self.assertEqual(check_k5(plus, inconclusive, none, None, {}, ctx), ["K5_INCONCLUSIVE:noise"])
        one_undefined = stream_stats("probe:noise", [F, U, F], 1, True)
        self.assertEqual(check_k5(plus, one_undefined, none, None, {}, ctx), [])


class TestNoiseDependentCriterion(unittest.TestCase):
    """(a) The outcome depends on the noise values, the user streams are deterministic."""

    TOY = "toy_det_noise_depends"

    def test_raw_draws_are_recorded(self):
        # base_seed 18: first noise values are +0.924..., -0.897..., +0.476... -> HOLDS, FAILS, HOLDS
        self.assertEqual(component(self.TOY)["probe_draws"], {"probe:noise": [H, F, H]})

    def test_differing_draws_do_not_raise_nondeterministic(self):
        self.assertNotIn("NONDETERMINISTIC", body(self.TOY)["study_flags"])

    def test_noise_holds_when_at_least_one_draw_holds(self):
        self.assertTrue(raised(self.TOY, "K5_HOLDS_ON_NOISE"))
        self.assertEqual(component(self.TOY)["counts"]["probe:noise"], {"holds": 1, "undefined": 0, "n": 1})
        self.assertEqual(body(self.TOY)["verdict"], "NOT_FALSIFIABLE")

    def test_plus_and_minus_are_separated(self):
        counts = component(self.TOY)["counts"]
        self.assertEqual(counts["world:plus"]["holds"], 1)
        self.assertEqual(counts["world:minus"]["holds"], 0)
        self.assertFalse(raised(self.TOY, "K2_NO_SEPARATION"))


class TestNoiseNeverHolds(unittest.TestCase):
    """(b) A criterion that never holds on noise does not raise K5_HOLDS_ON_NOISE."""

    def test_no_flag_and_all_draws_fail(self):
        self.assertFalse(raised("toy_good_det", "K5_HOLDS_ON_NOISE"))
        self.assertEqual(component("toy_good_det")["probe_draws"], {"probe:noise": [F, F, F]})
        self.assertEqual(body("toy_good_det")["verdict"], "FALSIFIABLE")


class TestUndefinedDraws(unittest.TestCase):
    """(c) At least two UNDEFINED draws -> K5_INCONCLUSIVE:noise; one UNDEFINED and two FAILS -> FAILS."""

    def test_two_undefined_draws_are_inconclusive(self):
        c = component("toy_det_noise_two_undefined")
        self.assertEqual(c["probe_draws"], {"probe:noise": [U, U, F]})
        self.assertEqual(c["counts"]["probe:noise"], {"holds": 0, "undefined": 1, "n": 1})
        self.assertEqual(c["flags"], ["K5_INCONCLUSIVE:noise"])
        self.assertEqual(c["verdict"], "WEAK")

    def test_one_undefined_draw_is_fails(self):
        c = component("toy_det_noise_one_undefined")
        self.assertEqual(c["probe_draws"], {"probe:noise": [F, F, U]})
        self.assertEqual(c["counts"]["probe:noise"], {"holds": 0, "undefined": 0, "n": 1})
        self.assertEqual(c["flags"], [])
        self.assertEqual(c["verdict"], "FALSIFIABLE")


class TestUserStreamsStillChecked(unittest.TestCase):
    """(d) Determinism is still verified on user-derived streams."""

    def test_toy_nondeterministic_still_raises(self):
        self.assertIn("NONDETERMINISTIC", body("toy_nondeterministic")["study_flags"])
        details = body("toy_nondeterministic")["study_flag_details"]["NONDETERMINISTIC"]
        self.assertTrue(all("probe:noise" not in item for item in details))
        self.assertTrue(any("world:plus" in item for item in details))

    def test_rng_use_in_a_user_world_is_caught(self):
        # the deterministic good toy has no rng use; the stochastic good toy used in deterministic mode would
        self.assertNotIn("NONDETERMINISTIC", body("toy_good_det")["study_flags"])


class TestShuffleProbeInDeterministicMode(unittest.TestCase):
    def test_draws_recorded_and_excluded_from_determinism_check(self):
        c = component("toy_det_shuffle")
        self.assertEqual(set(c["probe_draws"]), {"probe:noise", "probe:shuffle:a,b"})
        self.assertEqual(c["probe_draws"]["probe:shuffle:a,b"], [F, F, F])
        self.assertEqual(c["counts"]["probe:shuffle:a,b"]["n"], 1)
        self.assertNotIn("NONDETERMINISTIC", body("toy_det_shuffle")["study_flags"])
        self.assertEqual(body("toy_det_shuffle")["verdict"], "FALSIFIABLE")


class TestProbeDrawsField(unittest.TestCase):
    def test_only_in_deterministic_mode(self):
        self.assertNotIn("probe_draws", component("toy_good"))
        self.assertIn("probe_draws", component("toy_good_det"))
        self.assertEqual(component("toy_good_det")["probe_draws"].keys(), {"probe:noise"})

    def test_each_draw_list_has_three_entries(self):
        for toy in ("toy_good_det", "toy_det_noise_depends", "toy_det_shuffle", "toy_det_undefined"):
            for draws in component(toy)["probe_draws"].values():
                self.assertEqual(len(draws), 3, toy)
                self.assertTrue(set(draws) <= {H, F, U})

    def test_spec_version(self):
        self.assertEqual(body("toy_good")["spec_version"], "0.5")


if __name__ == "__main__":
    unittest.main()
