import json
import os
import tempfile
import unittest

import common
import toy_case
import mech_check_bodies as mcb

HEAD = "import numpy as np\n\n\n"


def body(*lines):
    """A body whose criterion holds the given statements (each a source line, 4-space indented)."""
    return HEAD + "def criterion(d):\n" + "".join(f"    {ln}\n" for ln in lines) + "    return True\n"


class Case:
    def __init__(self, test, faulty=None, fixed=None, arms=()):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.dir = toy_case.write_case(os.path.join(self.tmp.name, "case"), 0.9, faulty_body=faulty, fixed_body=fixed)
        self.out = os.path.join(self.tmp.name, "MECH_CHECK.json")
        if arms:
            os.makedirs(os.path.join(self.dir, "skeletons"))
            for arm in arms:
                with open(os.path.join(self.dir, "reference.py"), encoding="utf-8") as f, \
                        open(os.path.join(self.dir, "skeletons", f"{arm}.py"), "w", encoding="utf-8", newline="\n") as g:
                    g.write(f.read())

    def report(self):
        return mcb.check_case(self.dir)

    def cli(self, *extra):
        return common.run_tool("mech_check_bodies.py", "--case", self.dir, "--out", self.out, *extra)


class ListedComparisonTests(unittest.TestCase):
    def listed(self, *lines):
        return mcb.check_body(body(*lines), "b.py")["listed_comparisons"]

    def test_each_summary_call_against_a_constant_is_listed(self):
        cases = {
            "np.mean(d['x']) > 0.3": "mean",
            "d['x'].mean() < 0.3": "mean",
            "np.var(d['x']) >= 1": "var",
            "np.std(d['x']) <= 1e-9": "std",
            "np.min(d['x']) == 0": "min",
            "d['x'].max() != 3": "max",
            "min(d['x']) > 0": "min",
            "max(d['x']) > 0": "max",
            "np.all(d['x'] > 0) == 1": "all",
            "np.any(d['x']) == 0": "any",
            "all(d['x']) == 1": "all",
            "any(d['x']) == 1": "any",
            "np.linalg.norm(d['x']) == 0": "linalg.norm",
            "np.isnan(d['x']).any() == 0": "any",
            "np.isnan(d['x']) == 0": "isnan",
            "np.isfinite(d['x']) == 1": "isfinite",
            "np.ptp(d['x']) < 1": "ptp",
            "d['x'].ptp() < 1": "ptp",
            "np.median(d['x']) > -0.5": "median",
        }
        for text, name in cases.items():
            with self.subTest(text):
                found = self.listed(text)
                self.assertEqual([e["call"] for e in found], [name], text)
                self.assertEqual(found[0]["file"], "b.py")
                self.assertEqual(found[0]["line"], 5)
                self.assertEqual(found[0]["text"], text)

    def test_constant_on_the_left_and_chains(self):
        self.assertEqual([e["op"] for e in self.listed("0.3 < np.mean(d['x'])")], ["<"])
        found = self.listed("0 < np.max(d['x']) < 10")
        self.assertEqual([(e["call"], e["op"]) for e in found], [("max", "<"), ("max", "<")])
        self.assertEqual(self.listed("-0.5 < np.median(d['x'])")[0]["call"], "median")
        self.assertEqual(self.listed("np.mean(d['x']) > +2")[0]["call"], "mean")

    def test_a_listed_call_anywhere_in_the_side_counts(self):
        # T3-3 (a): the side may be a wrapper or an expression around the call
        cases = {
            "float(np.mean(d['x'])) > 0.3": ("mean", "constant"),
            "np.mean(d['x']) - 1 > 0": ("mean", "constant"),
            "abs(np.std(d['x']) - np.std(d['y'])) < 1e-9": ("abs", "constant"),  # D-R4-1: abs is a listed call
            "np.max(d['x']) - np.min(d['x']) == 0": ("max", "constant"),
            "2 * np.var(d['x']) >= 1": ("var", "constant"),
            "bool(np.all(np.isfinite(d['x']))) == 1": ("all", "constant"),
            "(np.mean(d['x']) + 1) / 2 > 0.5": ("mean", "constant"),
        }
        for text, (call, kind) in cases.items():
            with self.subTest(text):
                found = self.listed(text)
                self.assertEqual(len(found), 1, text)
                self.assertEqual((found[0]["call"], found[0]["kind"]), (call, kind))
                self.assertIn(call, found[0]["calls"])
        self.assertEqual(self.listed("np.max(d['x']) - np.min(d['x']) == 0")[0]["calls"], ["max", "min"])

    def test_the_other_side_kinds(self):
        for text, kind in (("np.mean(d['x']) > 0.3", "constant"), ("np.mean(d['x']) > -0.3", "constant"),
                           ("np.mean(d['x']) > 2 * 0.5", "constant"), ("np.mean(d['x']) > 1 - 1e-9", "constant"),
                           ("np.mean(d['x']) > -(2 ** 3)", "constant"), ("np.mean(d['x']) > thr", "name"),
                           ("thr <= np.mean(d['x'])", "name"), ("0.3 < float(np.mean(d['x']))", "constant")):
            with self.subTest(text):
                found = self.listed(f"thr = 0.3; _ = ({text})")
                self.assertEqual([e["kind"] for e in found], [kind], text)

    def test_chains_are_read_pair_by_pair(self):
        found = self.listed("0 < float(np.max(d['x'])) < thr")
        self.assertEqual([(e["op"], e["kind"]) for e in found], [("<", "constant"), ("<", "name")])
        # a pair whose other side is not a constant or a name is not listed even inside a chain
        found = self.listed("thr < np.max(d['x']) < np.min(d['y'])")
        self.assertEqual([(e["op"], e["kind"]) for e in found], [("<", "name")])

    def test_things_that_are_not_listed(self):
        for text in ("np.mean(d['x']) > np.mean(d['y'])",       # the other side holds a call
                     "np.mean(d['x']) > len(d['y'])",           # the other side is a call
                     "np.mean(d['x']) > d['y'][0]",             # a subscript is neither a constant nor a name
                     "np.mean(d['x']) > thr + 1",               # arithmetic with a name is not arithmetic of literals
                     "np.mean(d['x']) > 3 * thr",
                     "d['x'].shape[0] > 3",                     # not a listed call
                     "np.prod(d['x']) > 3",                     # prod is not in the list
                     "float(d['x'].shape[0]) - 1 > 0",
                     "np.mean(d['x']) is None",                 # identity
                     "np.mean(d['x']) in (1, 2)",               # membership
                     "np.mean(d['x']) == True",                 # a bool is not a numeric constant
                     "np.mean(d['x']) > 3j",                    # complex is not
                     "d['x'].shape[0] > 3",
                     "np.linalg.det(d['x']) > 0",
                     "np.linalg.norm"
                     ):
            with self.subTest(text):
                self.assertEqual(self.listed(f"thr = 0.3; _ = ({text})"), [], text)

    def test_comparison_inside_a_helper_is_listed_with_its_line(self):
        src = HEAD + "def helper(x):\n    return x.std() < 1e-6\n\n\ndef criterion(d):\n    return helper(d['x'])\n"
        found = mcb.check_body(src, "faulty_body.py")["listed_comparisons"]
        self.assertEqual([(e["file"], e["line"], e["text"]) for e in found], [("faulty_body.py", 5, "x.std() < 1e-6")])

    def test_multiline_comparison_text_is_one_line(self):
        found = self.listed("(np.mean(d['x']) >\n            0.3)")
        self.assertEqual(found[0]["text"], "np.mean(d['x']) > 0.3")


