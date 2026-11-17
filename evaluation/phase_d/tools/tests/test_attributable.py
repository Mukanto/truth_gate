import json
import os
import re
import tempfile
import unittest

import common
from attributable import classify, fisher_greater, streams_of

PC_CERTS = os.path.join(common.PC, "run", "certs", "v050")
PC_EXPECTED = os.path.join(common.PC, "EXPECTED_FLAGS.json")
FIXTURE_OUTPUT = os.path.join(common.WORK, "..", "fixture_attributable_pc_output.txt")

PB_DETECTED = {"B2-01", "B2-02", "B2-08", "B2-09", "B2-10", "B2-11", "B2-12",
               "B3-01", "B3-04", "B3-05", "B3-06", "B3-08", "B3-09", "B3-11", "B3-12"}
ATTRIBUTABLE = {"B2-01", "B2-02", "B2-12", "B3-01", "B3-04", "B3-05", "B3-06", "B3-08", "B3-09", "B3-11"}
ATTRIBUTABLE_DECLARED = ATTRIBUTABLE - {"B3-04", "B3-05"}
NOT_ATTRIBUTABLE = {"B2-08", "B2-09", "B2-10", "B2-11", "B3-12"}


def body(verdict, flags, counts, bounds=None, hard=None):
    """The part of a gate certificate body that the rule reads: one component with flags, counts and bounds.

    ``counts`` maps a stream to (holds, n); ``bounds`` maps a stream to (lower, upper); ``hard`` maps a stream to its
    hard_undefined count (default 0, as the gate writes it).
    """
    hard = hard or {}
    comp = {"id": "C", "flags": list(flags),
            "counts": {s: {"holds": h, "undefined": hard.get(s, 0), "hard_undefined": hard.get(s, 0), "n": n}
                       for s, (h, n) in counts.items()},
            "bounds": {s: {"lower": lo, "upper": up} for s, (lo, up) in (bounds or {}).items()}}
    return {"verdict": verdict, "load_error": None, "components": [comp]}


def load_error_body():
    """The body of a study that failed to load, as truth_gate/certificate.py writes it."""
    return {"verdict": "UNDEFINED", "components": [], "load_error": {"type": "SyntaxError", "message": "bad"}}


class FisherTests(unittest.TestCase):
    def test_hand_checked_values(self):
        # a = 86 of 200 against b = 47 of 200 (B2-08, world:minus): the value of the fixture file
        self.assertAlmostEqual(fisher_greater(86, 200, 47, 200), 2.53e-05, delta=0.01e-05)
        # 3 of 3 against 0 of 3: only the extreme table, 1 / C(6,3) = 1/20
        self.assertEqual(fisher_greater(3, 3, 0, 3), 1 / 20)
        # 2 of 2 against 0 of 2: 1 / C(4,2)
        self.assertEqual(fisher_greater(2, 2, 0, 2), 1 / 6)
        # 1 of 2 against 0 of 2: tables with >= 1 success in group 1 given 1 success in all: 2 of 4 placements
        self.assertEqual(fisher_greater(1, 2, 0, 2), 0.5)
        # 4 of 5 against 1 of 5: (C(5,4) C(5,1) + C(5,5) C(5,0)) / C(10,5) = 26/252
        self.assertAlmostEqual(fisher_greater(4, 5, 1, 5), 26 / 252, places=15)
        # equal counts: p is large; no successes anywhere: p = 1
        self.assertEqual(fisher_greater(0, 5, 0, 5), 1.0)
        self.assertGreater(fisher_greater(5, 10, 5, 10), 0.5)
        # unequal group sizes: 3 of 4 against 0 of 6: C(4,3) C(6,0) + C(4,... ) -> only x = 3 with k = 3: 4/C(10,3)
        self.assertEqual(fisher_greater(3, 4, 0, 6), 4 / 120)

    def test_exact_for_large_counts(self):
        p = fisher_greater(200, 200, 0, 200)
        self.assertAlmostEqual(p, 9.71e-120 / 1, delta=0.01e-120)  # B3-08 in the fixture file
        self.assertGreater(p, 0)

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            fisher_greater(5, 4, 0, 4)


