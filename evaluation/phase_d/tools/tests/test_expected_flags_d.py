import json
import os
import tempfile
import unittest

import common
import toy_case
import expected_flags_d as ef
from structure_stat import import_truth_gate

PC_EXPECTED = os.path.join(common.PC, "EXPECTED_FLAGS.json")


def add_arm(case_dir, arm, null=False, extra_control=None, pairs=()):
    """A W-arm skeleton: the reference with an optional null world, an extra control and relational pairs."""
    with open(os.path.join(case_dir, "reference.py"), encoding="utf-8") as f:
        src = f.read()
    if null:
        src = src.replace('        "plus": World(plus),\n', '        "plus": World(plus),\n        "null": World(minus),\n')
    if pairs:
        src = src.replace("    controls=[", f"    relational={list(pairs)!r},\n    controls=[", 1)
    if extra_control:
        src = src.replace('    controls=[Control("permute_y"',
                          f'    controls=[Control("{extra_control}", ["C"], transform=lambda d, rng: {{**d, "x": rng.permutation(d["x"])}}), '
                          'Control("permute_y"', 1)
    os.makedirs(os.path.join(case_dir, "skeletons"), exist_ok=True)
    with open(os.path.join(case_dir, "skeletons", f"{arm}.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(src)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.case = toy_case.write_case(os.path.join(self.tmp.name, "case"), 0.9)
        self.out = os.path.join(self.tmp.name, "EXPECTED_FLAGS_D.json")

    def cli(self, *extra, case=True):
        args = ["--package-root", common.PKG, "--out", self.out, *extra]
        if case:
            args = ["--case", self.case, *args]
        return common.run_tool("expected_flags_d.py", *args)

    def read(self):
        with open(self.out, encoding="utf-8") as f:
            return json.load(f)


class BaseListTests(Base):
    @unittest.skipUnless(os.path.isfile(PC_EXPECTED), "Phase C's EXPECTED_FLAGS.json not found")
    def test_base_list_equals_phase_cs(self):
        with open(PC_EXPECTED, encoding="utf-8") as f:
            pc = json.load(f)
        self.assertEqual(ef.BASE, pc["base"])
        self.assertEqual(len(ef.BASE), 9)
        self.assertEqual(ef.check_base(PC_EXPECTED)[0], True)

    @unittest.skipUnless(os.path.isfile(PC_EXPECTED), "Phase C's EXPECTED_FLAGS.json not found")
    def test_per_case_lists_have_phase_cs_shape(self):
        # every Phase C in-scope case is the base list followed by HIGH_RATE:control:<id> / HIGH_RATE:probe:shuffle:<a>,<b>
        with open(PC_EXPECTED, encoding="utf-8") as f:
            cases = json.load(f)["cases"]
        for cid, rec in cases.items():
            if not rec.get("in_scope"):
                continue
            exp = rec["expected"]
            self.assertEqual(exp[:len(ef.BASE)], ef.BASE, cid)
            for flag in exp[len(ef.BASE):]:
                self.assertTrue(flag.startswith(("HIGH_RATE:control:", "HIGH_RATE:probe:shuffle:")), (cid, flag))


class EnumerationTests(Base):
    def test_reference_arm_of_the_toy(self):
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        out = self.read()
        self.assertEqual(set(out), {"note", "base", "base_checked_against", "cases"})
        self.assertEqual(list(out["cases"]), ["TOY-1/reference"])
        self.assertEqual(out["cases"]["TOY-1/reference"]["expected"], ef.BASE + ["HIGH_RATE:control:permute_y"])
        self.assertEqual(out["base"], ef.BASE)

    def test_each_arm_has_its_own_controls_and_pairs(self):
        add_arm(self.case, "W0")
        add_arm(self.case, "W1", null=True, extra_control="permute_x", pairs=[("x", "y")])
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        cases = self.read()["cases"]
        self.assertEqual(sorted(cases), ["TOY-1/W0", "TOY-1/W1", "TOY-1/reference"])
        self.assertEqual(cases["TOY-1/W0"]["expected"], ef.BASE + ["HIGH_RATE:control:permute_y"])
        # controls in declaration order, then the relational pairs
        self.assertEqual(cases["TOY-1/W1"]["expected"],
                         ef.BASE + ["HIGH_RATE:control:permute_x", "HIGH_RATE:control:permute_y",
                                    "HIGH_RATE:probe:shuffle:x,y"])

    def test_two_relational_pairs(self):
        add_arm(self.case, "W1", pairs=[("x", "y"), ("y", "x")])
        self.cli()
        self.assertEqual(self.read()["cases"]["TOY-1/W1"]["expected"][-2:],
                         ["HIGH_RATE:probe:shuffle:x,y", "HIGH_RATE:probe:shuffle:y,x"])

    def test_expected_flags_function_matches_the_gates_stream_names(self):
        from truth_gate.checks import build_plan
        from structure_stat import load_study_module
        from assemble import assemble
        add_arm(self.case, "W1", null=True, extra_control="permute_x", pairs=[("x", "y")])
        with open(os.path.join(self.case, "skeletons", "W1.py"), encoding="utf-8") as f:
            sk = f.read()
        study = load_study_module(assemble(sk, toy_case.FAULTY_BODY), "w1.py", "t").STUDY
        streams = [sd.name for sd in build_plan(study) if sd.kind in ("control",) or sd.name.startswith("probe:shuffle:")]
        self.assertEqual([f[len("HIGH_RATE:"):] for f in ef.expected_flags(study)[len(ef.BASE):]], streams)

    def test_study_option_takes_an_assembled_file(self):
        from assemble import assemble
        with open(os.path.join(self.case, "reference.py"), encoding="utf-8") as f:
            src = assemble(f.read(), toy_case.FAULTY_BODY)
        path = os.path.join(self.tmp.name, "faulty_W1.py")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        r = self.cli("--study", f"D-007/W1={path}", case=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(list(self.read()["cases"]), ["D-007/W1"])

    def test_the_output_is_usable_by_attributable_py(self):
        add_arm(self.case, "W1")
        self.cli()
        certs = {}
        for name, minus in (("faulty", 60), ("fixed", 4)):
            comp = {"id": "C", "flags": ["K2_HIGH_SIZE"] if name == "faulty" else [],
                    "counts": {"world:minus": {"holds": minus, "undefined": 0, "hard_undefined": 0, "n": 200}}, "bounds": {}}
            certs[name] = os.path.join(self.tmp.name, f"{name}.json")
            with open(certs[name], "w", encoding="utf-8") as f:
                json.dump({"body": {"verdict": "NOT_FALSIFIABLE" if name == "faulty" else "FALSIFIABLE", "load_error": None,
                                    "components": [comp]}}, f)
        r = common.run_tool("attributable.py", "--faulty", certs["faulty"], "--fixed", certs["fixed"], "--expected-file",
                            self.out, "--case", "TOY-1/W1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["attributable"])


class CheckAgainstPhaseCTests(Base):
    def test_a_different_base_stops_the_tool_and_writes_nothing(self):
        fake = os.path.join(self.tmp.name, "pc.json")
        with open(fake, "w", encoding="utf-8") as f:
            json.dump({"base": ef.BASE[:-1], "cases": {}}, f)
        r = self.cli("--phase-c-expected", fake)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("differs", r.stderr)
        self.assertFalse(os.path.exists(self.out))

    def test_an_equal_base_is_recorded(self):
        fake = os.path.join(self.tmp.name, "pc.json")
        with open(fake, "w", encoding="utf-8") as f:
            json.dump({"base": ef.BASE, "cases": {}}, f)
        self.assertEqual(self.cli("--phase-c-expected", fake).returncode, 0)
        self.assertEqual(self.read()["base_checked_against"], fake)

    def test_a_package_root_without_the_file_warns_but_writes(self):
        with tempfile.TemporaryDirectory() as t:
            # a package root that is a copy of the gate only: no evaluation/ folder
            import shutil
            shutil.copytree(os.path.join(common.PKG, "truth_gate"), os.path.join(t, "truth_gate"),
                            ignore=shutil.ignore_patterns("__pycache__"))
            r = common.run_tool("expected_flags_d.py", "--case", self.case, "--package-root", t, "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("not checked", r.stderr)
        self.assertIsNone(self.read()["base_checked_against"])

    def test_a_named_file_that_does_not_exist_is_a_usage_error(self):
        self.assertEqual(self.cli("--phase-c-expected", os.path.join(self.tmp.name, "nope.json")).returncode, 2)


class UsageErrorTests(Base):
    def test_usage_errors(self):
        self.assertEqual(self.cli(case=False).returncode, 2)  # neither --case nor --study
        self.assertEqual(self.cli("--study", "no-equals-sign", case=False).returncode, 2)
        self.assertEqual(self.cli("--study", "D-001/W1=" + os.path.join(self.tmp.name, "missing.py"), case=False).returncode, 2)
        os.remove(os.path.join(self.case, "faulty_body.py"))
        self.assertEqual(self.cli().returncode, 2)
        r = common.run_tool("expected_flags_d.py", "--case", self.case, "--package-root", self.tmp.name, "--out", self.out)
        self.assertEqual(r.returncode, 2)  # not a gate

    def test_a_body_that_does_not_assemble_is_a_usage_error(self):
        with open(os.path.join(self.case, "faulty_body.py"), "w", encoding="utf-8") as f:
            f.write("import math\n\ndef criterion(d):\n    return True\n")
        self.assertEqual(self.cli().returncode, 2)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
