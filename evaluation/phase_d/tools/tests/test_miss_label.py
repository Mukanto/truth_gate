import json
import os
import tempfile
import unittest

import common
import toy_case
import miss_label as ml
from assemble import assemble
from structure_stat import import_truth_gate, load_study_module

TRIVIAL = "import numpy as np\n\n\ndef criterion(d):\n    return True\n"
EXPECTED = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
            "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "HIGH_RATE:probe:noise", "HIGH_RATE:world:null",
            "HIGH_RATE:control:permute_y"]


def study(phi, edit=None):
    """The assembled faulty study of the toy with autocorrelation ``phi`` (and an optional edit of the reference)."""
    ref = toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": phi}
    if edit:
        ref = edit(ref)
    return assemble(ref, TRIVIAL)


def module_of(src):
    return load_study_module(src, "faulty_study.py", "t")


def cert(verdict, flags, minus_holds=3, counts=None, load_error=None):
    if load_error is not None:
        return {"verdict": "UNDEFINED", "components": [], "load_error": load_error}
    base = {"world:plus": (190, 200), "world:minus": (minus_holds, 200), "probe:noise": (2, 200), "control:permute_y": (3, 200)}
    base.update(counts or {})
    comp = {"id": "C", "flags": list(flags),
            "counts": {s: {"holds": h, "undefined": 0, "hard_undefined": 0, "n": n} for s, (h, n) in base.items()},
            "bounds": {}}
    return {"verdict": verdict, "load_error": None, "components": [comp]}


FIXED_CLEAN = cert("FALSIFIABLE", [], minus_holds=4)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)
        cls.strong = module_of(study(0.99))  # the worlds carry the structure the note describes
        cls.weak = module_of(study(0.0))     # they do not

    def label(self, faulty, fixed=FIXED_CLEAN, module=None, note=0.99, private=None, **kw):
        priv = private if private is not None else toy_case.private(note)
        return ml.label_miss(faulty, fixed, EXPECTED, priv, module or self.strong, common.PKG, **kw)