class BodyIssueTests(unittest.TestCase):
    def issues(self, src):
        return mcb.check_body(src, "b.py")["issues"]

    def test_the_toy_bodies_are_clean(self):
        for src in (toy_case.FAULTY_BODY, toy_case.FIXED_BODY):
            self.assertEqual(mcb.check_body(src, "b.py")["issues"], [])

    def test_module_level_rule(self):
        for src in (HEAD + "T = 0.3\n\n\ndef criterion(d):\n    return True\n",
                    HEAD + "np.seterr(all='ignore')\n\n\ndef criterion(d):\n    return True\n",
                    "import os\n\n\ndef criterion(d):\n    return True\n",
                    '"""doc"""\n' + HEAD + "def criterion(d):\n    return True\n",
                    HEAD + "class K:\n    pass\n\n\ndef criterion(d):\n    return True\n"):
            with self.subTest(src):
                found = self.issues(src)
                self.assertTrue(any(i.startswith("module level") for i in found), found)

    def test_exactly_one_criterion(self):
        self.assertTrue(any("exactly one" in i for i in self.issues(HEAD + "def helper(d):\n    return 1\n")))
        two = HEAD + "def criterion(d):\n    return 1\n\n\ndef criterion(d):\n    return 2\n"
        self.assertTrue(any("exactly one" in i for i in self.issues(two)))

    def test_syntax_error(self):
        self.assertTrue(self.issues("def criterion(d:\n")[0].startswith("syntax error"))

    def test_banned_names_numpy_file_functions_and_dunders(self):
        from check_skeletons_d import BANNED_NAMES, BANNED_NP_ATTR
        for name in sorted(BANNED_NAMES):
            with self.subTest(name):
                self.assertTrue(any(f"name {name} " in i for i in self.issues(body(f"{name}"))), name)
        for attr in sorted(BANNED_NP_ATTR):
            with self.subTest(attr):
                self.assertTrue(any(f"attribute .{attr}" in i for i in self.issues(body(f"np.{attr}"))), attr)
        self.assertTrue(any("dunder attribute .__class__" in i for i in self.issues(body("d.__class__"))))
        self.assertTrue(any("dunder attribute .__dict__" in i for i in self.issues(body("d.__dict__"))))
        self.assertEqual([i for i in self.issues(body("x = d.__init__")) if "dunder" in i], [])  # __init__ is allowed
        # the same sets as check_skeletons_d, not a copy
        self.assertIs(mcb.BANNED_NAMES, BANNED_NAMES)
        self.assertIs(mcb.BANNED_NP_ATTR, BANNED_NP_ATTR)

    def test_a_banned_name_is_found_in_a_helper_and_in_defaults(self):
        src = HEAD + "def helper(x, y=open):\n    return x\n\n\ndef criterion(d):\n    return helper(1)\n"
        self.assertTrue(any("name open" in i for i in self.issues(src)))

    def test_a_clean_body_with_comparisons_has_no_issue_only_a_list(self):
        res = mcb.check_body(body("ok = np.mean(d['x']) > 0.3"), "b.py")
        self.assertEqual(res["issues"], [])
        self.assertEqual(len(res["listed_comparisons"]), 1)


