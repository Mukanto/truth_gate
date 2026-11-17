import json
import os
import re
import tempfile
import unittest

import common
import toy_case

CLAIM = "The first series exceeds its mean."
TOOL = os.path.join(common.TOOLS, "check_skeletons_d.py")
PC_TOOL = os.path.join(common.PC, "tools", "check_skeletons.py")

SKELETON = '''"""SZ-1: %(claim)s"""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def plus(rng):
    """The claim is true."""
    return {"x": rng.standard_normal(%(shape)s) + 1.0}


def minus(rng):
    """The claim is false."""
    return {"x": rng.standard_normal(%(shape)s)}


def criterion(d):
    """Data keys: x, float %(shape)s, a series.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="SZ-1",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the mean is set to 0"),
    },
    controls=[Control("permute_x", ["C"], transform=lambda d, rng: {**d, "x": rng.permutation(d["x"])})],
)
'''


def shape_literal(shape):
    return "(" + ", ".join(str(n) for n in shape) + ("," if len(shape) == 1 else "") + ")"


def size_case(folder, shape, arms=("reference",), dims=None, arm_shapes=None, claim=CLAIM, sizes=None):
    """A one-key case. The brief says ``dims`` (default: ``shape``); the skeletons generate ``shape`` unless
    ``arm_shapes`` maps an arm to another shape. ``arms`` are the skeleton files written."""
    os.makedirs(os.path.join(folder, "skeletons"), exist_ok=True)
    dims = list(shape if dims is None else dims)
    brief = {"id": "SZ-1", "claim": claim,
             "data_keys": [{"key": "x", "shape": shape_literal(dims), "dims": dims, "dtype": "float64", "meaning": "a series"}],
             "sizes": sizes or " by ".join(str(n) for n in dims) + " observations"}
    with open(os.path.join(folder, "brief.json"), "w", encoding="utf-8") as f:
        json.dump(brief, f)
    paths = {"reference": "reference.py", "W0": os.path.join("skeletons", "W0.py"), "W1": os.path.join("skeletons", "W1.py")}
    for arm in arms:
        text = SKELETON % {"claim": claim, "shape": shape_literal((arm_shapes or {}).get(arm, shape))}
        with open(os.path.join(folder, paths[arm]), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return folder


def run(*args):
    r = common.run_tool("check_skeletons_d.py", "--package-root", common.PKG, *args)
    return r


class CheckSkeletonsDTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.tmp.name, "report.json")

    def case(self, shape, arms=("reference",), name="case", **kw):
        return size_case(os.path.join(self.tmp.name, name), shape, arms, **kw)

    def report(self):
        with open(self.out, encoding="utf-8") as f:
            return json.load(f)

    def test_constants_differ_from_phase_c_as_specified(self):
        import check_skeletons_d as d
        self.assertEqual((d.MAX_DIM, d.MAX_ELEMENTS, d.MAX_MS), (2000, 2000000, 1000.0))
        with open(PC_TOOL, encoding="utf-8") as f:
            pc = f.read()
        self.assertRegex(pc, r"MAX_DIM = 1000\b")
        self.assertRegex(pc, r"MAX_ELEMENTS = 500000\b")
        self.assertRegex(pc, r"MAX_MS = 100\.0\b")
        with open(TOOL, encoding="utf-8") as f:
            head = f.read(2500)
        self.assertIn("| array dimension cap | 1000 | 2000 |", head)  # the table of differences is at the top

    def test_other_code_is_the_phase_c_code(self):
        """Apart from the docstring, the three constants and main(), the file is Phase C's, line for line, except for
        lines added for R2-8 (every one carries the marker D-R2-8, or is a blank separator, or is the ``else:`` / call
        line of the premise block); no Phase C line is removed or changed other than the three constants."""
        import difflib
        with open(PC_TOOL, encoding="utf-8") as f:
            pc = f.read().splitlines()
        with open(TOOL, encoding="utf-8") as f:
            new = f.read().splitlines()
        body = lambda lines: lines[next(i for i, ln in enumerate(lines) if ln.startswith("import argparse")):]  # noqa: E731
        pc_b, new_b = body(pc), body(new)
        pc_main = next(i for i, ln in enumerate(pc_b) if ln.startswith("def main"))
        new_main = next(i for i, ln in enumerate(new_b) if ln.startswith("CASE_SKELETONS"))
        changed = [ln for ln in difflib.unified_diff(pc_b[:pc_main], new_b[:new_main], lineterm="", n=0)
                   if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        removed = [ln for ln in changed if ln[0] == "-"]
        added = [ln for ln in changed if ln[0] == "+" and "D-R2-8" not in ln and ln[1:].strip() != ""]
        self.assertEqual(sorted(re.match(r"-(\w+)", ln).group(1) for ln in removed), ["MAX_DIM", "MAX_ELEMENTS", "MAX_MS"])
        self.assertEqual(sorted(re.match(r"\+(\w+)", ln).group(1) for ln in added), ["MAX_DIM", "MAX_ELEMENTS", "MAX_MS"])

    def test_case_reference_only(self):
        r = run("--case", self.case((300,)), "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rep = self.report()
        self.assertEqual(set(rep), {"truth_gate_file", "SZ-1/reference"})
        self.assertEqual(rep["SZ-1/reference"]["issues"], [])
        root = os.path.realpath(common.PKG).lower().replace("\\", "/")
        self.assertTrue(os.path.realpath(rep["truth_gate_file"]).lower().replace("\\", "/").startswith(root))

    def test_case_with_both_arms(self):
        r = run("--case", self.case((300,), ("reference", "W0", "W1")), "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(set(self.report()), {"truth_gate_file", "SZ-1/reference", "SZ-1/W0", "SZ-1/W1"})

    def test_require_arms(self):
        c = self.case((300,), ("reference", "W0"))
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 0)
        r = run("--case", c, "--require-arms", "--out", self.out)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.report()["SZ-1/W1"]["issues"], ["missing file"])

    def test_missing_reference_is_an_issue(self):
        c = self.case((300,), ())
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        self.assertEqual(self.report()["SZ-1/reference"]["issues"], ["missing file"])

    def test_two_cases_in_one_call(self):
        a, b = self.case((300,), name="a"), self.case((200,), name="b")
        r = run("--case", a, "--case", b, "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("OK"), 2)

    def test_dimension_cap_is_2000(self):
        for n, ok in ((1999, True), (2000, True), (2001, False)):
            with self.subTest(n=n):
                r = run("--case", self.case((n,), name=f"d{n}"), "--out", self.out)
                self.assertEqual(r.returncode, 0 if ok else 1, r.stdout)
                if not ok:
                    self.assertTrue(any("exceeds the size cap" in i for i in self.report()["SZ-1/reference"]["issues"]))

    def test_dimension_cap_is_raised_from_1000(self):
        self.assertEqual(run("--case", self.case((1500,)), "--out", self.out).returncode, 0)

    def test_element_cap_is_2_million(self):
        ok = run("--case", self.case((1400, 1400), name="e1"), "--out", self.out)  # 1.96 million
        self.assertEqual(ok.returncode, 0, ok.stdout)
        bad = run("--case", self.case((1500, 1500), name="e2"), "--out", self.out)  # 2.25 million
        self.assertEqual(bad.returncode, 1)
        self.assertTrue(any("exceeds the size cap" in i for i in self.report()["SZ-1/reference"]["issues"]))

    # --- R2-8: the brief's dims are the shapes
    def issues(self, key="SZ-1/reference"):
        return self.report()[key]["issues"]

    def test_matching_dims_pass_in_two_dimensions(self):
        r = run("--case", self.case((500, 200)), "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_transposed_key_is_an_issue(self):
        # the brief says (500, 200); the skeleton generates (200, 500). Both numbers are in the brief's text, so the old
        # check ("every dimension number appears somewhere in the brief") passed it.
        c = self.case((200, 500), dims=(500, 200))
        r = run("--case", c, "--out", self.out)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("shape (200, 500) != brief dims (500, 200)" in i for i in self.issues()), self.issues())
        self.assertFalse(any("not found in the brief text" in i for i in self.issues()))  # the old check saw nothing

    def test_a_size_equal_to_a_number_in_the_claim_is_an_issue(self):
        claim = "The first series exceeds its mean by at least 200 units."
        ok = run("--case", self.case((300,), claim=claim, name="ok"), "--out", self.out)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        # the brief says 300 observations; the skeleton generates 200, and 200 is a number of the claim
        c = self.case((200,), dims=(300,), claim=claim, sizes="300 observations (200 units is the claimed excess)", name="bad")
        r = run("--case", c, "--out", self.out)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("shape (200,) != brief dims (300,)" in i for i in self.issues()), self.issues())
        self.assertFalse(any("not found in the brief text" in i for i in self.issues()))

    def test_a_brief_without_dims_is_an_issue(self):
        c = self.case((300,))
        path = os.path.join(c, "brief.json")
        with open(path, encoding="utf-8") as f:
            brief = json.load(f)
        del brief["data_keys"][0]["dims"]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(brief, f)
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        self.assertTrue(any("no valid dims" in i for i in self.issues()))
        brief["data_keys"][0]["dims"] = [300.0]  # not an int
        with open(path, "w", encoding="utf-8") as f:
            json.dump(brief, f)
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        self.assertTrue(any("no valid dims" in i for i in self.issues()))

    def test_shapes_differing_between_arms_is_an_issue(self):
        c = self.case((300,), ("reference", "W0", "W1"), arm_shapes={"W0": (250,)})
        r = run("--case", c, "--out", self.out)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.issues("SZ-1/reference"), [])
        w0 = self.issues("SZ-1/W0")
        self.assertTrue(any("shape (250,) != brief dims (300,)" in i for i in w0), w0)
        self.assertTrue(any(i.startswith("shapes differ from SZ-1/reference") for i in w0), w0)
        self.assertEqual(self.issues("SZ-1/W1"), [])

    def test_the_arms_are_compared_even_if_the_reference_is_the_odd_one(self):
        c = self.case((300,), ("reference", "W0", "W1"), arm_shapes={"reference": (250,)})
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        for arm in ("W0", "W1"):
            self.assertTrue(any(i.startswith("shapes differ from SZ-1/reference") for i in self.issues(f"SZ-1/{arm}")))

    def test_a_control_world_or_premise_output_with_another_shape_is_an_issue(self):
        c = self.case((300,))
        path = os.path.join(c, "reference.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        src = src.replace("controls=[", "premises=[Premise(\"p1\", lambda d, rng: {**d, \"x\": d[\"x\"][:10]}, \"assumed\", [\"C\"])],\n"
                          "    controls=[Control(\"cw\", [\"C\"], world=World(lambda rng: {\"x\": rng.standard_normal(299)})), ", 1)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        found = self.issues()
        self.assertIn("premise p1: x shape (10,) != brief dims (300,)", found)
        self.assertIn("control world cw: x shape (299,) != brief dims (300,)", found)

    def test_a_control_transform_output_with_another_shape_is_an_issue(self):
        c = self.case((300,))
        path = os.path.join(c, "reference.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        src = src.replace('lambda d, rng: {**d, "x": rng.permutation(d["x"])}', 'lambda d, rng: {**d, "x": rng.permutation(d["x"])[:10]}')
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        self.assertIn("control permute_x: x shape (10,) != brief dims (300,)", self.issues())

    def test_the_time_limit_text_says_1000_ms(self):
        with open(TOOL, encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("share the 100 ms limit", text)
        self.assertIn("share the 1000 ms limit", text)
        self.assertIn("250 ms", text)

    def test_docstring_cites_item_9_of_the_draft(self):  # D-R5-5 (R3B-6)
        with open(TOOL, encoding="utf-8") as f:
            first = f.readline()
        self.assertIn("3 item 9", first)
        self.assertNotIn("3 item 8", first)

    def test_static_checks_are_phase_cs(self):
        c = self.case((300,))
        path = os.path.join(c, "reference.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src.replace("rng.standard_normal(", "np.random.standard_normal(", 1))
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        rep = self.report()["SZ-1/reference"]
        self.assertIs(rep["loaded"], False)
        self.assertTrue(any("np.random" in i for i in rep["issues"]))

    def test_docstring_must_carry_the_brief_id_and_claim(self):
        c = self.case((300,))
        path = os.path.join(c, "reference.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src.replace('"""SZ-1: ', '"""OTHER-1: ', 1))
        self.assertEqual(run("--case", c, "--out", self.out).returncode, 1)
        self.assertIn("module docstring differs from '<id>: <claim>'", self.report()["SZ-1/reference"]["issues"])

    def test_toy_reference_passes(self):
        with tempfile.TemporaryDirectory() as t:
            folder = toy_case.write_case(os.path.join(t, "toy"), 0.9)
            r = run("--case", folder, "--out", self.out)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_phase_c_layout_still_works(self):
        c = self.case((300,))
        sk = os.path.join(self.tmp.name, "sk")
        os.makedirs(sk)
        with open(os.path.join(c, "reference.py"), encoding="utf-8") as f, \
                open(os.path.join(sk, "SZ-1.py"), "w", encoding="utf-8", newline="\n") as g:
            g.write(f.read())
        with open(os.path.join(c, "brief.json"), encoding="utf-8") as f:
            brief = json.load(f)
        briefs = os.path.join(self.tmp.name, "briefs.json")
        with open(briefs, "w", encoding="utf-8") as f:
            json.dump([brief], f)
        r = run("--skeletons", sk, "--briefs", briefs, "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(set(self.report()), {"truth_gate_file", "SZ-1"})

    def test_usage_errors(self):
        c = self.case((300,))
        self.assertEqual(common.run_tool("check_skeletons_d.py", "--case", c, "--out", self.out,
                                         "--package-root", self.tmp.name).returncode, 2)  # truth_gate not there
        self.assertEqual(run("--out", self.out).returncode, 2)  # neither layout
        briefs = os.path.join(self.tmp.name, "b.json")
        self.assertEqual(run("--case", c, "--skeletons", self.tmp.name, "--briefs", briefs, "--out", self.out).returncode, 2)
        self.assertEqual(run("--case", os.path.join(self.tmp.name, "nope"), "--out", self.out).returncode, 2)
        self.assertEqual(common.run_tool("check_skeletons_d.py", "--case", c).returncode, 2)  # required args missing


if __name__ == "__main__":
    unittest.main()
