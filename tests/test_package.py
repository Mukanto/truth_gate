"""Package constraints (spec sections 9 and 11): layout, imports, documented flags, public API."""

import ast
import os
import sys
import unittest

import _helpers
import kapi
from test_toy_flags import FLAG_TOYS

PACKAGE = os.path.join(_helpers.ROOT, "kapi")
MODULES = ("__init__", "study", "sampling", "stats", "probes", "checks", "guard", "certificate", "cli", "__main__")
FORBIDDEN_IMPORTS = {"subprocess", "socket", "urllib", "http", "requests", "ftplib", "smtplib", "scipy", "ctypes"}


def imported_roots(path):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


class TestLayout(unittest.TestCase):
    def test_modules_exist(self):
        for name in MODULES:
            self.assertTrue(os.path.isfile(os.path.join(PACKAGE, name + ".py")), name)
        for name in ("README.md", "pyproject.toml"):
            self.assertTrue(os.path.isfile(os.path.join(_helpers.ROOT, name)), name)

    def test_only_standard_library_and_numpy(self):
        allowed = set(sys.stdlib_module_names) | {"numpy"}
        for name in MODULES:
            roots = imported_roots(os.path.join(PACKAGE, name + ".py"))
            self.assertLessEqual(roots, allowed, f"{name}: {roots - allowed}")
            self.assertFalse(roots & FORBIDDEN_IMPORTS, f"{name}: {roots & FORBIDDEN_IMPORTS}")

    def test_no_file_writes_outside_the_cli(self):
        for name in MODULES:
            with open(os.path.join(PACKAGE, name + ".py"), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
                    mode = ast.literal_eval(node.args[1]) if len(node.args) > 1 else "r"
                    if name != "cli":
                        self.assertNotRegex(str(mode), "[wax+]", f"{name} opens a file for writing")

    def test_pyproject_is_minimal(self):
        with open(os.path.join(_helpers.ROOT, "pyproject.toml"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn('name = "truth-gate"', text)  # distribution name; the package is still imported as kapi
        self.assertIn('version = "0.3.0"', text)
        self.assertIn('dependencies = ["numpy"]', text)


class TestPublicApi(unittest.TestCase):
    def test_names(self):
        for name in ("Study", "Criterion", "World", "Premise", "Control", "Budget", "Targets", "StudyError", "run_gate"):
            self.assertTrue(hasattr(kapi, name), name)
        self.assertEqual(kapi.__version__, "0.3.0")

    def test_study_error_is_an_exception(self):
        self.assertTrue(issubclass(kapi.StudyError, Exception))


class TestReadmeCoversEveryFlag(unittest.TestCase):
    def test_flags_documented(self):
        # The flag reference moved from the README to docs/GATE.md when the README became an overview.
        with open(os.path.join(_helpers.ROOT, "docs", "GATE.md"), encoding="utf-8") as handle:
            reference = handle.read()
        for flag in FLAG_TOYS:
            token = flag.replace(":*", "")
            self.assertIn("`" + token, reference, f"{flag} is not documented in docs/GATE.md")

    def test_readme_mentions_non_claims_and_weaknesses(self):
        with open(os.path.join(_helpers.ROOT, "README.md"), encoding="utf-8") as handle:
            readme = handle.read()
        for phrase in ("does not mean the hypothesis is true", "It only reports", "Known weaknesses", "evade K5"):
            self.assertIn(phrase, readme)


class TestNoEvaluationCases(unittest.TestCase):
    def test_no_case_directory_or_files(self):
        self.assertFalse(os.path.exists(os.path.join(_helpers.ROOT, "eval", "cases")))


if __name__ == "__main__":
    unittest.main()