class RandomnessRuleTests(unittest.TestCase):
    """T3-3 (b): only np.random.default_rng(<integer literal>); aliasing is refused (Phase C: mech_check_twins.py 102-204)."""

    def issues(self, *lines, head=HEAD):
        src = head + "def criterion(d):\n" + "".join(f"    {ln}\n" for ln in lines) + "    return True\n"
        return mcb.check_body(src, "b.py")["issues"]

    def test_default_rng_with_an_integer_literal_is_allowed(self):
        self.assertEqual(self.issues("rng = np.random.default_rng(12345)", "x = rng.random(3)", "y = rng.standard_normal(2)"), [])
        self.assertEqual(self.issues("x = np.random.default_rng(0).random(3)"), [])

    def test_default_rng_needs_one_integer_literal(self):
        for call in ("np.random.default_rng()", "np.random.default_rng(seed)", "np.random.default_rng(1.5)",
                     "np.random.default_rng(-1)", "np.random.default_rng(True)", "np.random.default_rng(0, 1)",
                     "np.random.default_rng(seed=3)", "np.random.default_rng([1, 2])"):
            with self.subTest(call):
                found = self.issues(f"rng = {call}")
                self.assertTrue(any("default_rng without a single int literal seed" in i for i in found), (call, found))

    def test_other_np_random_uses_are_refused(self):
        for use in ("np.random.seed(1)", "np.random.rand(3)", "np.random.randn(3)", "np.random.shuffle(d['x'])",
                    "np.random.RandomState(1)", "np.random.Generator", "np.random.permutation(3)", "np.random.normal()"):
            with self.subTest(use):
                found = self.issues(use)
                self.assertTrue(any("np.random used other than as np.random.default_rng" in i for i in found), (use, found))

    def test_aliasing_np_random_or_np_is_refused(self):
        for line in ("r = np.random", "r = np", "a, b = np, 1", "r: object = np.random", "r = (q := np.random)", "r = [np.random]"):
            with self.subTest(line):
                found = self.issues(line)
                self.assertTrue(found, line)
        self.assertTrue(any("numpy alias assignment" in i for i in self.issues("r = np.random")))
        self.assertTrue(any("numpy alias assignment" in i for i in self.issues("r = np")))
        self.assertTrue(any("numpy alias assignment" in i for i in self.issues("a, b = np, 1")))

    def test_capturing_default_rng_is_refused(self):
        for line in ("f = np.random.default_rng", "g = [np.random.default_rng]", "h = (np.random.default_rng)"):
            with self.subTest(line):
                self.assertTrue(any("default_rng captured without being called" in i for i in self.issues(line)), line)
        self.assertTrue(any("bare name default_rng" in i for i in self.issues("rng = default_rng(1)")))

    def test_import_from_is_refused_even_inside_a_function(self):
        for line in ("from numpy.random import default_rng", "import numpy.random", "from numpy import random",
                     "import numpy as other", "import math"):
            with self.subTest(line):
                found = self.issues(line)
                self.assertTrue(any("import other than the module-level 'import numpy as np'" in i for i in found), (line, found))
        found = mcb.check_body("from numpy.random import default_rng\nimport numpy as np\n\n\ndef criterion(d):\n    return True\n", "b.py")["issues"]
        self.assertTrue(any("import other than" in i for i in found))
        self.assertTrue(any(i.startswith("module level") for i in found))

    def test_a_generator_method_on_another_name_is_not_np_random(self):
        self.assertEqual(self.issues("rng = np.random.default_rng(1)", "x = rng.random(3)"), [])
        self.assertEqual(self.issues("g = d['x']", "y = g.random"), [])

    def test_an_aliased_numpy_binding_is_checked_too(self):
        # the module-level rule refuses `import numpy as other`, and the randomness rule treats the alias as numpy
        found = mcb.check_body("import numpy as other\n\n\ndef criterion(d):\n    return other.random.rand(2) is None\n", "b.py")["issues"]
        self.assertTrue(any("other.random used other than as other.random.default_rng" in i for i in found), found)

    def test_the_phase_c_source_is_cited(self):
        self.assertIn("evaluation/phase_c/tools/mech_check_twins.py", mcb.__doc__)
        self.assertIn("lines 197-204", mcb.__doc__)