class LabelOrderTests(Base):
    def test_detected_pair_has_no_label(self):
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60))
        self.assertIsNone(r["label"])
        self.assertTrue(r["detected"] and r["attributable"]["attributable"])
        self.assertIsNone(r["structure"])  # nothing is computed for a detected pair

    def test_e_attrition_cause_given(self):
        r = ml.label_miss(None, None, None, None, None, common.PKG, attrition="timeout")
        self.assertEqual((r["label"], r["cause"], r["text"]), ("e", "timeout", "attrition or no verdict"))

    def test_e_attrition_wins_over_everything(self):
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), attrition="part-B no")
        self.assertEqual((r["label"], r["cause"]), ("e", "part-B no"))

    def test_e_faulty_load_error_undefined_untested(self):
        r = self.label(cert(None, [], load_error={"type": "SyntaxError"}))
        self.assertEqual((r["label"], r["cause"]), ("e", "faulty load error"))
        r = self.label(cert("UNDEFINED", ["K1_UNDEFINED"]))
        self.assertEqual((r["label"], r["cause"]), ("e", "faulty verdict UNDEFINED"))
        r = self.label(cert("UNTESTED", ["K2_MINUS_IDENTICAL"]))
        self.assertEqual((r["label"], r["cause"]), ("e", "faulty verdict UNTESTED"))

    def test_c_flagged_not_attributable(self):
        faulty = cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60)
        fixed = cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=50)  # the fixed twin is flagged on minus too
        r = self.label(faulty, fixed)
        self.assertEqual(r["label"], "c")
        self.assertTrue(r["attributable"]["pb_detected"] and not r["attributable"]["attributable"])
        self.assertFalse(r["detected"])

    def test_e_through_a_fixed_load_error(self):
        # T3-6: a fixed twin without a result makes the pair label (e) with the cause, not (c)
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), cert(None, [], load_error={"type": "X"}))
        self.assertEqual((r["label"], r["cause"], r["cause_twin"]), ("e", "fixed load error", "fixed"))
        self.assertFalse(r["detected"])
        self.assertIsNone(r["attributable"])  # nothing else was computed

    def test_a_fixed_problem_does_not_make_a_pair_e_when_the_faulty_twin_is_not_pb_detected(self):
        # D-R4-5 (R3-4): the faulty twin's own labels apply; the fixed twin's cause is a note
        load_error = cert(None, [], load_error={"type": "X"})
        for fixed_kw in ({"fixed": load_error}, {"fixed": None}, {"fixed_attrition": "timeout"}):
            with self.subTest(list(fixed_kw)):
                fixed_arg = fixed_kw.get("fixed", FIXED_CLEAN)
                r = ml.label_miss(cert("FALSIFIABLE", [], minus_holds=3), fixed_arg, EXPECTED, toy_case.private(0.99),
                                  self.strong, common.PKG, fixed_attrition=fixed_kw.get("fixed_attrition"))
                self.assertEqual(r["label"], "b")
                self.assertFalse(r["pb_detected"])
                self.assertIsNotNone(r["fixed_attrition"])
                self.assertIsNone(r["cause"])
                self.assertTrue(any("note: the fixed twin has no result" in x for x in r["reasons"]))

    def test_fixed_attrition_with_a_faulty_twin_that_is_not_pb_detected_gives_a_b_or_d(self):
        timeout = "timeout"
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3), fixed_attrition=timeout)
        self.assertEqual((r["label"], r["fixed_attrition"]), ("b", "timeout"))
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3), fixed_attrition=timeout, module=self.weak)
        self.assertEqual((r["label"], r["fixed_attrition"]), ("a", "timeout"))
        r = self.label(cert("FALSIFIABLE", [], minus_holds=40), fixed_attrition=timeout)
        self.assertEqual((r["label"], r["fixed_attrition"]), ("d", "timeout"))
        # NOT_FALSIFIABLE through a flag that is not expected is not PB-detected either
        r = self.label(cert("NOT_FALSIFIABLE", ["K3_PREMISE_NOT_TESTED"], minus_holds=3), fixed_attrition=timeout)
        self.assertEqual((r["label"], r["pb_detected"]), ("b", False))
        # an expected flag without the verdict NOT_FALSIFIABLE is not PB-detected
        r = self.label(cert("WEAK", ["K2_HIGH_SIZE"], minus_holds=3), fixed_attrition=timeout)
        self.assertEqual((r["label"], r["pb_detected"]), ("b", False))

    def test_fixed_attrition_with_a_pb_detected_faulty_twin_is_e(self):
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), fixed_attrition="timeout")
        self.assertEqual((r["label"], r["cause"], r["cause_twin"], r["pb_detected"]), ("e", "timeout", "fixed", True))
        self.assertIsNone(r["fixed_attrition"])

    def test_the_faulty_twins_causes_still_come_first_with_a_fixed_problem(self):
        r = self.label(cert("UNDEFINED", ["K1_UNDEFINED"]), fixed_attrition="timeout")
        self.assertEqual((r["cause"], r["cause_twin"]), ("faulty verdict UNDEFINED", "faulty"))

    def test_e_through_a_fixed_timeout(self):
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), fixed_attrition="timeout")
        self.assertEqual((r["label"], r["cause"], r["cause_twin"], r["text"]), ("e", "timeout", "fixed", "attrition or no verdict"))

    def test_a_fixed_attrition_wins_over_a_certificate_that_is_present(self):
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), FIXED_CLEAN, fixed_attrition="timeout")
        self.assertEqual((r["label"], r["cause"]), ("e", "timeout"))

    def test_e_through_an_absent_fixed_certificate(self):
        r = ml.label_miss(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), None, EXPECTED, toy_case.private(0.99),
                          self.strong, common.PKG)
        self.assertEqual((r["label"], r["cause"], r["cause_twin"]), ("e", "fixed certificate absent", "fixed"))

    def test_the_faulty_twins_causes_come_first(self):
        r = self.label(cert("UNDEFINED", ["K1_UNDEFINED"]), cert(None, [], load_error={"type": "X"}))
        self.assertEqual((r["cause"], r["cause_twin"]), ("faulty verdict UNDEFINED", "faulty"))
        r = self.label(cert(None, [], load_error={"type": "X"}), cert(None, [], load_error={"type": "X"}))
        self.assertEqual((r["cause"], r["cause_twin"]), ("faulty load error", "faulty"))
        r = ml.label_miss(None, None, None, None, None, common.PKG, attrition="part-B no")
        self.assertEqual((r["cause"], r["cause_twin"]), ("part-B no", None))

    def test_a_fixed_hard_undefined_with_components_is_still_c(self):
        counts = {"world:minus": (6, 200)}
        fixed = cert("UNDEFINED", ["K1_UNDEFINED"], counts=counts)
        fixed["components"][0]["counts"]["world:minus"]["hard_undefined"] = 50
        r = self.label(cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60), fixed)
        self.assertEqual(r["label"], "c")

    def test_c_comes_before_a_even_if_the_structure_is_missing(self):
        faulty = cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60)
        fixed = cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=50)
        r = self.label(faulty, fixed, module=self.weak)
        self.assertEqual(r["label"], "c")
        self.assertLess(r["structure"]["share_beyond_half"], 0.5)  # (a) would have applied; (c) takes precedence

    def test_c_comes_before_b_even_if_the_count_is_below_kstar(self):
        faulty = cert("NOT_FALSIFIABLE", ["HIGH_RATE:control:permute_y"], minus_holds=3,
                      counts={"control:permute_y": (80, 200)})
        fixed = cert("NOT_FALSIFIABLE", ["HIGH_RATE:control:permute_y"], counts={"control:permute_y": (60, 200)})
        r = self.label(faulty, fixed)
        self.assertEqual(r["label"], "c")
        self.assertLess(r["faulty_minus_holds"], r["kstar_arm"])

    def test_a_structure_share_below_half(self):
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3), module=self.weak)
        self.assertEqual((r["label"], r["text"]), ("a", "declared worlds lack the structure"))
        self.assertLess(r["structure"]["share_beyond_half"], 0.5)
        self.assertLess(r["faulty_minus_holds"], r["kstar_arm"])  # (b) would also apply: (a) comes first

    def test_b_structure_present_count_below_kstar(self):
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3))
        self.assertEqual((r["label"], r["kstar_arm"], r["m"], r["n"]), ("b", 18, 4, 200))
        self.assertGreaterEqual(r["structure"]["share_beyond_half"], 0.5)

    def test_d_other(self):
        r = self.label(cert("FALSIFIABLE", [], minus_holds=40))
        self.assertEqual((r["label"], r["text"]), ("d", "other: examined as a possible gate finding"))
        self.assertGreaterEqual(r["faulty_minus_holds"], r["kstar_arm"])

    def test_boundary_of_b_is_the_kstar_itself(self):
        self.assertEqual(self.label(cert("FALSIFIABLE", [], minus_holds=17))["label"], "b")
        self.assertEqual(self.label(cert("FALSIFIABLE", [], minus_holds=18))["label"], "d")

    def test_a_faulty_study_flagged_but_without_an_expected_flag_is_a_miss_of_the_structure_kind(self):
        # NOT_FALSIFIABLE through a flag that is not in the expected list: not PB-detected, so (c) does not apply
        r = self.label(cert("NOT_FALSIFIABLE", ["K3_PREMISE_NOT_TESTED"], minus_holds=3))
        self.assertFalse(r["attributable"]["pb_detected"])
        self.assertEqual(r["label"], "b")