class StreamMapTests(unittest.TestCase):
    def test_map(self):
        counts = {"world:plus": 1, "world:minus": 1, "probe:noise": 1, "probe:zeros": 1, "control:a": 1, "control:b": 1,
                  "probe:shuffle:u,v": 1, "probe:shuffle:u,w": 1, "world:null": 1}
        # plus lower bound 0.8: control a (upper 0.5) and shuffle u,w (upper 0.3) are significantly lower (no flag);
        # control b (upper 0.9) and shuffle u,v (upper 0.8, equal to the lower bound) are not.
        bounds = {"world:plus": {"lower": 0.8, "upper": 1.0}, "control:a": {"lower": 0.3, "upper": 0.5},
                  "control:b": {"lower": 0.6, "upper": 0.9}, "probe:shuffle:u,v": {"lower": 0.5, "upper": 0.8},
                  "probe:shuffle:u,w": {"lower": 0.1, "upper": 0.3}}
        self.assertEqual(streams_of("K2_HIGH_SIZE", counts, bounds), ["world:minus"])
        self.assertEqual(streams_of("K2_FAILS_UNREACHABLE", counts, bounds), ["world:minus"])
        self.assertEqual(streams_of("K5_HOLDS_ON_NOISE", counts, bounds), ["probe:noise"])
        self.assertEqual(streams_of("HIGH_RATE:probe:noise", counts, bounds), ["probe:noise"])
        self.assertEqual(streams_of("K5_HOLDS_ON_NULL", counts, bounds), ["world:null"])
        self.assertEqual(streams_of("HIGH_RATE:world:null", counts, bounds), ["world:null"])
        self.assertEqual(streams_of("K5_HOLDS_ON_SHUFFLE", counts, bounds), ["probe:shuffle:u,v"])
        self.assertEqual(streams_of("K4_CONTROL_ALSO_HOLDS", counts, bounds), ["control:b"])
        self.assertEqual(streams_of("HIGH_RATE:control:a", counts, bounds), ["control:a"])
        self.assertEqual(streams_of("HIGH_RATE:probe:shuffle:u,v", counts, bounds), ["probe:shuffle:u,v"])
        for flag in ("K2_NO_SEPARATION", "K5_HOLDS_ON_DEGENERATE", "K5_INCONCLUSIVE:zeros", "K1_UNDEFINED", "BAD_RETURN"):
            self.assertEqual(streams_of(flag, counts, bounds), [])

    def test_k4_and_shuffle_need_bounds(self):
        counts = {"world:plus": 1, "control:a": 1, "probe:shuffle:u,v": 1}
        for bounds in (None, {}):  # a deterministic-mode certificate has no bounds
            self.assertEqual(streams_of("K4_CONTROL_ALSO_HOLDS", counts, bounds), [])
            self.assertEqual(streams_of("K5_HOLDS_ON_SHUFFLE", counts, bounds), [])
        self.assertEqual(streams_of("K4_CONTROL_ALSO_HOLDS", counts, {"world:plus": {"lower": 0.5, "upper": 1.0}}), [])


