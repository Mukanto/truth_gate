import os
import tempfile
import unittest

import common  # noqa: F401  (puts tools/ on sys.path)
import toy_case
from assemble import BEGIN_MARK, END_MARK, AssembleError, assemble, differ_only_in_criterion

SKELETON = toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": 0.9}


class AssembleTests(unittest.TestCase):
    def test_toy_bodies_assemble(self):
        for body in (toy_case.FAULTY_BODY, toy_case.FIXED_BODY):
            out = assemble(SKELETON, body)
            compile(out, "<assembled>", "exec")
            self.assertEqual(out.count("import numpy as np"), 1)  # the body's own import is gone
            self.assertEqual(out.count("def criterion("), 1)
            self.assertNotIn("NotImplementedError", out)
            self.assertIn("def _knn_predict(", out)
            self.assertIn(BEGIN_MARK, out)
            self.assertTrue(out.endswith("\n"))
            # everything outside the region is the skeleton, line for line
            lines = out.splitlines()
            b, e = lines.index(BEGIN_MARK), lines.index(END_MARK)
            sk_lines = SKELETON.splitlines()
            self.assertEqual(lines[:b], sk_lines[:b])
            tail = lines[e + 1:]
            self.assertEqual(tail, sk_lines[len(sk_lines) - len(tail):])
            replaced = sk_lines[b:len(sk_lines) - len(tail)]  # exactly the placeholder function was replaced
            self.assertTrue(replaced[0].startswith("def criterion("))
            self.assertEqual(replaced[-1].strip(), "raise NotImplementedError")

    def test_placeholder_without_docstring_is_fine(self):
        sk = SKELETON.replace('    """Data keys: x, float (300,), predictor series; y, float (300,), outcome series.\n'
                              '    Holds when the claim is supported by the data. Written by someone else."""\n', "")
        self.assertNotIn("Written by someone else", sk)
        compile(assemble(sk, toy_case.FIXED_BODY), "<a>", "exec")

    def test_differ_only_in_criterion(self):
        a = assemble(SKELETON, toy_case.FAULTY_BODY)
        b = assemble(SKELETON, toy_case.FIXED_BODY)
        self.assertNotEqual(a, b)
        self.assertTrue(differ_only_in_criterion(a, b))
        self.assertTrue(differ_only_in_criterion(a, a))
        # a change anywhere outside the region is a difference
        self.assertFalse(differ_only_in_criterion(a, b.replace("N = 300", "N = 301")))
        self.assertFalse(differ_only_in_criterion(a, b.replace('"plus": World(plus)', '"plus": World(minus)')))
        # a region that moved is a difference
        self.assertFalse(differ_only_in_criterion(a, "# extra line\n" + b))
        with self.assertRaises(AssembleError):
            differ_only_in_criterion(SKELETON, b)

    def test_rejects_bad_skeletons(self):
        cases = {
            "decorator": SKELETON.replace("def criterion(d):", "@staticmethod\ndef criterion(d):"),
            "extra statement": SKELETON.replace("    raise NotImplementedError", "    x = 1\n    raise NotImplementedError"),
            "not a raise": SKELETON.replace("    raise NotImplementedError", "    return True"),
            "other exception": SKELETON.replace("raise NotImplementedError", "raise ValueError"),
            "no placeholder": SKELETON.replace("def criterion(d):", "def other(d):").replace("Criterion(\"C\", criterion)",
                                                                                           "Criterion(\"C\", other)"),
            "study refers elsewhere": SKELETON.replace('Criterion("C", criterion)', 'Criterion("C", plus)'),
            "criterion id differs": SKELETON.replace('Criterion("C", criterion)', 'Criterion("D", criterion)'),
            "syntax error": SKELETON + "\ndef (:\n",
            "marker present": SKELETON + "\n" + BEGIN_MARK + "\n",
        }
        for name, sk in cases.items():
            with self.subTest(name), self.assertRaises(AssembleError):
                assemble(sk, toy_case.FIXED_BODY)

    def test_rejects_two_criteria_in_skeleton(self):
        sk = SKELETON + "\n\ndef criterion(d):\n    raise NotImplementedError\n"
        with self.assertRaises(AssembleError):
            assemble(sk, toy_case.FIXED_BODY)

    def test_rejects_bad_bodies(self):
        cases = {
            "no criterion": "import numpy as np\n\ndef helper(d):\n    return 1\n",
            "two criteria": toy_case.FIXED_BODY + "\n\ndef criterion(d):\n    return True\n",
            "other import": "import math\nimport numpy as np\n\ndef criterion(d):\n    return True\n",
            "from import": "from math import pi\n\ndef criterion(d):\n    return True\n",
            "syntax error": "def criterion(d:\n",
            "empty": "",
            "name clash with the skeleton": toy_case.FIXED_BODY + "\n\ndef plus(rng):\n    return {}\n",
            "constant clash": "import numpy as np\nN = 5\n\ndef criterion(d):\n    return True\n",
            "clash with an imported name": "import numpy as np\nStudy = 1\n\ndef criterion(d):\n    return True\n",
        }
        for name, body in cases.items():
            with self.subTest(name), self.assertRaises(AssembleError):
                assemble(SKELETON, body)

    def test_module_level_rule_of_r2_29(self):
        """Only ``import numpy as np`` and function definitions at module level; anything else is refused."""
        good = "import numpy as np\n\n\ndef helper(x):\n    return x\n\n\ndef criterion(d):\n    return bool(helper(True))\n"
        compile(assemble(SKELETON, good), "<a>", "exec")
        extra = {
            "assignment": "import numpy as np\nTHRESHOLD = 0.3\n\n\ndef criterion(d):\n    return True\n",
            "annotated assignment": "import numpy as np\nT: float = 0.3\n\n\ndef criterion(d):\n    return True\n",
            "numpy attribute assignment": "import numpy as np\nnp.seterr(all='ignore')\n\n\ndef criterion(d):\n    return True\n",
            "attribute store": "import numpy as np\nnp.foo = 1\n\n\ndef criterion(d):\n    return True\n",
            "call": "import numpy as np\nprint(1)\n\n\ndef criterion(d):\n    return True\n",
            "class": "import numpy as np\n\n\nclass K:\n    pass\n\n\ndef criterion(d):\n    return True\n",
            "if": "import numpy as np\nif True:\n    pass\n\n\ndef criterion(d):\n    return True\n",
            "for": "import numpy as np\nfor i in range(3):\n    pass\n\n\ndef criterion(d):\n    return True\n",
            "module docstring": '"""A body."""\nimport numpy as np\n\n\ndef criterion(d):\n    return True\n',
            "import numpy without alias": "import numpy\n\n\ndef criterion(d):\n    return True\n",
            "import numpy as other": "import numpy as other\n\n\ndef criterion(d):\n    return True\n",
            "from numpy import": "from numpy import mean\n\n\ndef criterion(d):\n    return True\n",
            "import inside a try": "try:\n    import numpy as np\nexcept ImportError:\n    pass\n\n\ndef criterion(d):\n    return True\n",
            "async def": "import numpy as np\n\n\nasync def helper():\n    return 1\n\n\ndef criterion(d):\n    return True\n",
            "two imports of numpy and a third": "import numpy as np\nimport numpy as np\nimport os\n\n\ndef criterion(d):\n    return True\n",
        }
        for name, body in extra.items():
            with self.subTest(name), self.assertRaises(AssembleError) as cm:
                assemble(SKELETON, body)
            self.assertIn("module level", str(cm.exception), name)
        # the same rule through the function the other tools call
        from assemble import module_level_problems
        import ast
        self.assertEqual(module_level_problems(ast.parse(good)), [])
        self.assertEqual(module_level_problems(ast.parse(extra["assignment"])), [(2, "Assign")])

    def test_a_body_that_reads_a_skeleton_level_name_is_refused(self):
        """D-R4-2: the module-level rule alone lets a function read the skeleton's globals; the free-name check does not."""
        head = "import numpy as np\n\n\n"
        for name in ("N", "PHI", "plus", "STUDY"):
            body = head + f"def criterion(d):\n    return bool(d['x'][0] < {name})\n"
            with self.subTest(name), self.assertRaises(AssembleError) as cm:
                assemble(SKELETON, body)
            self.assertIn(f"reads module-level name {name} (line 5)", str(cm.exception))
        with self.assertRaises(AssembleError) as cm:
            assemble(SKELETON, head + "def criterion(d):\n    return bool(nobody)\n")
        self.assertIn("undefined name nobody", str(cm.exception))
        # a helper that reads a skeleton name is refused too
        helper = head + "def h(x):\n    return x + N\n\n\ndef criterion(d):\n    return bool(h(1))\n"
        with self.assertRaises(AssembleError):
            assemble(SKELETON, helper)
        # a parameter called N is the body's own name, not a free name
        ok = head + "def h(x, N=3):\n    return x + N\n\n\ndef criterion(d):\n    return bool(h(1))\n"
        compile(assemble(SKELETON, ok), "<a>", "exec")

    def test_a_decorated_module_level_function_is_refused(self):
        """T3-4: a decorator runs code at import, so it is refused; the message names the line."""
        from assemble import module_level_problems
        import ast
        helper = "import numpy as np\n\n\n@np.vectorize\ndef helper(x):\n    return x\n\n\ndef criterion(d):\n    return True\n"
        crit = "import numpy as np\n\n\n@np.vectorize\ndef criterion(d):\n    return True\n"
        for name, body in (("helper", helper), ("criterion", crit)):
            with self.subTest(name), self.assertRaises(AssembleError) as cm:
                assemble(SKELETON, body)
            self.assertIn("decorated FunctionDef at line 5", str(cm.exception))
        self.assertEqual(module_level_problems(ast.parse(helper)), [(5, "decorated FunctionDef")])
        # an undecorated function and a decorator-free nested function are fine
        nested = "import numpy as np\n\n\ndef criterion(d):\n    def inner(x):\n        return x\n    return bool(inner(True))\n"
        compile(assemble(SKELETON, nested), "<a>", "exec")

    def test_exactly_one_function_must_be_criterion(self):
        for name, body in {"none": "import numpy as np\n\n\ndef helper(d):\n    return 1\n",
                           "two": "import numpy as np\n\n\ndef criterion(d):\n    return 1\n\n\ndef criterion(d):\n    return 2\n"}.items():
            with self.subTest(name), self.assertRaises(AssembleError):
                assemble(SKELETON, body)

    def test_body_with_only_the_numpy_import_line_removed(self):
        body = "import numpy as np\n\n\ndef criterion(d):\n    return bool(np.all(d['x'] == d['x']))\n"
        out = assemble(SKELETON, body)
        self.assertIn("def criterion(d):\n    return bool(np.all(d['x'] == d['x']))", out)

    def test_crlf_input(self):
        out = assemble(SKELETON.replace("\n", "\r\n"), toy_case.FIXED_BODY.replace("\n", "\r\n"))
        self.assertNotIn("\r", out)
        compile(out, "<a>", "exec")


class AssembleCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.sk, self.body, self.out = (os.path.join(t, n) for n in ("sk.py", "body.py", "out.py"))
        with open(self.sk, "w", encoding="utf-8", newline="\n") as f:
            f.write(SKELETON)
        with open(self.body, "w", encoding="utf-8", newline="\n") as f:
            f.write(toy_case.FIXED_BODY)

    def test_cli_ok(self):
        r = common.run_tool("assemble.py", "--skeleton", self.sk, "--body", self.body, "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual(f.read(), assemble(SKELETON, toy_case.FIXED_BODY))

    def test_cli_with_package_root(self):
        r = common.run_tool("assemble.py", "--skeleton", self.sk, "--body", self.body, "--out", self.out,
                            "--package-root", common.PKG)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_cli_refuses_a_bad_pair(self):
        with open(self.body, "w", encoding="utf-8") as f:
            f.write("import math\ndef criterion(d):\n    return True\n")
        r = common.run_tool("assemble.py", "--skeleton", self.sk, "--body", self.body, "--out", self.out)
        self.assertEqual(r.returncode, 1)
        self.assertFalse(os.path.exists(self.out))

    def test_cli_usage_errors(self):
        self.assertEqual(common.run_tool("assemble.py", "--skeleton", self.sk).returncode, 2)
        r = common.run_tool("assemble.py", "--skeleton", self.sk, "--body", self.body + ".missing", "--out", self.out)
        self.assertEqual(r.returncode, 2)
        r = common.run_tool("assemble.py", "--skeleton", self.sk, "--body", self.body, "--out", self.out,
                            "--package-root", self.tmp.name)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