class DecoratorAndWholeTreeTests(unittest.TestCase):
    """T3-4: decorators are refused anywhere; the banned-name scan covers decorators and default arguments."""

    def issues(self, src):
        return mcb.check_body(src, "b.py")["issues"]

    def test_a_decorated_module_level_function_is_refused(self):
        src = HEAD + "@np.vectorize\ndef helper(x):\n    return x\n\n\ndef criterion(d):\n    return True\n"
        found = self.issues(src)
        self.assertTrue(any("decorator on helper (line 5)" in i for i in found), found)

    def test_a_nested_decorator_is_refused(self):
        src = HEAD + "def criterion(d):\n    @np.vectorize\n    def inner(x):\n        return x\n    return True\n"
        self.assertTrue(any("decorator on inner" in i for i in self.issues(src)))

    def test_a_decorated_class_is_refused(self):
        src = HEAD + "def criterion(d):\n    @staticmethod\n    class K:\n        pass\n    return True\n"
        self.assertTrue(any("decorator on K" in i for i in self.issues(src)))

    def test_a_banned_name_in_a_decorator_is_found(self):
        src = HEAD + "@print(1)\ndef criterion(d):\n    return True\n"
        found = self.issues(src)
        self.assertTrue(any("name print" in i for i in found), found)
        self.assertTrue(any("decorator on criterion" in i for i in found))

    def test_banned_names_and_attributes_in_default_arguments_are_found(self):
        for default, expect in (("open", "name open"), ("np.load", "attribute .load"), ("d.__class__", "dunder attribute .__class__"),
                                ("eval", "name eval"), ("np.memmap", "attribute .memmap")):
            with self.subTest(default):
                src = HEAD + f"def helper(x, y={default}):\n    return x\n\n\ndef criterion(d):\n    return True\n"
                self.assertTrue(any(expect in i for i in self.issues(src)), (default, self.issues(src)))
        src = HEAD + "def helper(*, y=open):\n    return 1\n\n\ndef criterion(d, z=getattr):\n    return True\n"
        found = self.issues(src)
        self.assertTrue(any("name open" in i for i in found) and any("name getattr" in i for i in found), found)

    def test_a_banned_name_in_a_lambda_and_a_comprehension_is_found(self):
        src = HEAD + "def criterion(d):\n    f = lambda: open\n    g = [eval for _ in d]\n    return True\n"
        found = self.issues(src)
        self.assertTrue(any("name open" in i for i in found) and any("name eval" in i for i in found), found)

    def test_the_toy_bodies_stay_clean(self):
        for src in (toy_case.FAULTY_BODY, toy_case.FIXED_BODY):
            self.assertEqual(self.issues(src), [])


