"""CLI: exit codes, output files, verify (spec section 8). Always writes into a temp directory."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import _helpers
from _helpers import toy_path
from kapi import certificate
from kapi.cli import default_out_path, main


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="kapi_test_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def path(self, name):
        return os.path.join(self.tmp, name)


class TestCheckExitCodes(TempDirCase):
    def check(self, toy, *extra):
        out = self.path(toy + ".json")
        code, stdout, _ = run_cli("check", toy_path(toy), "--out", out, *extra)
        return code, stdout, out

    def test_exit_code_per_verdict(self):
        for toy, code in (
            ("toy_good", 0),
            ("toy_good_det", 0),
            ("toy_lowpower", 1),
            ("toy_no_control", 2),
            ("toy_leak_listdir", 2),
            ("toy_undefined_none", 3),
            ("toy_dup_ids", 3),
            ("toy_no_study", 3),
            ("toy_import_leak", 3),
        ):
            with self.subTest(toy=toy):
                self.assertEqual(self.check(toy)[0], code)

    def test_certificate_is_written_and_valid(self):
        code, stdout, out = self.check("toy_good")
        with open(out, encoding="utf-8") as handle:
            envelope = json.load(handle)
        self.assertEqual(certificate.validate_envelope(envelope), [])
        self.assertEqual(envelope["body"]["verdict"], "FALSIFIABLE")
        self.assertIn(envelope["body_sha256"], stdout)

    def test_table_lists_component_verdict_and_flags(self):
        _, stdout, _ = self.check("toy_lowpower")
        self.assertIn("COMPONENT", stdout)
        self.assertIn("x_gt_5", stdout)
        self.assertIn("WEAK", stdout)
        self.assertIn("K2_LOW_POWER", stdout)
        _, stdout, _ = self.check("toy_leak_listdir")
        self.assertIn("K6_LEAK_ATTEMPT", stdout)

    def test_quick_mode_is_recorded(self):
        _, _, out = self.check("toy_good", "--quick")
        with open(out, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["body"]["mode"], "quick")

    def test_nothing_else_is_written(self):
        self.check("toy_good")
        self.assertEqual(os.listdir(self.tmp), ["toy_good.json"])

    def test_default_output_path_rule(self):
        self.assertEqual(default_out_path(os.path.join("a", "study.py")), os.path.join("a", "study.kapi.json"))
        self.assertEqual(default_out_path("s.py"), "s.kapi.json")


class TestUsageErrors(TempDirCase):
    def test_usage_errors_exit_4(self):
        cases = [
            [],
            ["bogus"],
            ["check"],
            ["check", toy_path("toy_good"), "--nope"],
            ["verify", "only_one_argument"],
            ["check", self.path("missing.py"), "--out", self.path("o.json")],
            ["check", toy_path("toy_good"), "--out", self.path("no_such_dir") + os.sep + "o.json"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertEqual(run_cli(*argv)[0], 4)

    def test_failed_usage_writes_nothing(self):
        run_cli("check", self.path("missing.py"), "--out", self.path("o.json"))
        self.assertEqual(os.listdir(self.tmp), [])

    def test_verify_usage_errors(self):
        self.assertEqual(run_cli("verify", self.path("missing.json"), toy_path("toy_good"))[0], 4)
        garbage = self.path("garbage.json")
        with open(garbage, "w") as handle:
            handle.write("not json")
        self.assertEqual(run_cli("verify", garbage, toy_path("toy_good"))[0], 4)
        wrong = self.path("wrong.json")
        with open(wrong, "w") as handle:
            json.dump({"hello": 1}, handle)
        self.assertEqual(run_cli("verify", wrong, toy_path("toy_good"))[0], 4)


class TestVerify(TempDirCase):
    def make_cert(self, name="toy_good", *extra):
        study = self.path("study.py")
        shutil.copyfile(toy_path(name), study)
        cert = self.path("cert.json")
        run_cli("check", study, "--out", cert, *extra)
        return study, cert

    def test_unchanged_study_verifies_with_0(self):
        study, cert = self.make_cert()
        code, stdout, _ = run_cli("verify", cert, study)
        self.assertEqual(code, 0)
        self.assertIn("OK", stdout)

    def test_quick_certificate_is_verified_in_quick_mode(self):
        study, cert = self.make_cert("toy_good", "--quick")
        self.assertEqual(run_cli("verify", cert, study)[0], 0)

    def test_study_changed_after_certificate_gives_5(self):
        study, cert = self.make_cert()
        with open(study, "a", encoding="utf-8") as handle:
            handle.write("\n# edited after the certificate was issued\n")
        code, stdout, _ = run_cli("verify", cert, study)
        self.assertEqual(code, 5)
        self.assertIn("MISMATCH", stdout)

    def test_substantive_change_gives_5(self):
        study, cert = self.make_cert()
        with open(study, encoding="utf-8") as handle:
            text = handle.read().replace("> 1.0", "> 1.5")
        with open(study, "w", encoding="utf-8") as handle:
            handle.write(text)
        self.assertEqual(run_cli("verify", cert, study)[0], 5)

    def test_tampered_certificate_gives_5(self):
        study, cert = self.make_cert()
        with open(cert, encoding="utf-8") as handle:
            envelope = json.load(handle)
        envelope["body"]["verdict"] = "FALSIFIABLE" if envelope["body"]["verdict"] != "FALSIFIABLE" else "WEAK"
        with open(cert, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle)
        self.assertEqual(run_cli("verify", cert, study)[0], 5)

    def test_deterministic_and_failed_load_certificates_verify(self):
        for name in ("toy_good_det", "toy_dup_ids", "toy_leak_open"):
            with self.subTest(toy=name):
                study, cert = self.make_cert(name)
                self.assertEqual(run_cli("verify", cert, study)[0], 0)


class TestModuleEntryPoint(TempDirCase):
    def test_python_dash_m_kapi(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        out = self.path("cert.json")
        done = subprocess.run(
            [sys.executable, "-B", "-m", "kapi", "check", toy_path("toy_good_det"), "--out", out],
            cwd=_helpers.ROOT, capture_output=True, text=True, env=env,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(os.path.exists(out))
        usage = subprocess.run(
            [sys.executable, "-B", "-m", "kapi"], cwd=_helpers.ROOT, capture_output=True, text=True, env=env
        )
        self.assertEqual(usage.returncode, 4)


if __name__ == "__main__":
    unittest.main()
