"""Spec 0.7 section 5, the two tests marked (G) "written before the code" for Truth_Gate 0.5.

* **Metamorphic None = False.**  For fixture studies whose criterion abstains (``tests/toy_studies_spec07/abs_*.py``),
  the twin study in which every ``None`` the criterion returns is replaced by ``False`` must give identical flags
  except ``K1_*``, ``K3_INCONCLUSIVE``, ``K4_INCONCLUSIVE``, ``K5_INCONCLUSIVE:*`` and ``K8_*``, in stochastic and in
  deterministic mode, and the verdict of the ``None`` study must be the one implied by its remaining flags.
* **Gaming.**  The five cases of section 5 (``gaming_*.py`` and ``abs_probes.py``).

These tests are written for the 0.5 behaviour (abstention counted as no claim).  Against 0.4.1 the flag parts pass and
the verdict parts fail wherever K1 still turns an abstention into UNDEFINED; that is expected.  The fixtures use small
budgets (40 or 100 samples): the metamorphic test compares flags between twins that count the same HOLDS, so it is
valid at any n, and the gaming cases that assert a statistic (a, c, d) state in a comment why their n is enough.
"""

import os
import shutil
import tempfile
import unittest

import _helpers
from truth_gate import run_gate
from truth_gate.stats import wilson_lower

FIXTURES = os.path.join(_helpers.ROOT, "tests", "toy_studies_spec07")

_RUNS: dict = {}
_TWIN_DIR: list = []

# --------------------------------------------------------------------------
# Running studies (cached per process) and building the None -> False twin
# --------------------------------------------------------------------------

ABSTAIN_NONE = "ABSTAIN = None\n"
ABSTAIN_FALSE = "ABSTAIN = False\n"


def setUpModule():
    _TWIN_DIR.append(tempfile.mkdtemp(prefix="spec07_twins_"))


def tearDownModule():
    for directory in _TWIN_DIR:
        shutil.rmtree(directory, ignore_errors=True)
    _TWIN_DIR.clear()
    _RUNS.clear()


def fixture_path(name: str) -> str:
    return os.path.join(FIXTURES, name + ".py")


def twin_path(name: str) -> str:
    """Write the twin of a fixture, with ``ABSTAIN = False`` instead of ``ABSTAIN = None``, and return its path."""
    with open(fixture_path(name), "r", encoding="utf-8") as handle:
        source = handle.read()
    assert source.count(ABSTAIN_NONE) == 1, f"{name}: expected exactly one {ABSTAIN_NONE.strip()!r} line"
    path = os.path.join(_TWIN_DIR[0], name + ".py")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(source.replace(ABSTAIN_NONE, ABSTAIN_FALSE))
    return path


def gate_body(path: str) -> dict:
    if path not in _RUNS:
        _RUNS[path] = run_gate(path)["body"]
    body = _RUNS[path]
    assert body["load_error"] is None, f"{path}: {body['load_error']}"
    return body


def fixture_body(name: str) -> dict:
    return gate_body(fixture_path(name))


def twin_body(name: str) -> dict:
    return gate_body(twin_path(name))


def by_id(body: dict) -> dict:
    return {c["id"]: c for c in body["components"]}


def single(body: dict) -> dict:
    assert len(body["components"]) == 1
    return body["components"][0]


# --------------------------------------------------------------------------
# Metamorphic None = False
# --------------------------------------------------------------------------

def excluded(flag: str) -> bool:
    """Flags the metamorphic statement leaves out: K1_*, K3/K4_INCONCLUSIVE, K5_INCONCLUSIVE:*, K8_*."""
    return (
        flag.startswith("K1_")
        or flag in ("K3_INCONCLUSIVE", "K4_INCONCLUSIVE")
        or flag.startswith("K5_INCONCLUSIVE:")
        or flag.startswith("K8_")
    )


# An independent copy of the verdict cascade of spec 0.7 / 0.5 section 5.8 (the test must not use the engine's own
# tables to decide what the engine should say).
_MANDATORY = frozenset({
    "K2_HOLDS_UNREACHABLE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K2_UNRESOLVABLE", "K2_HIGH_SIZE",
    "K3_PREMISE_NOT_TESTED", "K4_NO_CONTROL", "K4_CONTROL_ALSO_HOLDS",
    "K5_HOLDS_ON_NOISE", "K5_HOLDS_ON_DEGENERATE", "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE",
    "K8_NOT_INVARIANT",
})
_MANDATORY_PREFIXES = ("HIGH_RATE:",)
_UNTESTED = frozenset({"K2_MINUS_IDENTICAL"})
_CAPPING = frozenset({"K2_LOW_POWER", "K3_INCONCLUSIVE", "K4_WAIVED", "K4_INCONCLUSIVE", "SUGGESTED_UNREVIEWED",
                      "K8_INCONCLUSIVE"})