class StaleTextTests(Base):
    """D-R5-5 (R3B-6): the text of label (b)."""

    def test_label_b_text(self):
        self.assertEqual(ml.TEXTS["b"], "the error's minus rate stayed below the gate's flag threshold")
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3))
        self.assertEqual((r["label"], r["text"]), ("b", "the error's minus rate stayed below the gate's flag threshold"))

    def test_docstring_has_the_new_text_and_not_the_old(self):
        self.assertIn("the error's minus rate stayed below the gate's flag threshold", ml.__doc__)
        self.assertNotIn("error did not change decisions", ml.__doc__)
        self.assertNotIn("error did not change decisions", " ".join(ml.TEXTS.values()))


class KstarArmTests(Base):
    def test_kstar_is_computed_from_the_arms_own_study(self):
        def edit(ref):  # a null world and one relational pair: m = 1 + 1 + 2 + 1 + 1 = 6
            ref = ref.replace('        "plus": World(plus),\n', '        "plus": World(plus),\n        "null": World(minus),\n')
            return ref.replace("    controls=[", '    relational=[("x", "y")],\n    controls=[')
        big = module_of(study(0.99, edit))
        small = self.strong
        faulty = cert("FALSIFIABLE", [], minus_holds=18)
        r_small = self.label(faulty, module=small)
        r_big = self.label(faulty, module=big)
        self.assertEqual((r_small["m"], r_small["kstar_arm"], r_small["label"]), (4, 18, "d"))
        self.assertEqual((r_big["m"], r_big["kstar_arm"], r_big["label"]), (6, 19, "b"))  # the same count, another arm

    def test_kstar_matches_validity_checks_function(self):
        import validity_check as vc
        r = self.label(cert("FALSIFIABLE", []))
        self.assertEqual(r["kstar_arm"], vc.kstar_of(0.05, 4, 0.05))


