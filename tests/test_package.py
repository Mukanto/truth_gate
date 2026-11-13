"""Package constraints (spec sections 9 and 11): layout, imports, documented flags, public API."""

import ast
import os
import re
import sys
import unittest

import _helpers
import kapi
from test_toy_flags import FLAG_TOYS

PACKAGE = os.path.join(_helpers.ROOT, "truth_gate")
KAPI = os.path.join(_helpers.ROOT, "kapi")
MODULES = ("__init__", "study", "sampling", "stats", "probes", "checks", "guard", "certificate", "cli", "__main__")
FORBIDDEN_IMPORTS = {"subprocess", "socket", "urllib", "http", "requests", "ftplib", "smtplib", "scipy", "ctypes"}

# The only modules that may write files (audit F9).  Every other module of truth_gate/ and kapi/ is read-only.
FILE_WRITERS = {
    "cli": "writes the certificate (`check --out`), the starter manifest (`suggest`) and the badge JSON (`badge --out`)",
    "scaffold": "`init` writes PREREG.md, truthgate.toml, BLIND_AUDIT_PROMPT.md, run_guarded.py and the CI workflow",
    "freeze": "`freeze write` writes the freeze manifest",
    "badge": "builds the badge payload for the CLI; allowed to write its endpoint JSON if it ever has to",
    "ci": "appends to $GITHUB_STEP_SUMMARY and $GITHUB_OUTPUT; the pre-commit wrapper keeps certificates in a temporary folder",
    "external": "copies `[external] uses` and `allow_paths` into its temporary working folder (deleted at the end)",
}


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


def package_modules(folder):
    return sorted(name[:-3] for name in os.listdir(folder) if name.endswith(".py"))


_WRITE_MODE = re.compile("[wax+]")
_WRITING_CALLS = {  # owner name -> function names that create, change or delete files
    "os": {"open", "makedirs", "mkdir", "remove", "unlink", "rename", "replace", "rmdir", "removedirs", "truncate"},
    "shutil": {"copy", "copy2", "copyfile", "copyfileobj", "copymode", "copystat", "copytree", "move", "rmtree"},
    "tempfile": {"mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile", "SpooledTemporaryFile",
                 "TemporaryDirectory"},
    "np": {"save", "savez", "savez_compressed", "savetxt"},
    "numpy": {"save", "savez", "savez_compressed", "savetxt"},
}
_WRITING_METHODS = {"write_text", "write_bytes", "touch", "mkdir", "unlink", "rmdir", "rename"}