_CAPPING_PREFIXES = ("K5_INCONCLUSIVE:", "K1_ABSTAINED_MAJORITY:")
# Information flags (never enter a verdict): K1_ABSTAINED:<stream>, BAD_RETURN, K2_MINUS_UNREAD, K8_SOME_CHANGES.
_SEVERITY = ("FALSIFIABLE", "WEAK", "UNTESTED", "NOT_FALSIFIABLE", "UNDEFINED")


def implied_verdict(flags, k1_undefined_expected: bool) -> str:
    """Verdict of a component from its flags.  ``K1_UNDEFINED`` is legitimate only where the fixture says so."""
    if k1_undefined_expected:
        return "UNDEFINED"
    flags = {f for f in flags if f != "K1_UNDEFINED"}  # a K1_UNDEFINED the fixture does not justify is not implied
    if any(f in _MANDATORY or f.startswith(_MANDATORY_PREFIXES) for f in flags):
        return "NOT_FALSIFIABLE"
    if flags & _UNTESTED:
        return "UNTESTED"
    if any(f in _CAPPING or f.startswith(_CAPPING_PREFIXES) for f in flags):
        return "WEAK"
    return "FALSIFIABLE"


# name -> (streams on which every component of the None study must abstain at least once,
#          whether K1_UNDEFINED is justified: the abstentions are more than half of the plus samples)
STOCHASTIC_FIXTURES = {
    "abs_minus": (("world:minus",), False),
    "abs_plus_below_half": (("world:plus",), False),  # 30% of plus, below one half
    "abs_null": (("world:null",), False),
    "abs_probes": (("probe:noise",), False),
    "abs_components": (("world:minus",), False),  # a criterion with components, abstaining through dict values
}
DETERMINISTIC_FIXTURES = {
    "det_abs_minus": (("world:minus",), False),
    "det_abs_null": (("world:null",), False),
    "det_abs_probes": (("probe:noise",), False),
    "det_abs_plus": (("world:plus",), True),  # the single plus sample abstains: rate 1 > one half
}
ALL_FIXTURES = {**STOCHASTIC_FIXTURES, **DETERMINISTIC_FIXTURES}


def _make_metamorphic_tests():
    ns = {}
    for name, (streams, k1_expected) in ALL_FIXTURES.items():

        def flags_identical(self, name=name, streams=streams):
            abstaining, twin = fixture_body(name), twin_body(name)
            self.assertEqual(abstaining["mode"], twin["mode"])
            self.assertEqual(sorted(by_id(abstaining)), sorted(by_id(twin)))
            for cid, comp in by_id(abstaining).items():
                other = by_id(twin)[cid]
                # The fixture really abstains where it says, and the twin really never does.
                for stream in streams:
                    self.assertGreater(comp["counts"][stream]["undefined"], 0, f"{cid}@{stream}")
                for stream, counts in other["counts"].items():
                    self.assertEqual(counts["undefined"], 0, f"twin {cid}@{stream}")
                # None and False are both not-HOLDS: the HOLDS counts and the bounds do not move.
                self.assertEqual({s: c["holds"] for s, c in comp["counts"].items()},
                                 {s: c["holds"] for s, c in other["counts"].items()}, cid)
                self.assertEqual({s: c["n"] for s, c in comp["counts"].items()},
                                 {s: c["n"] for s, c in other["counts"].items()}, cid)
                self.assertEqual(comp["bounds"], other["bounds"], cid)
                kept = {f for f in comp["flags"] if not excluded(f)}
                self.assertEqual(kept, {f for f in other["flags"] if not excluded(f)},
                                 f"{cid}: flags differ outside the excluded families")
            self.assertEqual(abstaining["study_flags"], twin["study_flags"])

        def verdict_implied(self, name=name, k1_expected=k1_expected):
            abstaining, twin = fixture_body(name), twin_body(name)
            for cid, comp in by_id(abstaining).items():
                # The twin has no abstention: its verdict is exactly the cascade of its flags.
                self.assertEqual(by_id(twin)[cid]["verdict"], implied_verdict(by_id(twin)[cid]["flags"], False), cid)
                # The abstaining study: the cascade of the remaining flags (K1_UNDEFINED only if the fixture justifies it).
                self.assertEqual(comp["verdict"], implied_verdict(comp["flags"], k1_expected),
                                 f"{cid}: flags {comp['flags']}")
            component_verdicts = [c["verdict"] for c in abstaining["components"]]
            worst = max(_SEVERITY.index(v) for v in component_verdicts)
            if abstaining["study_flags"]:
                worst = max(worst, _SEVERITY.index("NOT_FALSIFIABLE"))
            self.assertEqual(abstaining["verdict"], _SEVERITY[worst])

        ns[f"test_flags_identical__{name}"] = flags_identical
        ns[f"test_verdict_implied__{name}"] = verdict_implied
    return ns


