"""Truth_Gate 0.4, stage (e): ``.pre-commit-hooks.yaml`` (spec 0.6, section 10) and the tiny YAML reader the tests use."""

import contextlib
import io
import os
import re
import shlex
import tomllib
import unittest

import _helpers
from truth_gate import ci
from truth_gate.freeze import main as freeze_main
from yaml_lite import YamlError, load

ROOT = _helpers.ROOT


def read(path):
    with open(os.path.join(ROOT, path), "r", encoding="utf-8") as handle:
        return handle.read()


class TestYamlLite(unittest.TestCase):
    def test_reads_the_subset(self):
        doc = load("a: 1\nb:\n  - x: y\n    z: [1, 'two', \"three\"]\n  - plain  # comment\nc: |\n  line one\n    two\nd: 'it''s'\n")
        self.assertEqual(doc, {"a": 1, "b": [{"x": "y", "z": [1, "two", "three"]}, "plain"],
                               "c": "line one\n  two\n", "d": "it's"})

    def test_rejects_what_is_outside_the_subset(self):
        for text in ("a: &x 1\n", "a: {b: 1}\n", "a:\n\tb: 1\n", "a: 1\na: 2\n", "a: 1\n---\nb: 2\n", "a: 1\n  b: 2\n"):
            with self.subTest(text=text), self.assertRaises(YamlError):
                load(text)

    def test_a_hash_inside_a_value_is_kept(self):
        self.assertEqual(load("a: 'x # y'\nb: c#d\n"), {"a": "x # y", "b": "c#d"})


class TestPreCommitHooks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hooks = load(read(".pre-commit-hooks.yaml"))
        cls.by_id = {h["id"]: h for h in cls.hooks}

    def test_the_two_hooks_of_spec_section_10_exist(self):
        self.assertEqual([h["id"] for h in self.hooks], ["truth-gate-freeze", "truth-gate-check"])

    def test_every_hook_is_a_python_hook_with_the_required_keys(self):
        for hook in self.hooks:
            with self.subTest(hook=hook["id"]):
                for key in ("id", "name", "entry", "language"):
                    self.assertTrue(hook.get(key), key)
                self.assertEqual(hook["language"], "python")

    def test_the_entry_commands_exist_in_the_cli(self):
        with open(os.path.join(ROOT, "pyproject.toml"), "rb") as handle:
            scripts = tomllib.load(handle)["project"]["scripts"]
        self.assertEqual(scripts["truth-gate"], "truth_gate.cli:main")
        freeze = shlex.split(self.by_id["truth-gate-freeze"]["entry"])
        self.assertEqual(freeze[0], "truth-gate")  # the console script the package installs
        self.assertEqual(freeze, ["truth-gate", "freeze", "verify"])
        self.assertEqual(freeze[1], "freeze")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as stop:
            freeze_main(["verify", "--help"])  # the subcommand exists
        self.assertEqual(stop.exception.code, 0)
        # R-27: pre-commit may pass several files in one call, `check` takes one: the hook runs the wrapper
        check = shlex.split(self.by_id["truth-gate-check"]["entry"])
        self.assertEqual(check, ["python", "-m", "truth_gate.ci", "--pre-commit"])
        args = ci.build_parser().parse_args(check[3:] + ["a/truthgate.toml", "b/truthgate.json"])
        self.assertTrue(args.pre_commit)
        self.assertEqual(args.files, ["a/truthgate.toml", "b/truthgate.json"])  # several filenames parse
        self.assertIs(self.by_id["truth-gate-check"]["pass_filenames"], True)

    def test_the_freeze_hook_takes_its_manifest_from_args_and_runs_every_commit(self):
        hook = self.by_id["truth-gate-freeze"]
        self.assertIs(hook["pass_filenames"], False)  # a frozen file can change while the manifest does not
        self.assertIs(hook["always_run"], True)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(freeze_main(["verify", os.path.join(ROOT, "no", "such", "FREEZE.json")]), 2)

    def test_the_check_hook_matches_only_truthgate_manifests(self):
        pattern = re.compile(self.by_id["truth-gate-check"]["files"])
        for path in ("truthgate.toml", "truthgate.json", "studies/a/truthgate.toml", "x/truthgate.json"):
            self.assertTrue(pattern.search(path), path)
        for path in ("pyproject.toml", "package.json", "mytruthgate.toml", "truthgate.toml.bak", "truthgate.tomll",
                     "tests/manifests/trial_example.toml", "truthgate.kapi.json", "FREEZE.json", "truthgate/x.toml"):
            self.assertFalse(pattern.search(path), path)


if __name__ == "__main__":
    unittest.main()
