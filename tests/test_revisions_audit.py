"""Post-freeze revisions of the blind code audit that live in the CLI: R-33 (exit 4 for internal errors, an over-long
integer cell, and a certificate with non-finite numbers).  See ``docs/design/spec-0.6-REVISIONS-post-freeze.md``.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

import _helpers  # noqa: F401  (puts the repository root on sys.path)
from truth_gate import cli


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="tg_audit_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def path(self, name):
        return os.path.join(self.root, name)

    def write(self, name, text):
        with open(self.path(name), "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return self.path(name)


class TestInternalErrorsExit4(Base):
    """R-33: exit 1 means WEAK; an internal error must never look like a verdict."""

    def assert_internal_error(self, code, err):
        self.assertEqual(code, 4)
        lines = [line for line in err.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, err)
        self.assertIn("internal error", lines[0])
        self.assertNotIn("Traceback", err)

    def test_check_with_an_unexpected_exception(self):
        study = self.write("study.py", "x = 1\n")
        with mock.patch.object(cli, "run_gate", side_effect=RuntimeError("boom\nsecond line")):
            code, out, err = run_cli("check", study, "--out", self.path("cert.json"))
        self.assert_internal_error(code, err)
        self.assertIn("RuntimeError", err)
        self.assertIn("boom", err)
        self.assertNotIn("second line", err)  # one line only
        self.assertFalse(os.path.exists(self.path("cert.json")))

    def test_every_command_exits_4_on_an_unexpected_exception(self):
        cert = self.write("cert.json", '{"body": {"mode": "full"}, "body_sha256": "00"}')
        study = self.write("study.py", "x = 1\n")
        data = self.write("d.csv", "a\n1\n")
        cases = (
            ("verify", [cli, "body_sha256"], ["verify", cert, study]),
            ("badge", [cli, "badge_payload"], ["badge", cert]),
            ("suggest", [cli, "suggest_manifest"], ["suggest", data, "--out", self.path("m.toml")]),
            ("init", [cli, "write_scaffold"], ["init", self.path("proj")]),
            ("explain", [cli.explain_module, "explain"], ["explain", "K1"]),
            ("freeze", [cli, "freeze_main"], ["freeze", "verify", cert]),
        )
        for command, (target, name), argv in cases:
            with self.subTest(command=command):
                with mock.patch.object(target, name, side_effect=ValueError("x")):
                    code, _out, err = run_cli(*argv)
                self.assert_internal_error(code, err)

    def test_a_long_message_is_cut_to_one_short_line(self):
        study = self.write("study.py", "x = 1\n")
        with mock.patch.object(cli, "run_gate", side_effect=RuntimeError("m" * 5000)):
            code, _out, err = run_cli("check", study)
        self.assert_internal_error(code, err)
        self.assertLess(len(err), 400)

    def test_usage_errors_and_manifest_errors_keep_their_own_messages(self):
        code, _out, err = run_cli("check", self.path("nope.toml"))
        self.assertEqual(code, 4)
        self.assertNotIn("internal error", err)


class TestOverLongIntegerCell(Base):
    def manifest(self, cell):
        self.write("w.csv", "n,x\n" + cell + ",1.5\n" + "2,2.5\n" * 5)
        return self.write("truthgate.json", json.dumps({
            "study": {"name": "t"},
            "data": {"columns": {"n": {"type": "int"}, "x": {"type": "float"}}},
            "worlds": {"plus": {"file": "w.csv", "provenance": "synthetic"},
                       "minus": {"derive": "plus", "change": "x is zero",
                                 "mutations": [{"op": "constant", "column": "x", "value": 0.0}]}},
            "criteria": [{"id": "C", "pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}],
            "controls": [{"id": "neg", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}],
        }))

    def test_an_over_long_integer_cell_is_a_manifest_error_exit_4_without_a_certificate(self):
        out = self.path("cert.json")
        code, _stdout, err = run_cli("check", self.manifest("9" * 5000), "--out", out)
        self.assertEqual(code, 4)
        self.assertIn("manifest error", err)
        self.assertIn("too long", err)
        self.assertNotIn("internal error", err)
        self.assertFalse(os.path.exists(out))

    def test_a_normal_integer_cell_of_the_same_file_still_loads(self):
        out = self.path("cert.json")
        code, _stdout, err = run_cli("check", self.manifest("7"), "--out", out)
        self.assertNotEqual(code, 4, err)
        self.assertTrue(os.path.exists(out))


class TestNonFiniteCertificates(Base):
    def cert(self, constant):
        text = '{"body": {"tool": "Truth_Gate", "x": %s, "mode": "full"}, "body_sha256": "00"}' % constant
        return self.write("cert.json", text)

    def test_verify_and_badge_exit_4_on_nan_and_infinity(self):
        study = self.write("study.py", "x = 1\n")
        for constant in ("NaN", "Infinity", "-Infinity"):
            path = self.cert(constant)
            with self.subTest(command="verify", constant=constant):
                code, out, err = run_cli("verify", path, study)
                self.assertEqual(code, 4, (out, err))
                self.assertIn("cannot read certificate", err)
                self.assertNotIn("internal error", err)
            with self.subTest(command="badge", constant=constant):
                code, out, err = run_cli("badge", path)
                self.assertEqual(code, 4, (out, err))
                self.assertIn("cannot read certificate", err)

    def test_a_finite_certificate_is_still_read(self):
        self.assertEqual(cli.load_certificate_file(self.write("c.json", '{"a": 1.5}')), {"a": 1.5})
        with self.assertRaises(ValueError):
            cli.load_certificate_file(self.write("c2.json", '{"a": NaN}'))


if __name__ == "__main__":
    unittest.main()
