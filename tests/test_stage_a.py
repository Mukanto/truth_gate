"""Truth_Gate 0.4, stage (a): the kapi shim, certificate schema 2, exit code 7, the guard allow-list (spec 0.6)."""

import copy
import contextlib
import hashlib
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

import _helpers
from _helpers import body, run_toy, toy_path
import kapi
import truth_gate
from truth_gate import certificate, cli, guard

PACKAGE_DIR = os.path.join(_helpers.ROOT, "truth_gate")
SHIM_DIR = os.path.join(_helpers.ROOT, "kapi")


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def module_names(folder):
    return sorted(
        name[:-3] for name in os.listdir(folder)
        if name.endswith(".py") and name not in ("__init__.py", "__main__.py")
    )


class TestShim(unittest.TestCase):
    def test_public_names_are_the_same_objects(self):
        self.assertEqual(kapi.__all__, truth_gate.__all__)
        for name in truth_gate.__all__:
            with self.subTest(name=name):
                self.assertIs(getattr(kapi, name), getattr(truth_gate, name))

    def test_version_is_truth_gates(self):
        self.assertEqual(kapi.__version__, truth_gate.__version__)
        self.assertEqual(truth_gate.__version__, "0.4.1")
        self.assertEqual(kapi.SPEC_VERSION, "0.6")

    def test_every_submodule_is_aliased(self):
        names = module_names(PACKAGE_DIR)
        self.assertIn("checks", names)
        for name in names:
            with self.subTest(module=name):
                real = importlib.import_module("truth_gate." + name)
                alias = importlib.import_module("kapi." + name)
                self.assertIs(alias, real)
                self.assertIs(sys.modules["kapi." + name], real)
                self.assertIs(getattr(kapi, name), real)

    def test_old_import_forms_work(self):
        from kapi.checks import evaluate
        from kapi.study import Study
        from kapi import guard as shim_guard
        self.assertIs(evaluate, truth_gate.checks.evaluate)
        self.assertIs(Study, truth_gate.Study)
        self.assertIs(shim_guard, guard)

    def test_shim_folder_holds_only_the_two_entry_files(self):
        self.assertEqual(sorted(n for n in os.listdir(SHIM_DIR) if n.endswith(".py")), ["__init__.py", "__main__.py"])

    def test_no_warning_on_import(self):
        done = subprocess.run(
            [sys.executable, "-B", "-W", "error", "-c", "import kapi, kapi.checks, kapi.cli"],
            cwd=_helpers.ROOT, capture_output=True, text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stderr, "")

    def test_python_dash_m_kapi_and_truth_gate_agree(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        tmp = tempfile.mkdtemp(prefix="kapi_test_")
        self.addCleanup(shutil.rmtree, tmp, True)
        results = {}
        for module in ("kapi", "truth_gate"):
            out = os.path.join(tmp, module + ".json")
            done = subprocess.run(
                [sys.executable, "-B", "-W", "error", "-m", module, "check", toy_path("toy_good_det"), "--out", out],
                cwd=_helpers.ROOT, capture_output=True, text=True, env=env,
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(done.stderr, "")
            with open(out, encoding="utf-8") as handle:
                results[module] = json.load(handle)["body_sha256"]
        self.assertEqual(results["kapi"], results["truth_gate"])


class TestSchema2(unittest.TestCase):
    def test_new_fields_for_a_python_study(self):
        b = body("toy_good")
        self.assertEqual(b["tool"], "truth-gate")
        self.assertEqual(b["tool_version"], truth_gate.__version__)
        self.assertEqual(b["spec_version"], "0.6")
        self.assertEqual(b["input_kind"], "python")
        self.assertEqual(b["study_notes"], [])
        self.assertNotIn("kapi_version", b)

    def test_body_fields_constant(self):
        self.assertEqual(
            certificate.BODY_FIELDS,
            ("tool", "tool_version", "spec_version", "input_kind", "python_version", "numpy_version", "mode", "study",
             "m_comparisons", "alpha_per_bound", "components", "premise_map", "study_flags", "study_notes", "leak_log",
             "verdict", "non_claims"),
        )
        for name in ("toy_good", "toy_dup_ids"):
            self.assertEqual(certificate.validate_envelope(run_toy(name)), [], name)

    def test_load_failure_certificate_has_the_schema_2_fields(self):
        b = body("toy_dup_ids")
        self.assertEqual((b["tool"], b["input_kind"], b["study_notes"]), ("truth-gate", "python", []))

    def test_no_other_new_fields_yet(self):
        for name in ("manifest", "mutations", "k8", "m_k8", "pattern_stats", "suggested_unreviewed"):
            self.assertNotIn(name, body("toy_good"))
        self.assertEqual(set(body("toy_good")["study"]), set(body("toy_good_det")["study"]))

    def test_validation_rejects_bad_new_fields(self):
        for key, bad in (("tool", "kapi"), ("input_kind", "yaml"), ("study_notes", "none")):
            env = copy.deepcopy(run_toy("toy_good"))
            env["body"][key] = bad
            env["body_sha256"] = certificate.body_sha256(env["body"])
            self.assertTrue(certificate.validate_envelope(env), key)
        env = copy.deepcopy(run_toy("toy_good"))
        del env["body"]["input_kind"]
        env["body_sha256"] = certificate.body_sha256(env["body"])
        self.assertIn("body is missing 'input_kind'", certificate.validate_envelope(env))

    def test_non_claims(self):
        claims = body("toy_good")["non_claims"]
        self.assertEqual(claims, certificate.NON_CLAIMS)
        self.assertEqual(len(claims), 6)
        self.assertEqual(claims[2], "The gate does not modify or repair criteria. It only reports.")
        self.assertEqual(claims[3], "Generated mutations and suggested declarations are generic; they do not know your domain.")
        self.assertTrue(claims[4].startswith("A file world is only as independent as its provenance;"))
        self.assertEqual(claims[5], "The leak guard does not cover external programs; a study note lists them.")
        self.assertFalse(any("Kap" in c for c in claims))

    def test_known_limitations_gain_the_two_external_program_entries(self):
        limits = body("toy_good")["known_limitations"]
        self.assertEqual(
            limits[3:],
            ["External programs are hashed by executable and `uses` files only; the libraries they load are not hashed.",
             "On Windows, killing an external program does not kill programs it started."],
        )


class TestVerifyExit7(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="kapi_test_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.study = toy_path("toy_good_det")

    def write_cert(self, name, envelope):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle)
        return path

    def never_rerun(self):
        return mock.patch.object(cli, "run_gate", side_effect=AssertionError("verify must not re-run the study"))

    def test_certificate_without_tool_field(self):
        env = copy.deepcopy(run_toy("toy_good_det"))
        b = env["body"]
        for key in ("tool", "tool_version", "input_kind", "study_notes"):
            del b[key]
        b["kapi_version"] = "0.3.0"
        b["spec_version"] = "0.5"
        env["body_sha256"] = certificate.body_sha256(b)
        with self.never_rerun():
            code, out, _ = run_cli("verify", self.write_cert("old.json", env), self.study)
        self.assertEqual(code, 7)
        self.assertIn("0.3.0", out)
        self.assertIn("v0.3.0", out)
        self.assertIn("0.4.1", out)

    def test_certificate_of_another_tool_version(self):
        env = copy.deepcopy(run_toy("toy_good_det"))
        env["body"]["tool_version"] = "0.4.0"
        env["body_sha256"] = certificate.body_sha256(env["body"])
        with self.never_rerun():
            code, out, _ = run_cli("verify", self.write_cert("other.json", env), self.study)
        self.assertEqual(code, 7)
        self.assertIn("0.4.0", out)
        self.assertIn("v0.4.0", out)

    def test_altered_old_certificate_reads_as_altered(self):
        """Revision R-2: integrity is checked before the version, so tampering gives 5, not 7."""
        env = copy.deepcopy(run_toy("toy_good_det"))
        b = env["body"]
        for key in ("tool", "tool_version", "input_kind", "study_notes"):
            del b[key]
        b["kapi_version"] = "0.3.0"
        env["body_sha256"] = certificate.body_sha256(b)
        b["verdict"] = "FALSIFIABLE" if b["verdict"] != "FALSIFIABLE" else "WEAK"  # altered after hashing
        with self.never_rerun():
            code, out, _ = run_cli("verify", self.write_cert("altered_old.json", env), self.study)
        self.assertEqual(code, 5)
        self.assertIn("MISMATCH", out)

    def test_same_version_still_verifies(self):
        env = run_toy("toy_good_det")
        self.assertEqual(run_cli("verify", self.write_cert("same.json", env), self.study)[0], 0)

    def test_unreadable_or_foreign_certificates_keep_exit_4(self):
        self.assertEqual(run_cli("verify", self.write_cert("junk.json", {"x": 1}), self.study)[0], 4)

    def test_real_0_3_0_certificate(self):
        """Uses the actual 0.3.0 package from git tag v0.3.0; skipped when the tag or git is unavailable."""
        try:
            archive = subprocess.run(
                ["git", "archive", "v0.3.0", "kapi"], cwd=_helpers.ROOT, capture_output=True, check=True
            ).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git tag v0.3.0 is not available")
        export = os.path.join(self.tmp, "kapi030")
        os.makedirs(export)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(export)
        out = os.path.join(self.tmp, "real030.json")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=export)
        bootstrap = (
            "import sys; sys.path.insert(0, sys.argv.pop(1)); import kapi; "
            "assert kapi.__version__ == '0.3.0', kapi.__file__; "
            "from kapi.cli import main; sys.exit(main(sys.argv[1:]))"
        )
        done = subprocess.run(
            [sys.executable, "-B", "-c", bootstrap, export, "check", self.study, "--out", out],
            cwd=_helpers.ROOT, capture_output=True, text=True, env=env,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        with open(out, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["body"]["kapi_version"], "0.3.0")
        with self.never_rerun():
            code, text, _ = run_cli("verify", out, self.study)
        self.assertEqual(code, 7)
        self.assertIn("v0.3.0", text)


class TestGuardAllowList(unittest.TestCase):
    def test_both_package_folders_are_allowed(self):
        self.assertEqual(os.path.normcase(os.path.realpath(guard.PACKAGE_DIR)), os.path.normcase(os.path.realpath(PACKAGE_DIR)))
        self.assertEqual(os.path.normcase(os.path.realpath(guard.SHIM_DIR)), os.path.normcase(os.path.realpath(SHIM_DIR)))
        allowed = guard._default_allow_dirs()
        self.assertIn(guard._norm(PACKAGE_DIR), allowed)
        self.assertIn(guard._norm(SHIM_DIR), allowed)

    def test_shim_files_can_be_opened_while_armed(self):
        with guard.armed(__file__):
            self.assertIsNone(guard._hook("open", (os.path.join(SHIM_DIR, "__init__.py"), "r", 0)))
            self.assertIsNone(guard._hook("os.listdir", (SHIM_DIR,)))
            self.assertEqual(guard.take_log(), [])

    def test_study_importing_the_shim_fresh_does_not_leak(self):
        """A study that says ``from kapi import ...`` in a process that has not imported kapi yet."""
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); from truth_gate.certificate import run_gate; "
            "env = run_gate(sys.argv[2], quick=True); "
            "print(env['body']['leak_log'], env['body']['study_flags'])"
        )
        done = subprocess.run(
            [sys.executable, "-B", "-c", code, _helpers.ROOT, toy_path("toy_good")],
            cwd=_helpers.ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(done.stdout.startswith("[] "), done.stdout)
        self.assertNotIn("K6_LEAK_ATTEMPT", done.stdout)


if __name__ == "__main__":
    unittest.main()