class FreeNameTests(unittest.TestCase):
    """D-R4-1 (R3-1): free names, global and nonlocal, signatures, and the larger listed-call set."""

    def issues(self, src, skeleton=()):
        return mcb.check_body(src, "b.py", skeleton)["issues"]

    def test_reading_a_skeleton_name_is_refused(self):
        src = HEAD + "def criterion(d):\n    return bool(np.mean(d['x']) > THRESHOLD)\n"
        found = self.issues(src, skeleton={"THRESHOLD", "N", "rng"})
        self.assertIn("reads module-level name THRESHOLD (line 5)", found)
        for name in ("N", "rng"):
            src = HEAD + f"def criterion(d):\n    return bool({name} > 0)\n"
            self.assertIn(f"reads module-level name {name} (line 5)", self.issues(src, skeleton={"THRESHOLD", "N", "rng"}))

    def test_a_name_nobody_defines_is_undefined(self):
        found = self.issues(HEAD + "def criterion(d):\n    return bool(MYSTERY > 0)\n", skeleton={"THRESHOLD"})
        self.assertIn("undefined name MYSTERY (line 5)", found)
        self.assertIn("undefined name THRESHOLD (line 5)", self.issues(HEAD + "def criterion(d):\n    return THRESHOLD\n"))

    def test_allowed_names(self):
        src = (HEAD + "def helper(a, k=3, *rest, flag=True, **kw):\n    t = a + k\n    return [t * i for i in range(len(rest))]\n\n\n"
               "def criterion(d):\n    f = lambda u, v=1: u + v\n    try:\n        z = helper(d['x'])\n    except ValueError as err:\n"
               "        z = [err]\n    def inner(q):\n        return q + f(1)\n    for i, y in enumerate(d):\n        pass\n"
               "    return bool(np.all(np.isfinite(inner(np.zeros(2)))) and len(z) >= 0 and abs(-1) == 1)\n")
        self.assertEqual([i for i in self.issues(src, skeleton={"THRESHOLD"})
                          if "undefined name" in i or "module-level name" in i], [])

    def test_helpers_of_the_file_and_forward_references_are_allowed(self):
        src = HEAD + "def criterion(d):\n    return bool(later(d))\n\n\ndef later(d):\n    return True\n"
        self.assertEqual([i for i in self.issues(src) if "name" in i], [])

    def test_a_name_local_to_another_function_is_not_visible(self):
        src = HEAD + "def helper(x):\n    secret = 1\n    return x\n\n\ndef criterion(d):\n    return bool(secret)\n"
        self.assertIn("undefined name secret (line 10)", self.issues(src))

    def test_names_in_defaults_and_decorator_arguments_are_read_at_module_level(self):
        src = HEAD + "def helper(x, y=THRESHOLD):\n    return x\n\n\ndef criterion(d):\n    return True\n"
        self.assertIn("reads module-level name THRESHOLD (line 4)", self.issues(src, skeleton={"THRESHOLD"}))
        src = HEAD + "def helper(x, y=np.pi):\n    return x\n\n\ndef criterion(d):\n    return True\n"
        self.assertFalse([i for i in self.issues(src) if "name" in i and "np" in i and "undefined" in i])

    def test_global_and_nonlocal_are_refused(self):
        found = self.issues(HEAD + "def criterion(d):\n    global COUNTER\n    COUNTER = 1\n    return True\n")
        self.assertIn("global statement (line 5)", found)
        found = self.issues(HEAD + "def criterion(d):\n    n = 0\n    def inner():\n        nonlocal n\n        n = 1\n"
                            "    inner()\n    return True\n")
        self.assertIn("nonlocal statement (line 7)", found)

    def test_criterion_signature(self):
        for sig, expect in (("d, k=1", "signature has default values"), ("d, *, k=1", "signature has default values"),
                            ("d, k", "signature is not (d)"), ("x", "signature is not (d)"), ("*d", "signature is not (d)"),
                            ("d: dict", "signature has annotations"), ("d) -> bool:#", "signature has annotations")):
            with self.subTest(sig):
                src = HEAD + f"def criterion({sig}):\n    return True\n" if not sig.endswith("#") else \
                    HEAD + "def criterion(d) -> bool:\n    return True\n"
                found = self.issues(src)
                self.assertTrue(any(i.startswith("criterion:") and expect in i for i in found), (sig, found))
        self.assertEqual([i for i in self.issues(HEAD + "def criterion(d):\n    return True\n") if i.startswith("criterion:")], [])

    def test_helper_defaults_must_be_literals(self):
        ok = ("0", "1.5", "-1", "'text'", "None", "True", "(1, 2)", "(1, ('a', None))", "()", "1e-9")
        for default in ok:
            with self.subTest(default):
                src = HEAD + f"def helper(x, y={default}):\n    return x\n\n\ndef criterion(d):\n    return True\n"
                self.assertEqual([i for i in self.issues(src) if "default value" in i], [], default)
        bad = ("[]", "{}", "set()", "[1, 2]", "{'a': 1}", "np.pi", "np.zeros(3)", "len('a')", "1 + 2", "(1, [])", "lambda: 1",
               "[i for i in range(3)]", "x")
        for default in bad:
            with self.subTest(default):
                src = HEAD + f"def helper(x, y={default}):\n    return x\n\n\ndef criterion(d):\n    return True\n"
                found = self.issues(src)
                self.assertTrue(any("helper: default value" in i and "is not a literal" in i for i in found), (default, found))
        src = HEAD + "def helper(x, *, k=[]):\n    return x\n\n\ndef criterion(d):\n    return True\n"
        self.assertTrue(any("default value" in i for i in self.issues(src)))  # keyword-only defaults too
        src = HEAD + "def criterion(d):\n    f = lambda u, v=[]: u\n    return True\n"
        self.assertTrue(any("lambda: default value" in i for i in self.issues(src)))

    def test_the_listed_call_set(self):
        from check_skeletons_d import BANNED_NAMES  # noqa: F401
        for name in ("mean", "var", "std", "ptp", "allclose", "isclose", "count_nonzero", "unique", "all", "any", "median",
                     "nanmean", "nanstd", "nanvar", "array_equal", "sum", "max", "min", "abs", "isnan", "isfinite"):
            with self.subTest(name):
                found = mcb.check_body(body(f"ok = np.{name}(d['x']) == 0"), "b.py")["listed_comparisons"]
                self.assertEqual([e["call"] for e in found], [name])
        self.assertEqual([e["call"] for e in mcb.check_body(body("ok = np.linalg.norm(d['x']) == 0"), "b.py")["listed_comparisons"]],
                         ["linalg.norm"])
        for name in ("min", "max", "all", "any", "sum", "abs", "len"):
            with self.subTest("builtin " + name):
                found = mcb.check_body(body(f"ok = {name}(d['x']) == 0"), "b.py")["listed_comparisons"]
                self.assertEqual([e["call"] for e in found], [name])
        self.assertEqual(mcb.DIST_CALLS | {"isnan", "isfinite"}, mcb.SUMMARY_CALLS)

    def test_the_reviewers_demo_body(self):
        demo = (HEAD + "def helper(y, acc=[]):\n    global COUNTER\n    COUNTER = 1\n    return np.sum(np.abs(y)) == 0\n\n\n"
                "def criterion(d):\n    y = d['y']\n    if THRESHOLD > 1:\n        return None\n"
                "    return bool(len(np.unique(y)) == 2 and np.count_nonzero(y) < 3 and helper(y))\n")
        res = mcb.check_body(demo, "demo.py", {"THRESHOLD"})
        found = res["issues"]
        self.assertTrue(any(i.startswith("reads module-level name THRESHOLD") for i in found), found)
        self.assertTrue(any(i.startswith("global statement") for i in found), found)
        self.assertTrue(any("helper: default value '[]' is not a literal" in i for i in found), found)
        got = {(e["text"], e["call"]) for e in res["listed_comparisons"]}
        self.assertIn(("np.sum(np.abs(y)) == 0", "sum"), got)
        self.assertIn(("len(np.unique(y)) == 2", "len"), got)
        self.assertIn(("np.count_nonzero(y) < 3", "count_nonzero"), got)

    def test_the_case_report_uses_the_skeleton_names(self):
        c = Case(self, fixed=HEAD + "def criterion(d):\n    return bool(N > 1)\n")
        rep = c.report()
        self.assertFalse(rep["ok"])
        self.assertIn("fixed_body.py: reads module-level name N (line 5)", rep["issues"])

    def test_the_toy_bodies_have_no_name_or_signature_issue(self):
        for src in (toy_case.FAULTY_BODY, toy_case.FIXED_BODY):
            self.assertEqual(self.issues(src, skeleton={"N", "PHI", "plus", "minus", "STUDY"}), [])