TestMetamorphicNoneIsFalse = type("TestMetamorphicNoneIsFalse", (unittest.TestCase,), _make_metamorphic_tests())
TestMetamorphicNoneIsFalse.__doc__ = (
    "Replacing every None the criterion returns by False changes no flag outside K1_*, K3/K4_INCONCLUSIVE, "
    "K5_INCONCLUSIVE:* and K8_*, and the verdict follows from the remaining flags (spec 0.7 section 5, (G))."
)


class TestMetamorphicFixturesAreSound(unittest.TestCase):
    """The twin is built by one substitution; it must not silently be the same study."""

    def test_every_fixture_has_exactly_one_abstain_line_and_the_twin_differs(self):
        for name in ALL_FIXTURES:
            with open(fixture_path(name), "r", encoding="utf-8") as handle:
                source = handle.read()
            self.assertEqual(source.count(ABSTAIN_NONE), 1, name)
            with open(twin_path(name), "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), source.replace(ABSTAIN_NONE, ABSTAIN_FALSE), name)

    def test_the_fixtures_cover_the_required_abstention_sites_and_both_modes(self):
        sites = {stream for streams, _ in ALL_FIXTURES.values() for stream in streams}
        self.assertEqual(sites, {"world:plus", "world:minus", "world:null", "probe:noise"})
        for name in DETERMINISTIC_FIXTURES:
            self.assertEqual(fixture_body(name)["components"][0]["counts"]["world:plus"]["n"], 1, name)
        for name in STOCHASTIC_FIXTURES:
            self.assertGreater(fixture_body(name)["components"][0]["counts"]["world:plus"]["n"], 1, name)

    def test_plus_fixture_abstains_below_one_half_in_the_stochastic_case(self):
        counts = single(fixture_body("abs_plus_below_half"))["counts"]["world:plus"]
        self.assertGreater(counts["undefined"], 0)
        self.assertLessEqual(2 * counts["undefined"], counts["n"])


# --------------------------------------------------------------------------
# Gaming cases of section 5
# --------------------------------------------------------------------------

class TestGamingCases(unittest.TestCase):

    # (a) faulty criterion: HOLDS on 15% of minus and None on another 15% -> K2_HIGH_SIZE
    #
    # Arithmetic.  gaming_size.py has one criterion, one control, no premise and no null world, so the family has
    # m = 1 (separation) + 1 (control) + 2 (noise, zeros) = 4 comparisons and the per-bound level is
    # a = alpha_family / (2 m) = 0.05 / 8 = 0.00625 (z = 2.498).  With the default budget n = 200, 15% is 30 HOLDS and the
    # lower Wilson bound of 30/200 at that level is 0.0976, above the declared size 0.05; the bound stays above 0.05
    # down to 18 HOLDS (9%), so the flag does not depend on the realised draw (this seed: 37 HOLDS, 28 None).  The
    # abstentions count as not-HOLDS, so they cannot lower the HOLDS count that K2_HIGH_SIZE reads: 0.5 must still raise
    # it.  n is the default (200): the realised rates vary by about 2.5 percentage points (one sd), and 200 keeps
    # the whole plausible range of the 15% above the 9% needed.

    def test_a_faulty_criterion_with_15_percent_holds_and_15_percent_none_gets_k2_high_size(self):
        body = fixture_body("gaming_size")
        comp = single(body)
        counts = comp["counts"]["world:minus"]
        self.assertEqual(body["m_comparisons"], 4)
        self.assertEqual(counts["n"], 200)
        self.assertAlmostEqual(body["alpha_per_bound"], 0.05 / 8)
        # the fixture does what the case says: about 15% HOLDS and about 15% None on minus
        self.assertTrue(0.10 * counts["n"] <= counts["holds"] <= 0.20 * counts["n"], counts)
        self.assertTrue(0.10 * counts["n"] <= counts["undefined"] <= 0.20 * counts["n"], counts)
        # the statistic the flag reads
        self.assertGreater(wilson_lower(counts["holds"], counts["n"], body["alpha_per_bound"]), 0.05)
        self.assertIn("K2_HIGH_SIZE", comp["flags"])

    def test_a_the_flag_is_mandatory_so_the_verdict_is_not_falsifiable(self):
        comp = single(fixture_body("gaming_size"))
        self.assertEqual(comp["verdict"], "NOT_FALSIFIABLE")
        self.assertNotIn("K1_UNDEFINED", comp["flags"])

    # (b) a criterion that returns None on every noise-probe sample: K5_INCONCLUSIVE:noise, not a clean K5 pass

    def test_b_none_on_every_noise_sample_is_inconclusive_not_a_clean_pass(self):
        comp = single(fixture_body("abs_probes"))
        noise = comp["counts"]["probe:noise"]
        self.assertEqual(noise["undefined"], noise["n"])  # every noise-probe sample abstained
        self.assertIn("K5_INCONCLUSIVE:noise", comp["flags"])
        self.assertNotIn("K5_HOLDS_ON_NOISE", comp["flags"])
        self.assertEqual(comp["verdict"], "WEAK")  # capped, not FALSIFIABLE
        self.assertNotEqual(comp["verdict"], "FALSIFIABLE")

    # (c) 40% abstention and 60% FAILS on plus: NOT_FALSIFIABLE with K2_HOLDS_UNREACHABLE, not UNDEFINED
    #
    # gaming_plus_fails.py abstains for u < 0.4 on plus; at n = 100 that is about 40 samples (this seed: 45), and
    # the case needs 2 * a_plus <= n (at most 50), which holds with a margin of 5 samples (one sd is 4.9).  Zero HOLDS
    # is K2_HOLDS_UNREACHABLE whatever the abstention count.

    def test_c_forty_percent_abstention_and_no_holds_on_plus_gets_k2_holds_unreachable(self):
        comp = single(fixture_body("gaming_plus_fails"))
        plus = comp["counts"]["world:plus"]
        self.assertEqual(plus["n"], 100)
        self.assertEqual(plus["holds"], 0)
        self.assertTrue(30 <= plus["undefined"] <= 50, plus)  # about 40%, at most one half
        self.assertIn("K2_HOLDS_UNREACHABLE", comp["flags"])

    def test_c_the_verdict_is_not_falsifiable_not_undefined(self):
        body = fixture_body("gaming_plus_fails")
        comp = single(body)
        self.assertNotIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(body["verdict"], "NOT_FALSIFIABLE")

    # (d) 60% abstention on plus: UNDEFINED with K1_UNDEFINED
    #
    # gaming_plus_abstain60.py abstains for u < 0.6 on plus; at n = 100 that is about 60 samples (this seed: 62), and
    # the case needs 2 * a_plus > n (at least 51), which holds with a margin of 11 samples.  There is no exception on
    # plus: the UNDEFINED is the plus-majority rule, not a failure.

    def test_d_sixty_percent_abstention_on_plus_is_undefined_with_k1(self):
        body = fixture_body("gaming_plus_abstain60")
        comp = single(body)
        plus = comp["counts"]["world:plus"]
        self.assertEqual(plus["n"], 100)
        self.assertTrue(2 * plus["undefined"] > plus["n"], plus)  # more than one half
        self.assertIn("K1_UNDEFINED", comp["flags"])
        self.assertEqual(comp["verdict"], "UNDEFINED")
        self.assertEqual(body["verdict"], "UNDEFINED")

    def test_d_the_abstentions_are_not_failures(self):
        comp = single(fixture_body("gaming_plus_abstain60"))
        self.assertEqual(comp["errors"].get("world:plus", {}), {})  # no exception, no BAD_RETURN: all of it is None
        self.assertNotIn("BAD_RETURN", comp["flags"])

    # (e) a minus world of all NaN, criterion returns None on non-finite input: at most WEAK
    #
    # Every one of the 40 minus samples abstains, so a_minus = n and 2 * a_minus > n whatever the draw.

    def test_e_an_all_nan_minus_world_is_capped_by_k1_abstained_majority(self):
        comp = single(fixture_body("gaming_nan_minus"))
        minus = comp["counts"]["world:minus"]
        self.assertEqual(minus["undefined"], minus["n"])
        self.assertEqual(minus["holds"], 0)
        self.assertIn("K1_ABSTAINED_MAJORITY:world:minus", comp["flags"])

    def test_e_the_verdict_is_at_most_weak(self):
        body = fixture_body("gaming_nan_minus")
        comp = single(body)
        self.assertNotEqual(comp["verdict"], "FALSIFIABLE")
        self.assertEqual(comp["verdict"], "WEAK")  # no other flag: the cap is the only thing in the way
        self.assertEqual(body["verdict"], "WEAK")


if __name__ == "__main__":
    unittest.main()
