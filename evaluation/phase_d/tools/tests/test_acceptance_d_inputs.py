"""Structural checks of tests/acceptance_d (the synthetic certificates).  They assert no outcome of the attribution rule: the
designer writes those by hand in tests/acceptance_d/EXPECTED.md."""
import json
import os
import unittest

import common
from attributable import classify
from structure_stat import import_truth_gate

ROOT = os.path.join(common.HERE, "acceptance_d")
FOLDERS = ["a_true_b_false", "a_false_k2_high_size", "a_false_high_rate_control", "a_false_high_rate_noise",
           "a_false_k5_holds_on_null", "a_false_shuffle", "k4_two_controls_one_meets_bounds", "shuffle_two_pairs",
           "fixed_load_error", "faulty_load_error", "fixed_hard_undefined", "generic_only_k5_holds_on_noise", "declared_only",
           # D-R4-9 (R3-6)
           "k2_no_separation_only", "faulty_not_nf_with_rate_flag", "faulty_nf_unexpected_mandatory", "generic_and_declared",
           "fixed_missing_stream", "fixed_hard_undefined_other_stream", "fixed_k4_blocks_high_rate_control"]


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


class AcceptanceInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)

    def test_the_folders_are_those_of_the_spec(self):
        found = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)))
        self.assertEqual(found, sorted(FOLDERS))
        for d in FOLDERS:
            self.assertEqual(sorted(os.listdir(os.path.join(ROOT, d))), ["expected_flags.json", "faulty.json", "fixed.json"])
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "README.md")))

    def test_no_outcome_words_in_the_certificates(self):
        # (EXPECTED.md is the designer's own file; this test no longer checks for its absence and never reads it)
        for d in FOLDERS:
            for name in ("faulty.json", "fixed.json"):
                text = json.dumps(read(d, name))
                for word in ("attributable", "pb_detected", "generic", "declared"):
                    self.assertNotIn(word, text)

    def test_flags_and_bounds_are_the_gates_for_the_counts(self):
        from truth_gate import checks
        from truth_gate.stats import wilson_bounds
        for d in FOLDERS:
            for name in ("faulty", "fixed"):
                body = read(d, f"{name}.json")["body"]
                if not body["components"]:
                    self.assertEqual(body["verdict"], "UNDEFINED")
                    self.assertTrue(body["load_error"])
                    continue
                comp = body["components"][0]
                a = body["alpha_per_bound"]
                ctx = checks.Context(False, a, 0.8, 0.05)
                st = {s: checks.StreamStats(c["holds"], c["undefined"], c["n"], c["hard_undefined"])
                      for s, c in comp["counts"].items()}
                ctl = {s: st[s] for s in st if s.startswith("control:")}
                shuf = {s[len("probe:"):]: st[s] for s in st if s.startswith("probe:shuffle:")}
                flags = set(checks.check_k1(st))
                flags.update(checks.check_k2(st["world:plus"], st["world:minus"], ctx, False))
                flags.update(checks.check_k4(st["world:plus"], ctl, False, ctx))
                flags.update(checks.check_k5(st["world:plus"], st["probe:noise"], st["probe:zeros"], st.get("world:null"), shuf, ctx))
                flags.update(checks.check_high_rate({s: v for s, v in st.items() if s not in ("world:plus", "world:minus")}, ctx))
                self.assertEqual(sorted(flags), comp["flags"], (d, name))
                self.assertEqual(checks.component_verdict(flags), body["verdict"], (d, name))
                for s, v in st.items():
                    lo, up = wilson_bounds(v.holds, v.n, a)
                    self.assertAlmostEqual(comp["bounds"][s]["lower"], lo, places=11)
                    self.assertAlmostEqual(comp["bounds"][s]["upper"], up, places=11)

    def test_every_pair_runs_through_classify_without_an_exception(self):
        for d in FOLDERS:
            f, x = read(d, "faulty.json")["body"], read(d, "fixed.json")["body"]
            expected = read(d, "expected_flags.json")["cases"][d]["expected"]
            out = classify(f, x, expected)
            self.assertEqual(set(out), {"pb_detected", "attributable", "generic", "declared", "draft1_rule", "qualifying", "reasons"})

    def test_cli_reads_the_files(self):
        for d in FOLDERS:
            r = common.run_tool("attributable.py", "--faulty", os.path.join(ROOT, d, "faulty.json"), "--fixed",
                                os.path.join(ROOT, d, "fixed.json"), "--expected-file",
                                os.path.join(ROOT, d, "expected_flags.json"), "--case", d)
            self.assertEqual(r.returncode, 0, (d, r.stderr))


if __name__ == "__main__":
    unittest.main()