class ScopingTests(unittest.TestCase):
    """D-R5-1 (R3B-1): free names by Python's scoping rules; the skeleton's names before the builtins."""

    @classmethod
    def setUpClass(cls):
        import ast
        from assemble import AssembleError, assemble, top_level_names
        cls.assemble, cls.AssembleError = staticmethod(assemble), AssembleError
        cls.skeleton = toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": 0.9}
        cls.skeleton = cls.skeleton.replace("N = 300\n", "N = 300\nTHRESHOLD = 0.9\n\n\ndef max(*a):\n    return 99\n", 1)
        cls.names = top_level_names(ast.parse(cls.skeleton))

    BODIES = {
        "comprehension variable reused after the comprehension":
            HEAD + "def criterion(d):\n    sizes = [N for N in range(3)]\n    return bool(len(d['x']) > N)\n",
        "name bound only in a nested function":
            HEAD + "def criterion(d):\n    def helper():\n        THRESHOLD = 0.1\n        return THRESHOLD\n"
                   "    return bool(np.mean(d['x']) > THRESHOLD)\n",
        "name bound only as a lambda parameter":
            HEAD + "def criterion(d):\n    f = lambda THRESHOLD: THRESHOLD\n    return bool(np.mean(d['x']) > THRESHOLD)\n",
        "builtin shadowed by a skeleton function":
            HEAD + "def criterion(d):\n    return bool(max(1, 2) > 50)\n",
    }

    def test_each_body_gets_a_name_issue_and_is_refused_by_assemble(self):
        expect = {"comprehension variable reused after the comprehension": "reads module-level name N (line 6)",
                  "name bound only in a nested function": "reads module-level name THRESHOLD (line 8)",
                  "name bound only as a lambda parameter": "reads module-level name THRESHOLD (line 6)",
                  "builtin shadowed by a skeleton function": "reads module-level name max (line 5)"}
        self.assertIn("THRESHOLD", self.names)
        self.assertIn("max", self.names)
        for name, body in self.BODIES.items():
            with self.subTest(name):
                issues = mcb.check_body(body, "b.py", self.names)["issues"]
                self.assertIn(expect[name], issues)
                with self.assertRaises(self.AssembleError) as cm:
                    self.assemble(self.skeleton, body)
                self.assertIn(expect[name], str(cm.exception))

    def test_without_the_skeleton_names_the_same_bodies_are_undefined_names_or_builtins(self):
        issues = mcb.check_body(self.BODIES["name bound only as a lambda parameter"], "b.py")["issues"]
        self.assertIn("undefined name THRESHOLD (line 6)", issues)
        self.assertEqual([i for i in mcb.check_body(self.BODIES["builtin shadowed by a skeleton function"], "b.py")["issues"]
                          if "name" in i], [])  # a real builtin when no skeleton redefines it

    def test_a_body_with_comprehensions_nested_helpers_and_lambdas_passes(self):
        body = (HEAD + "def helper(a, b=1):\n    tot = sum(v for v in a)\n    return tot + b\n\n\n"
                "def criterion(d):\n    xs = [v * 2 for v in d['x']]\n    ys = {k: k * k for k in range(3)}\n"
                "    zs = {w for w in xs if w > 0}\n    def inner(q, r=2):\n        loc = [u + r for u in q]\n        return loc\n"
                "    f = lambda p, s=1: p + s + len(xs)\n    g = lambda: [t for t in xs if t > f(1)]\n"
                "    total = helper(xs) + f(1) + len(ys) + len(zs) + len(inner(xs)) + len(g())\n"
                "    nested = [[a * b for b in range(2)] for a in range(3)]\n"
                "    if (n := len(nested)) > 1:\n        total += n\n"
                "    return bool(total > 0 and any(e > 0 for e in xs))\n")
        self.assertEqual([i for i in mcb.check_body(body, "b.py", self.names)["issues"] if "name" in i], [])
        compile(self.assemble(self.skeleton, body), "<a>", "exec")

    def test_scoping_details(self):
        f = lambda src: [i for i in mcb.check_body(HEAD + src, "b.py", {"N", "X"})["issues"] if "name" in i]  # noqa: E731
        # a name bound in an enclosing function is visible to a nested function and to a lambda
        self.assertEqual(f("def criterion(d):\n    a = 1\n    def h():\n        return a\n    g = lambda: a\n    return h() + g()\n"), [])
        # a comprehension variable is not visible after the comprehension, nor in a sibling comprehension
        self.assertEqual(f("def criterion(d):\n    s = [X for X in d]\n    return [X for _ in d]\n"),
                         ["reads module-level name X (line 6)"])
        # a walrus inside a comprehension binds in the enclosing function
        self.assertEqual(f("def criterion(d):\n    s = [(X := v) for v in d]\n    return X\n"), [])
        # the first iterable of a comprehension is evaluated in the enclosing scope
        self.assertEqual(f("def criterion(d):\n    return [v for v in N]\n"), ["reads module-level name N (line 5)"])
        # a name bound later in the same function is local
        self.assertEqual(f("def criterion(d):\n    def h():\n        return later\n    later = 1\n    return h()\n"), [])
        # a class body's names are not visible to a method
        self.assertEqual(f("def criterion(d):\n    class K:\n        X = 1\n        def m(self):\n            return X\n    return K\n"),
                         ["reads module-level name X (line 8)"])
        # parameters, for targets, with targets, except names, imports-free bindings
        self.assertEqual(f("def criterion(d, *rest, **kw):\n    for i, (j, k) in enumerate(d):\n        pass\n"
                           "    with d as w:\n        pass\n    try:\n        pass\n    except ValueError as err:\n        err\n"
                           "    return rest, kw, i, j, k, w\n"), [])
        # a default value is evaluated in the enclosing scope
        self.assertEqual(f("def h(x, y=N):\n    return x\n\n\ndef criterion(d):\n    return h(1)\n"),
                         ["reads module-level name N (line 4)"])
        # a lambda parameter does not leak into the function
        self.assertEqual(f("def criterion(d):\n    g = lambda X: X\n    return g(1) + X\n"), ["reads module-level name X (line 6)"])