class StructureLabelTests(Base):
    def test_set_by_brief_is_not_applied(self):
        priv = toy_case.private(0.99, set_by_brief=True)
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3), module=self.weak, private=priv)
        self.assertEqual(r["label"], "b")  # (a) skipped although the world lacks the structure
        self.assertIsNone(r["structure"])
        self.assertTrue(any("set by the brief" in s for s in r["reasons"]))

    def test_no_statistic_is_not_applied(self):
        for priv in ({"structure_statistic": None}, {}):
            r = self.label(cert("FALSIFIABLE", [], minus_holds=3), module=self.weak, private=priv)
            self.assertEqual(r["label"], "b")
            self.assertTrue(any("no structure statistic" in s for s in r["reasons"]))

    def test_uncomputable_statistic_gives_its_own_label(self):
        priv = toy_case.private(0.99)
        priv["structure_statistic"]["code"] = "def stat(d):\n    return float('nan')\n"
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3), private=priv)
        self.assertEqual((r["label"], r["text"]), ("structure_not_computable", "structure not computable"))
        self.assertIn("error", r["structure"])
        # (c) still comes first
        faulty = cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60)
        fixed = cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=50)
        self.assertEqual(self.label(faulty, fixed, private=priv)["label"], "c")

    def test_the_statistic_uses_the_structure_minus_stream_and_200_samples(self):
        from structure_stat import structure_stat
        r = self.label(cert("FALSIFIABLE", [], minus_holds=3))
        direct = structure_stat(self.strong, toy_case.private(0.99), "minus", 200, 20261117, common.PKG)
        self.assertEqual(r["structure"], direct)
        self.assertEqual((ml.SEED, ml.STRUCTURE_SAMPLES), (20261117, 200))