def file_writes(path):
    """Calls in ``path`` that can write a file: ``open`` with a write mode (or a mode that is not a literal), the
    writing functions of ``os``, ``shutil``, ``tempfile`` and numpy, and ``Path.write_text`` and the like."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "open" or (
                isinstance(func, ast.Attribute) and func.attr == "open" and getattr(func.value, "id", None) == "io"):
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
            if mode is None:
                continue
            if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)) or _WRITE_MODE.search(mode.value):
                found.append(f"line {node.lineno}: open with a write mode")
        elif isinstance(func, ast.Attribute):
            owner = getattr(func.value, "id", None)
            if func.attr in _WRITING_CALLS.get(owner, ()) or func.attr in _WRITING_METHODS:
                found.append(f"line {node.lineno}: {owner or '...'}.{func.attr}")
    return found


class TestLayout(unittest.TestCase):
    def test_modules_exist(self):
        for name in MODULES:
            self.assertTrue(os.path.isfile(os.path.join(PACKAGE, name + ".py")), name)
        for name in ("README.md", "pyproject.toml"):
            self.assertTrue(os.path.isfile(os.path.join(_helpers.ROOT, name)), name)

    def test_only_standard_library_and_numpy(self):
        """Every module of truth_gate/ and kapi/ (listed from the folders, not by hand) imports the standard library,
        numpy and the package itself, and none of the forbidden modules (``subprocess`` only in ``external``)."""
        allowed = set(sys.stdlib_module_names) | {"numpy", "truth_gate", "kapi"}
        found = 0
        for folder in (PACKAGE, KAPI):
            for name in package_modules(folder):
                found += 1
                roots = imported_roots(os.path.join(folder, name + ".py"))
                label = f"{os.path.basename(folder)}/{name}"
                self.assertLessEqual(roots, allowed, f"{label}: {roots - allowed}")
                forbidden = FORBIDDEN_IMPORTS - ({"subprocess"} if label == "truth_gate/external" else set())
                self.assertFalse(roots & forbidden, f"{label}: {roots & forbidden}")
        self.assertGreater(found, len(MODULES))  # the lists are derived from the folders: the new modules are in

    def test_no_file_writes_outside_the_allowlist(self):
        """No module of truth_gate/ or kapi/ writes a file unless it is in ``FILE_WRITERS`` (with a reason)."""
        found = 0
        for folder in (PACKAGE, KAPI):
            for name in package_modules(folder):
                found += 1
                writes = file_writes(os.path.join(folder, name + ".py"))
                label = f"{os.path.basename(folder)}/{name}"
                if folder == PACKAGE and name in FILE_WRITERS:
                    continue
                self.assertEqual(writes, [], f"{label} writes a file: {writes}")
        self.assertGreater(found, len(MODULES))

    def test_the_allowlist_is_honest(self):
        """Every entry names a real module of truth_gate/ and has a reason; the checker does see a write."""
        modules = package_modules(PACKAGE)
        for name, reason in FILE_WRITERS.items():
            self.assertIn(name, modules)
            self.assertTrue(reason.strip(), name)
        for name in ("cli", "scaffold", "freeze", "external", "ci"):
            self.assertTrue(file_writes(os.path.join(PACKAGE, name + ".py")), f"{name} no longer writes: drop it from FILE_WRITERS")

    def test_the_write_detector_sees_the_usual_ways_of_writing(self):
        import tempfile
        cases = {
            'open(p, "w")': True, 'open(p, mode="a")': True, "open(p, mode)": True, 'open(p, "rb+")': True,
            'open(p, "xb")': True, 'open(p)': False, 'open(p, "r")': False, 'open(p, "rb")': False,
            "path.write_text(x)": True, "path.write_bytes(x)": True, "np.save(p, x)": True, "np.savez(p, a=x)": True,
            "os.makedirs(p)": True, "os.remove(p)": True, "shutil.copyfile(a, b)": True, "shutil.rmtree(p)": True,
            "tempfile.mkdtemp()": True, "tempfile.TemporaryFile()": True, "os.open(p, os.O_WRONLY)": True,
            "x.copy()": False, "items.remove(v)": False, "text.replace(a, b)": False, "d.get(k)": False,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
                    handle.write(source + "\n")
                try:
                    self.assertEqual(bool(file_writes(handle.name)), expected)
                finally:
                    os.remove(handle.name)

    def test_pyproject_is_minimal(self):
        with open(os.path.join(_helpers.ROOT, "pyproject.toml"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn('name = "truth-gate"', text)  # distribution name; the package is still imported as kapi
        self.assertIn('version = "0.5.0"', text)
        self.assertIn('dependencies = ["numpy"]', text)


def imports_subprocess_dynamically(path):
    """``__import__("subprocess")`` or ``import_module("subprocess")`` with a literal name."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if func in ("__import__", "import_module") and node.args and isinstance(node.args[0], ast.Constant)                     and str(node.args[0].value).split(".")[0] == "subprocess":
                return True
    return False


class TestSubprocessRule(unittest.TestCase):
    """Spec 0.6, section 1.1 item 8: no module imports ``subprocess`` except ``truth_gate/external.py``."""

    def test_every_module_but_external_stays_free_of_subprocess(self):
        for folder in (PACKAGE, os.path.join(_helpers.ROOT, "kapi")):
            for name in package_modules(folder):
                path = os.path.join(folder, name + ".py")
                if folder == PACKAGE and name == "external":
                    continue
                with self.subTest(module=name, folder=os.path.basename(folder)):
                    self.assertNotIn("subprocess", imported_roots(path))
                    self.assertFalse(imports_subprocess_dynamically(path))

    def test_external_is_the_only_exception(self):
        importers = [name for name in package_modules(PACKAGE) if "subprocess" in imported_roots(os.path.join(PACKAGE, name + ".py"))]
        self.assertEqual(importers, ["external"])

    def test_external_keeps_every_other_rule(self):
        roots = imported_roots(os.path.join(PACKAGE, "external.py"))
        self.assertLessEqual(roots, set(sys.stdlib_module_names) | {"numpy"} | {"truth_gate"})
        self.assertFalse(roots & (FORBIDDEN_IMPORTS - {"subprocess"}), roots & FORBIDDEN_IMPORTS)

    def test_the_other_forbidden_imports_apply_to_every_module(self):
        for name in package_modules(PACKAGE):
            with self.subTest(module=name):
                roots = imported_roots(os.path.join(PACKAGE, name + ".py"))
                self.assertFalse(roots & (FORBIDDEN_IMPORTS - {"subprocess"}), roots & FORBIDDEN_IMPORTS)


class TestPublicApi(unittest.TestCase):
    def test_names(self):
        for name in ("Study", "Criterion", "World", "Premise", "Control", "Budget", "Targets", "StudyError", "run_gate"):
            self.assertTrue(hasattr(kapi, name), name)
        self.assertEqual(kapi.__version__, "0.5.0")

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