class DocstringConstantsTests(unittest.TestCase):
    """D-R5-5 (R3B-6): the docstring names the constants, not a copy of their contents."""

    def test_listed_call_set_is_described_by_the_constants(self):
        doc = mcb.__doc__
        self.assertIn("``SUMMARY_CALLS``", doc)
        self.assertIn("``BUILTIN_SUMMARY_CALLS``", doc)
        self.assertNotIn("a call of mean, var, std, min, max, all, any", doc)
        self.assertNotIn("for the builtins min, max, all and any", doc)


class AssembledTests(unittest.TestCase):
    def test_toy_case_report(self):
        rep = Case(self).report()
        self.assertTrue(rep["ok"], rep["issues"])
        self.assertEqual(rep["case"], "TOY-1")
        self.assertEqual(set(rep["bodies"]), {"faulty_body.py", "fixed_body.py"})
        self.assertEqual(set(rep["assembled"]), {"reference/faulty", "reference/fixed", "reference"})
        self.assertEqual(rep["assembled"]["reference"], {"single_difference": True})

    def test_all_skeletons_present_are_assembled(self):
        rep = Case(self, arms=("W0", "W1")).report()
        self.assertEqual(set(rep["assembled"]), {f"{a}/{t}" for a in ("reference", "W0", "W1") for t in ("faulty", "fixed")}
                         | {"reference", "W0", "W1"})
        self.assertTrue(rep["ok"], rep["issues"])

    def test_a_budget_targets_or_deterministic_keyword_is_an_issue(self):
        for kw in ("budget=Budget()", "targets=Targets()", "deterministic=True"):
            with self.subTest(kw):
                c = Case(self)
                ref = os.path.join(c.dir, "reference.py")
                with open(ref, encoding="utf-8") as f:
                    src = f.read()
                self.assertIn("    controls=[", src)
                with open(ref, "w", encoding="utf-8", newline="\n") as f:
                    f.write(src.replace("    controls=[", f"    {kw},\n    controls=[", 1))
                rep = c.report()
                self.assertFalse(rep["ok"])
                name = kw.split("=")[0]
                self.assertIn(f"reference/faulty: Study(...) has a {name} keyword (default Budget, Targets and "
                              "deterministic are required)", rep["issues"])
                self.assertIn(f"reference/fixed: Study(...) has a {name} keyword (default Budget, Targets and "
                              "deterministic are required)", rep["issues"])

    def test_a_body_that_does_not_assemble_is_an_issue(self):
        rep = Case(self, faulty="import math\n\ndef criterion(d):\n    return True\n").report()
        self.assertFalse(rep["ok"])
        self.assertTrue(any(i.startswith("reference/faulty: does not assemble") for i in rep["issues"]))
        self.assertIn("reference/fixed", rep["assembled"])

    def test_missing_reference_is_an_issue(self):
        c = Case(self)
        os.remove(os.path.join(c.dir, "reference.py"))
        rep = c.report()
        self.assertFalse(rep["ok"])
        self.assertIn("reference.py is missing", rep["issues"])