class CliTests(Base):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.paths = {n: os.path.join(t, n) for n in ("faulty.json", "fixed.json", "expected.json", "private.json",
                                                      "study.py", "out.json")}
        with open(self.paths["study.py"], "w", encoding="utf-8", newline="\n") as f:
            f.write(study(0.99))
        with open(self.paths["private.json"], "w", encoding="utf-8") as f:
            json.dump(toy_case.private(0.99), f)
        with open(self.paths["expected.json"], "w", encoding="utf-8") as f:
            json.dump({"cases": {"D-001/W1": {"expected": EXPECTED}}}, f)
        self.write("faulty.json", {"body": cert("FALSIFIABLE", [], minus_holds=3)})
        self.write("fixed.json", {"body": FIXED_CLEAN})

    def write(self, name, obj):
        with open(self.paths[name], "w", encoding="utf-8") as f:
            json.dump(obj, f)

    def run_cli(self, *extra, files=True):
        args = ["--package-root", common.PKG, "--out", self.paths["out.json"], *extra]
        if files:
            args += ["--faulty", self.paths["faulty.json"], "--fixed", self.paths["fixed.json"], "--expected-file",
                     self.paths["expected.json"], "--case", "D-001/W1", "--private", self.paths["private.json"],
                     "--study", self.paths["study.py"]]
        return common.run_tool("miss_label.py", *args)

    def test_label_b_through_the_cli(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual((res["label"], res["kstar_arm"]), ("b", 18))
        with open(self.paths["out.json"], encoding="utf-8") as f:
            self.assertEqual(json.load(f)["label"], "b")

    def test_fixed_load_error_through_the_cli(self):
        self.write("faulty.json", {"body": cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60)})
        self.write("fixed.json", {"body": cert(None, [], load_error={"type": "SyntaxError"})})
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual((res["label"], res["cause"], res["cause_twin"]), ("e", "fixed load error", "fixed"))

    def test_fixed_problems_with_a_faulty_twin_that_is_not_pb_detected_through_the_cli(self):
        # faulty: FALSIFIABLE with a low minus count, as in setUp
        r = self.run_cli("--fixed-attrition", "timeout")
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual((res["label"], res["fixed_attrition"], res["pb_detected"]), ("b", "timeout", False))
        os.remove(self.paths["fixed.json"])
        res = json.loads(self.run_cli().stdout)
        self.assertEqual((res["label"], res["fixed_attrition"]), ("b", "fixed certificate absent"))
        self.write("fixed.json", {"body": cert(None, [], load_error={"type": "X"})})
        res = json.loads(self.run_cli().stdout)
        self.assertEqual((res["label"], res["fixed_attrition"]), ("b", "fixed load error"))

    def test_fixed_attrition_through_the_cli(self):
        self.write("faulty.json", {"body": cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60)})
        r = self.run_cli("--fixed-attrition", "timeout")
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual((res["label"], res["cause"], res["cause_twin"]), ("e", "timeout", "fixed"))

    def test_absent_fixed_certificate_through_the_cli(self):
        self.write("faulty.json", {"body": cert("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], minus_holds=60)})
        os.remove(self.paths["fixed.json"])  # the path is given, the file does not exist
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["cause"], "fixed certificate absent")
        # and with no --fixed at all
        args = ["--package-root", common.PKG, "--faulty", self.paths["faulty.json"], "--expected-file", self.paths["expected.json"],
                "--case", "D-001/W1", "--private", self.paths["private.json"], "--study", self.paths["study.py"]]
        r = common.run_tool("miss_label.py", *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["cause"], "fixed certificate absent")

    def test_attrition_needs_no_files(self):
        r = self.run_cli("--attrition", "timeout", files=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["cause"], "timeout")

    def test_bare_bodies_are_accepted(self):
        self.write("faulty.json", cert("FALSIFIABLE", [], minus_holds=40))
        self.assertEqual(json.loads(self.run_cli().stdout)["label"], "d")

    def test_usage_errors(self):
        self.assertEqual(self.run_cli(files=False).returncode, 2)  # nothing to label
        os.remove(self.paths["private.json"])
        self.assertEqual(self.run_cli().returncode, 2)
        with open(self.paths["private.json"], "w", encoding="utf-8") as f:
            json.dump(toy_case.private(0.99), f)
        self.write("expected.json", {"cases": {}})
        self.assertEqual(self.run_cli().returncode, 2)  # the key is not in the expected file
        r = common.run_tool("miss_label.py", "--attrition", "x", "--package-root", self.tmp.name)
        self.assertEqual(r.returncode, 2)  # not a gate


if __name__ == "__main__":
    unittest.main()