class ClassifyTests(unittest.TestCase):
    def setUp(self):
        self.faulty_counts = {"world:plus": (180, 200), "world:minus": (60, 200), "probe:noise": (80, 200),
                              "control:perm": (70, 200)}

    def test_declared_and_generic(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:probe:noise", "K5_HOLDS_ON_NOISE"], self.faulty_counts)
        x = body("FALSIFIABLE", [], {"world:plus": (180, 200), "world:minus": (8, 200), "probe:noise": (3, 200),
                                     "control:perm": (4, 200)})
        r = classify(f, x, ["K2_HIGH_SIZE", "K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"])
        self.assertTrue(r["pb_detected"] and r["attributable"] and r["generic"] and r["declared"] and r["draft1_rule"])
        self.assertEqual({q["stream"] for q in r["qualifying"]}, {"world:minus", "probe:noise"})

    def test_fixed_flag_on_the_stream_blocks_it(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], self.faulty_counts)
        x = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {**self.faulty_counts, "world:minus": (30, 200)})
        r = classify(f, x, ["K2_HIGH_SIZE"])
        self.assertTrue(r["pb_detected"])
        self.assertFalse(r["attributable"])
        self.assertTrue(any("fixed-flagged" in s for s in r["reasons"]))

    def test_fisher_condition(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (22, 200)})
        x = body("FALSIFIABLE", [], {"world:minus": (15, 200)})  # p about 0.15
        r = classify(f, x, ["K2_HIGH_SIZE"])
        self.assertFalse(r["attributable"])
        x = body("FALSIFIABLE", [], {"world:minus": (8, 200)})  # p < 0.05
        self.assertTrue(classify(f, x, ["K2_HIGH_SIZE"])["attributable"])

    def test_declared_only_and_generic_only(self):
        x = body("FALSIFIABLE", [], {"world:minus": (5, 200), "probe:noise": (5, 200)})
        f1 = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (60, 200), "probe:noise": (5, 200)})
        r1 = classify(f1, x, ["K2_HIGH_SIZE"])
        self.assertTrue(r1["declared"] and not r1["generic"])
        f2 = body("NOT_FALSIFIABLE", ["HIGH_RATE:probe:noise"], {"world:minus": (5, 200), "probe:noise": (60, 200)})
        r2 = classify(f2, x, ["HIGH_RATE:probe:noise"])
        self.assertTrue(r2["generic"] and not r2["declared"] and r2["attributable"])

    def test_not_expected_flags_do_not_count(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "K2_NO_SEPARATION"], {"world:minus": (60, 200)})
        x = body("FALSIFIABLE", [], {"world:minus": (5, 200)})
        r = classify(f, x, ["K2_NO_SEPARATION"])  # K2_NO_SEPARATION alone is not a rate flag
        self.assertTrue(r["pb_detected"])
        self.assertFalse(r["attributable"])
        self.assertFalse(classify(f, x, ["K5_HOLDS_ON_NOISE"])["pb_detected"])

    def test_verdict_must_be_not_falsifiable(self):
        f = body("WEAK", ["K2_HIGH_SIZE"], {"world:minus": (60, 200)})
        x = body("FALSIFIABLE", [], {"world:minus": (5, 200)})
        r = classify(f, x, ["K2_HIGH_SIZE"])
        self.assertEqual((r["pb_detected"], r["attributable"], r["draft1_rule"]), (False, False, False))

    def test_fixed_without_counts(self):
        f = body("NOT_FALSIFIABLE", ["HIGH_RATE:control:perm"], {"control:perm": (70, 200)})
        x = body("UNDEFINED", [], {})
        r = classify(f, x, ["HIGH_RATE:control:perm"])
        self.assertFalse(r["attributable"])
        self.assertTrue(any("fixed has no counts" in s for s in r["reasons"]))

    def test_draft1_margin(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (35, 200)})
        x = body("FALSIFIABLE", [], {"world:minus": (16, 200)})  # margin 19 of 200: p < 0.05 but below the margin
        r = classify(f, x, ["K2_HIGH_SIZE"])
        self.assertTrue(r["attributable"])
        self.assertFalse(r["draft1_rule"])
        x = body("FALSIFIABLE", [], {"world:minus": (15, 200)})
        self.assertTrue(classify(f, x, ["K2_HIGH_SIZE"])["draft1_rule"])

    # --- the paths of R2-2 and R2-23; tests/acceptance_d holds synthetic certificates for the same paths
    def test_k4_two_controls_only_one_meets_the_bounds_condition(self):
        plus_b = (0.84, 0.94)
        f = body("NOT_FALSIFIABLE", ["K4_CONTROL_ALSO_HOLDS"],
                 {"world:plus": (180, 200), "control:p": (2, 200), "control:q": (170, 200)},
                 {"world:plus": plus_b, "control:p": (0.0, 0.05), "control:q": (0.79, 0.89)})
        # control q's upper bound 0.89 is not below plus's lower bound 0.84: the gate raised K4 for q only
        x = body("FALSIFIABLE", [], {"world:plus": (180, 200), "control:p": (2, 200), "control:q": (3, 200)},
                 {"world:plus": plus_b, "control:p": (0.0, 0.05), "control:q": (0.0, 0.05)})
        r = classify(f, x, ["K4_CONTROL_ALSO_HOLDS"])
        self.assertEqual([q["stream"] for q in r["qualifying"]], ["control:q"])
        self.assertTrue(r["attributable"] and r["declared"] and not r["generic"])
        self.assertFalse(any("control:p" in s for s in r["reasons"]))  # p raised nothing, so p is not examined

    def test_k4_fixed_flag_on_one_control_does_not_block_the_other(self):
        plus_b = (0.84, 0.94)
        f = body("NOT_FALSIFIABLE", ["K4_CONTROL_ALSO_HOLDS"],
                 {"world:plus": (180, 200), "control:p": (150, 200), "control:q": (170, 200)},
                 {"world:plus": plus_b, "control:p": (0.69, 0.89), "control:q": (0.79, 0.89)})
        # fixed: control p holds as often as plus (its K4 flag), control q is low
        x = body("NOT_FALSIFIABLE", ["K4_CONTROL_ALSO_HOLDS"],
                 {"world:plus": (180, 200), "control:p": (172, 200), "control:q": (3, 200)},
                 {"world:plus": plus_b, "control:p": (0.8, 0.9), "control:q": (0.0, 0.05)})
        r = classify(f, x, ["K4_CONTROL_ALSO_HOLDS"])
        self.assertEqual([q["stream"] for q in r["qualifying"]], ["control:q"])
        self.assertTrue(any("control:p" in s and "fixed-flagged" in s for s in r["reasons"]))

    def test_shuffle_with_two_pairs(self):
        plus_b = (0.84, 0.94)
        f = body("NOT_FALSIFIABLE", ["K5_HOLDS_ON_SHUFFLE"],
                 {"world:plus": (180, 200), "probe:shuffle:a,b": (170, 200), "probe:shuffle:a,c": (2, 200)},
                 {"world:plus": plus_b, "probe:shuffle:a,b": (0.79, 0.89), "probe:shuffle:a,c": (0.0, 0.05)})
        x = body("FALSIFIABLE", [], {"world:plus": (180, 200), "probe:shuffle:a,b": (3, 200), "probe:shuffle:a,c": (2, 200)},
                 {"world:plus": plus_b, "probe:shuffle:a,b": (0.0, 0.05), "probe:shuffle:a,c": (0.0, 0.05)})
        r = classify(f, x, ["K5_HOLDS_ON_SHUFFLE"])
        self.assertEqual([q["stream"] for q in r["qualifying"]], ["probe:shuffle:a,b"])
        self.assertTrue(r["attributable"] and r["declared"])

    def test_flag_without_a_stream_meeting_the_condition_is_listed(self):
        f = body("NOT_FALSIFIABLE", ["K4_CONTROL_ALSO_HOLDS"], {"world:plus": (180, 200), "control:p": (2, 200)},
                 {"world:plus": (0.84, 0.94), "control:p": (0.0, 0.05)})  # inconsistent certificate: the flag has no stream
        x = body("FALSIFIABLE", [], {"world:plus": (180, 200), "control:p": (2, 200)})
        r = classify(f, x, ["K4_CONTROL_ALSO_HOLDS"])
        self.assertTrue(r["pb_detected"])
        self.assertFalse(r["attributable"])
        self.assertTrue(any("no stream meets the bounds condition" in s for s in r["reasons"]))

    def test_faulty_load_error_is_not_detected_and_does_not_raise(self):
        x = body("FALSIFIABLE", [], {"world:minus": (5, 200)})
        r = classify(load_error_body(), x, ["K2_HIGH_SIZE"])
        self.assertEqual((r["pb_detected"], r["attributable"], r["draft1_rule"]), (False, False, False))
        self.assertEqual(r["reasons"], ["faulty load error"])
        r = classify({"verdict": "NOT_FALSIFIABLE", "components": [], "load_error": None}, x, ["K2_HIGH_SIZE"])
        self.assertEqual(r["reasons"], ["faulty load error"])  # an empty component list alone is enough
        with_key = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (60, 200)})
        with_key["load_error"] = {"type": "X"}
        self.assertEqual(classify(with_key, x, ["K2_HIGH_SIZE"])["reasons"], ["faulty load error"])  # so is the key

    def test_fixed_load_error_gives_no_qualifying_stream(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (60, 200)})
        r = classify(f, load_error_body(), ["K2_HIGH_SIZE"])
        self.assertTrue(r["pb_detected"])
        self.assertEqual((r["attributable"], r["generic"], r["declared"], r["draft1_rule"], r["qualifying"]),
                         (False, False, False, False, []))
        self.assertEqual(r["reasons"], ["fixed load error"])

    def test_fixed_hard_undefined_on_the_stream_blocks_it(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "HIGH_RATE:probe:noise"],
                 {"world:minus": (60, 200), "probe:noise": (60, 200)})
        # fixed: 50 hard UNDEFINED outcomes on minus (which holds in 5 of 200); its noise stream is clean
        x = body("UNDEFINED", ["K1_UNDEFINED"], {"world:minus": (5, 200), "probe:noise": (5, 200)},
                 hard={"world:minus": 50})
        r = classify(f, x, ["K2_HIGH_SIZE", "HIGH_RATE:probe:noise"])
        self.assertTrue(r["pb_detected"])
        self.assertIn("K2_HIGH_SIZE@world:minus: fixed hard UNDEFINED on world:minus", r["reasons"])
        self.assertEqual([q["stream"] for q in r["qualifying"]], ["probe:noise"])  # the other stream still qualifies
        self.assertTrue(r["generic"] and not r["declared"])
        # only a hard UNDEFINED on that stream blocks it: one on another stream does not
        x2 = body("FALSIFIABLE", [], {"world:minus": (5, 200), "probe:noise": (5, 200)}, hard={"probe:noise": 50})
        r2 = classify(f, x2, ["K2_HIGH_SIZE"])
        self.assertTrue(r2["declared"] and not r2["generic"])
        # the same counts without the hard UNDEFINED qualify through minus
        x0 = body("FALSIFIABLE", [], {"world:minus": (5, 200), "probe:noise": (5, 200)})
        self.assertTrue(classify(f, x0, ["K2_HIGH_SIZE"])["declared"])

    def test_generic_only_through_k5_holds_on_noise(self):
        f = body("NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"],
                 {"world:plus": (180, 200), "world:minus": (4, 200), "probe:noise": (170, 200)},
                 {"world:plus": (0.84, 0.94), "probe:noise": (0.79, 0.89), "world:minus": (0.0, 0.05)})
        x = body("FALSIFIABLE", [], {"world:plus": (180, 200), "world:minus": (4, 200), "probe:noise": (3, 200)})
        r = classify(f, x, ["K5_HOLDS_ON_NOISE"])
        self.assertTrue(r["attributable"] and r["generic"] and not r["declared"])

    def test_condition_a_and_condition_b_are_both_needed(self):
        f = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (60, 200)})
        # (a) true (the fixed twin carries no flag) and (b) false (60 against 58: no excess)
        r = classify(f, body("FALSIFIABLE", [], {"world:minus": (58, 200)}), ["K2_HIGH_SIZE"])
        self.assertTrue(r["pb_detected"])
        self.assertFalse(r["attributable"])
        # (a) false (the fixed twin carries K2_HIGH_SIZE) and (b) true (60 against 30: Fisher p < 0.05)
        x = body("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], {"world:minus": (30, 200)})
        self.assertFalse(classify(f, x, ["K2_HIGH_SIZE"])["attributable"])
        # both true
        self.assertTrue(classify(f, body("FALSIFIABLE", [], {"world:minus": (30, 200)}), ["K2_HIGH_SIZE"])["attributable"])

    def test_condition_a_false_through_each_flag_kind(self):
        kinds = [("K2_HIGH_SIZE", "world:minus"), ("HIGH_RATE:control:p", "control:p"),
                 ("HIGH_RATE:probe:noise", "probe:noise"), ("K5_HOLDS_ON_NULL", "world:null"),
                 ("HIGH_RATE:probe:shuffle:a,b", "probe:shuffle:a,b")]
        for flag, stream in kinds:
            with self.subTest(flag):
                f = body("NOT_FALSIFIABLE", [flag], {stream: (80, 200)})
                x_flagged = body("NOT_FALSIFIABLE", [flag], {stream: (40, 200)})
                self.assertFalse(classify(f, x_flagged, [flag])["attributable"])
                self.assertTrue(classify(f, body("FALSIFIABLE", [], {stream: (3, 200)}), [flag])["attributable"])


@unittest.skipUnless(os.path.isdir(PC_CERTS), f"Phase C certificates not found under {PC_CERTS}")
class PhaseCAcceptanceTests(unittest.TestCase):
    """The acceptance test of TOOLS_SPEC_D section 4, on the read-only Phase C certificates (0.5.0)."""

    @classmethod
    def setUpClass(cls):
        with open(PC_EXPECTED, encoding="utf-8") as f:
            expected = json.load(f)["cases"]
        cls.result = {}
        cases_dir = os.path.join(common.PC, "cases")
        for case in sorted(os.listdir(cases_dir)):
            if not case.startswith(("B2-", "B3-")):
                continue
            with open(os.path.join(PC_CERTS, case, "faulty.json"), encoding="utf-8") as f:
                faulty = json.load(f)["body"]
            with open(os.path.join(PC_CERTS, case, "fixed.json"), encoding="utf-8") as f:
                fixed = json.load(f)["body"]
            cls.result[case] = classify(faulty, fixed, expected[case]["expected"])

    def test_every_pair_was_read(self):
        self.assertEqual(len(self.result), 22)  # 12 B-2 and 10 B-3 pairs in Phase C

    def test_pb_detected(self):
        self.assertEqual({c for c, r in self.result.items() if r["pb_detected"]}, PB_DETECTED)

    def test_attributable(self):
        self.assertEqual({c for c, r in self.result.items() if r["attributable"]}, ATTRIBUTABLE)

    def test_attributable_and_declared(self):
        self.assertEqual({c for c, r in self.result.items() if r["attributable"] and r["declared"]}, ATTRIBUTABLE_DECLARED)
        self.assertEqual({c for c, r in self.result.items() if r["generic"]} & {"B3-04", "B3-05"}, {"B3-04", "B3-05"})
        self.assertFalse(self.result["B3-04"]["declared"] or self.result["B3-05"]["declared"])

    def test_not_attributable_among_detected(self):
        self.assertEqual({c for c, r in self.result.items() if r["pb_detected"] and not r["attributable"]}, NOT_ATTRIBUTABLE)

    def test_bounds_condition_is_the_gates_sl_rule_on_every_phase_c_certificate(self):
        """For all 52 pairs x 2 twins: the streams the bounds condition names are exactly the streams for which the
        gate's own ``sl`` (truth_gate.checks, on the counts and the certificate's alpha_per_bound) fails, and the K4 /
        K5_HOLDS_ON_SHUFFLE flag is in the certificate exactly when there is such a stream (unless it was suppressed)."""
        from structure_stat import import_truth_gate
        import_truth_gate(common.PKG)
        from truth_gate.checks import Context, StreamStats, sl
        from attributable import not_sl_streams
        n_checked = n_flagged = 0
        for case in sorted(os.listdir(PC_CERTS)):
            for twin in ("faulty", "fixed"):
                path = os.path.join(PC_CERTS, case, f"{twin}.json")
                if not os.path.isfile(path):
                    continue
                with open(path, encoding="utf-8") as f:
                    b = json.load(f)["body"]
                if b.get("load_error") or not b["components"]:
                    continue
                for comp in b["components"]:
                    counts, bounds = comp["counts"], comp["bounds"]
                    if not bounds:
                        continue
                    ctx = Context(False, b["alpha_per_bound"], 0.0, 0.0)
                    stat = {s: StreamStats(c["holds"], c["undefined"], c["n"], c["hard_undefined"]) for s, c in counts.items()}
                    for prefix, flag in (("control:", "K4_CONTROL_ALSO_HOLDS"), ("probe:shuffle:", "K5_HOLDS_ON_SHUFFLE")):
                        gate = sorted(s for s in stat if s.startswith(prefix) and not sl(stat[s], stat["world:plus"], ctx))
                        mine = sorted(not_sl_streams(counts, bounds, prefix))
                        self.assertEqual(mine, gate, f"{case}/{twin}/{prefix}")
                        n_checked += 1
                        if "K2_HOLDS_UNREACHABLE" in comp["flags"]:
                            continue  # cascade suppression removes the SL flags when plus never holds
                        self.assertEqual(flag in comp["flags"], bool(gate), f"{case}/{twin}/{flag}")
                        n_flagged += bool(gate)
        self.assertGreater(n_checked, 100)
        self.assertGreater(n_flagged, 0)  # the rule was exercised on real flags, not only on empty sets

    @unittest.skipUnless(os.path.isfile(FIXTURE_OUTPUT), "designer's fixture output not found")
    def test_reproduces_the_designers_output_line_by_line(self):
        with open(FIXTURE_OUTPUT, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        self.assertEqual(len(lines), len(PB_DETECTED))
        for ln in lines:
            case, rest = ln.split(": ", 1)
            status, detail = rest.split(" | ", 1)
            r = self.result[case]
            self.assertEqual(status == "ATTRIBUTABLE", r["attributable"], case)
            # the designer's "<flag>@<stream> a vs b p=... [fixed-flagged] [OK]" entries, one per (flag, stream)
            theirs = [d.strip() for d in detail.split("; ")]
            mine = [d.strip() for d in r["reasons"]]
            self.assertEqual(sorted(theirs), sorted(mine), case)


class AttributableCliTests(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(PC_CERTS), "Phase C certificates not found")
    def test_cli_on_two_pairs(self):
        for case, want in (("B2-12", True), ("B2-08", False)):
            r = common.run_tool("attributable.py", "--faulty", os.path.join(PC_CERTS, case, "faulty.json"),
                                "--fixed", os.path.join(PC_CERTS, case, "fixed.json"), "--expected-file", PC_EXPECTED,
                                "--case", case)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["attributable"], want)
            self.assertEqual(set(out), {"pb_detected", "attributable", "generic", "declared", "draft1_rule",
                                        "qualifying", "reasons"})

    def test_cli_usage_errors(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "x.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"cases": {}}, f)
            r = common.run_tool("attributable.py", "--faulty", p, "--fixed", p, "--expected-file", p, "--case", "NOPE")
            self.assertEqual(r.returncode, 2)
            self.assertEqual(common.run_tool("attributable.py", "--faulty", p).returncode, 2)


if __name__ == "__main__":
    unittest.main()