class CliTests(unittest.TestCase):
    def test_exit_0_and_json(self):
        c = Case(self, faulty=body("big = np.mean(d['x']) > 0.3").replace("    return True\n", "    return bool(big)\n"))
        r = c.cli()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(c.out, encoding="utf-8") as f:
            rep = json.load(f)
        self.assertTrue(rep["ok"])
        self.assertEqual(len(rep["bodies"]["faulty_body.py"]["listed_comparisons"]), 1)
        entry = rep["bodies"]["faulty_body.py"]["listed_comparisons"][0]
        self.assertEqual(set(entry), {"file", "line", "text", "op", "kind", "call", "calls"})
        self.assertIn("1 listed comparison", r.stdout)

    def test_exit_1_on_an_issue(self):
        c = Case(self, fixed=HEAD + "T = 1\n\n\ndef criterion(d):\n    return True\n")
        r = c.cli()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        with open(c.out, encoding="utf-8") as f:
            self.assertFalse(json.load(f)["ok"])

    def test_exit_2_on_usage_errors(self):
        c = Case(self)
        os.remove(os.path.join(c.dir, "fixed_body.py"))
        self.assertEqual(c.cli().returncode, 2)
        self.assertEqual(common.run_tool("mech_check_bodies.py", "--case", c.dir).returncode, 2)


if __name__ == "__main__":
    unittest.main()
