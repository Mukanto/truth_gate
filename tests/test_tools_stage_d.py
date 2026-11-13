"""Truth_Gate 0.4, stage (d): ``init``, ``freeze``, ``badge`` and ``explain`` (spec 0.6, sections 9 and 11)."""

import ast
import contextlib
import copy
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

import _helpers
from test_external import FAKE
from test_toy_flags import FLAG_TOYS
from truth_gate import certificate, checks, cli, explain as explain_module, external, freeze as package_freeze
from truth_gate import k8, passes
from truth_gate.badge import badge_payload

ROOT = _helpers.ROOT
PROTOCOL = os.path.join(ROOT, "protocol")
STANDALONE = os.path.join(PROTOCOL, "tools", "freeze.py")
A4_FIXED = os.path.join(ROOT, "evaluation", "phase_a", "a4", "fixed", "truthgate.toml")


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def read(path, mode="rb"):
    with open(path, mode) as handle:
        return handle.read()


class TempCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_tools_")
        self.addCleanup(self.cleanup)

    def cleanup(self):
        def writable(func, path, *_):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(self.dir, onexc=writable)

    def path(self, *parts):
        return os.path.join(self.dir, *parts)


# ---------------------------------------------------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------------------------------------------------

class TestInit(TempCase):
    FILES = ["PREREG.md", "truthgate.toml", "BLIND_AUDIT_PROMPT.md", "run_guarded.py"]
    WORKFLOW = os.path.join(".github", "workflows", "truth-gate.yml")

    def test_writes_the_four_files_and_the_protocol_templates_byte_for_byte(self):
        target = self.path("study")
        code, out, err = run_cli("init", target)
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(os.listdir(target)), sorted(self.FILES))
        for written, template in (("PREREG.md", "PREREG_TEMPLATE.md"), ("BLIND_AUDIT_PROMPT.md", "BLIND_AUDIT_PROMPT.md"),
                                  ("run_guarded.py", "run_guarded.py")):
            self.assertEqual(read(os.path.join(target, written)), read(os.path.join(PROTOCOL, "templates", template)))
        self.assertNotIn(".github", os.listdir(target))
        self.assertEqual(out.count("wrote "), 4)

    def test_default_directory_is_the_current_one(self):
        old = os.getcwd()
        os.chdir(self.dir)
        try:
            code, out, err = run_cli("init")
        finally:
            os.chdir(old)
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(os.listdir(self.dir)), sorted(self.FILES))

    def test_ci_writes_the_workflow_that_uses_the_action(self):
        code, out, err = run_cli("init", self.dir, "--ci")
        self.assertEqual(code, 0, err)
        text = read(os.path.join(self.dir, self.WORKFLOW), "r")
        self.assertIn("uses: Mukanto/truth_gate@v0.5.0", text)
        for key in ("target:", "# freeze:", "# quick:", "# fail-on:"):  # the inputs of spec section 10
            self.assertIn(key, text)
        self.assertIn("pull_request", text)

    def test_never_overwrites_exit_4_lists_the_existing_files_and_writes_nothing(self):
        for existing in ("truthgate.toml", "run_guarded.py"):
            with self.subTest(existing=existing):
                target = self.path("s_" + existing)
                os.makedirs(target)
                with open(os.path.join(target, existing), "w", encoding="utf-8") as handle:
                    handle.write("mine")
                code, out, err = run_cli("init", target)
                self.assertEqual(code, 4)
                self.assertIn(existing, err)
                self.assertEqual(read(os.path.join(target, existing), "r"), "mine")
                self.assertEqual(os.listdir(target), [existing])  # nothing else was written

    def test_an_existing_workflow_blocks_ci_init_and_two_files_are_both_listed(self):
        target = self.path("s")
        os.makedirs(os.path.join(target, ".github", "workflows"))
        for name in (self.WORKFLOW, "PREREG.md"):
            with open(os.path.join(target, name), "w", encoding="utf-8") as handle:
                handle.write("mine")
        code, out, err = run_cli("init", target, "--ci")
        self.assertEqual(code, 4)
        self.assertIn("truth-gate.yml", err)
        self.assertIn("PREREG.md", err)
        self.assertFalse(os.path.exists(os.path.join(target, "truthgate.toml")))
        # without --ci the workflow does not matter
        self.assertEqual(run_cli("init", self.path("other"), "--ci")[0], 0)

    def test_the_scaffold_manifest_refuses_to_run_until_provenance_is_set_and_then_runs(self):
        run_cli("init", self.dir)
        manifest = self.path("truthgate.toml")
        code, out, err = run_cli("check", manifest, "--out", self.path("c.json"))
        self.assertEqual(code, 4)
        self.assertIn("provenance", err)
        rows = ["unit,group,value"]
        for i in range(40):
            treated = i % 2 == 0
            rows.append(f"u{i},{'treated' if treated else 'control'},{(1.0 if treated else 0.2) + 0.01 * (i % 7)}")
        with open(self.path("synthetic_data.csv"), "w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(rows) + "\n")
        text = read(manifest, "r").replace('provenance = "TODO"', 'provenance = "made up for this test"')
        with open(manifest, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        code, out, err = run_cli("check", manifest, "--out", self.path("c.json"))
        self.assertIn(code, (0, 1, 2), out + err)
        body = json.loads(read(self.path("c.json"), "r"))["body"]
        self.assertEqual(body["study"]["deterministic"], False)
        self.assertEqual(body["m_k8"], 2)  # the scaffold sets rows_exchangeable

    def test_the_package_ships_the_templates(self):
        with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as handle:
            self.assertIn('truth_gate = ["templates/*"]', handle.read())
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "truth_gate", "templates", "truth-gate.yml")))


# ---------------------------------------------------------------------------------------------------------------------
# freeze
# ---------------------------------------------------------------------------------------------------------------------

def load_standalone():
    spec = importlib.util.spec_from_file_location("standalone_freeze", STANDALONE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixedClock:
    """Stands in for the ``datetime`` module of a freeze module, so two runs write the same ``created_utc``."""

    def __init__(self, real):
        self.timezone = real.timezone
        self.datetime = type("FixedDatetime", (), {
            "now": staticmethod(lambda tz=None: real.datetime(2026, 11, 12, 10, 0, 0, tzinfo=tz))})


class TestFreeze(TempCase):
    def make_tree(self, name):
        base = self.path(name)
        for rel, text in (("study/a.py", "print('a')\n"), ("study/sub/b.txt", "b\n"), ("c.csv", "x,y\n1,2\n")):
            target = os.path.join(base, *rel.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
        os.makedirs(os.path.join(base, "study", "__pycache__"))
        with open(os.path.join(base, "study", "__pycache__", "a.pyc"), "wb") as handle:
            handle.write(b"ignored")
        return base

    def test_write_is_byte_identical_to_the_standalone_script(self):
        standalone = load_standalone()
        import datetime as real
        a, b, c = (self.make_tree(n) for n in ("a", "b", "c"))
        with mock.patch.object(standalone, "datetime", FixedClock(real)), \
                mock.patch.object(package_freeze, "datetime", FixedClock(real)):
            for flag in ((), ("--no-readonly",)):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(standalone.main(["write", os.path.join(a, "study"), os.path.join(a, "c.csv"),
                                                      "-o", os.path.join(a, "FREEZE.json"), *flag]), 0)
                    self.assertEqual(package_freeze.main(["write", os.path.join(b, "study"), os.path.join(b, "c.csv"),
                                                          "-o", os.path.join(b, "FREEZE.json"), *flag]), 0)
                    self.assertEqual(cli.main(["freeze", "write", os.path.join(c, "study"), os.path.join(c, "c.csv"),
                                               "-o", os.path.join(c, "FREEZE.json"), *flag]), 0)
                reference = read(os.path.join(a, "FREEZE.json"))
                self.assertEqual(read(os.path.join(b, "FREEZE.json")), reference)
                self.assertEqual(read(os.path.join(c, "FREEZE.json")), reference)
                self.assertIn(b"study/sub/b.txt", reference)
                self.assertNotIn(b"__pycache__", reference)
                for tree in (a, b, c):  # the second round writes a new manifest
                    os.chmod(os.path.join(tree, "FREEZE.json"), stat.S_IWRITE)
                    os.remove(os.path.join(tree, "FREEZE.json"))

    def test_the_package_functions_are_the_standalone_functions(self):
        standalone = load_standalone()
        names = ("sha256_file", "core_hash", "_expand", "_make_readonly", "_is_writable", "cmd_write", "load_manifest",
                 "verify_manifest", "cmd_verify")
        for name in names:
            with self.subTest(function=name):
                ours = inspect.getsource(getattr(package_freeze, name)).replace("\r\n", "\n")
                theirs = inspect.getsource(getattr(standalone, name)).replace("\r\n", "\n")
                self.assertEqual(ours, theirs)
        self.assertEqual(package_freeze.FORMAT, standalone.FORMAT)

    def test_verify_semantics_and_exit_codes_match_the_standalone_script(self):
        standalone = load_standalone()
        tree = self.make_tree("t")
        manifest = os.path.join(tree, "FREEZE.json")
        self.assertEqual(run_cli("freeze", "write", os.path.join(tree, "study"), "-o", manifest, "--no-readonly")[0], 0)
        self.assertEqual(run_cli("freeze", "write", os.path.join(tree, "study"), "-o", manifest)[0], 2)  # no overwrite
        results = []
        for runner in (lambda *a: run_cli("freeze", *a), None):
            if runner is None:
                def runner(*a):
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                        code = standalone.main(list(a))
                    return code, out.getvalue(), ""
            ok = runner("verify", manifest)
            self.assertEqual((ok[0], ok[1].strip().splitlines()[-1]), (0, "FREEZE OK"))
            with open(os.path.join(tree, "study", "a.py"), "a", encoding="utf-8") as handle:
                handle.write("# edited\n")
            bad = runner("verify", manifest)
            self.assertEqual(bad[0], 1)
            self.assertIn("MODIFIED: study/a.py", bad[1])
            self.assertIn("FREEZE BROKEN", bad[1])
            results.append(bad[:2])
            with open(os.path.join(tree, "study", "a.py"), "w", encoding="utf-8", newline="") as handle:
                handle.write("print('a')\n")
            self.assertEqual(runner("verify", manifest)[0], 0)
            self.assertEqual(runner("verify", os.path.join(tree, "none.json"))[0], 2)
        self.assertEqual(results[0], results[1])

    def test_usage_errors_exit_2_like_the_standalone_script(self):
        self.assertEqual(run_cli("freeze")[0], 2)
        self.assertEqual(run_cli("freeze", "write")[0], 2)
        self.assertEqual(run_cli("freeze", "frobnicate")[0], 2)

    def test_an_edited_manifest_is_detected(self):
        tree = self.make_tree("t")
        manifest = os.path.join(tree, "FREEZE.json")
        run_cli("freeze", "write", os.path.join(tree, "study"), "-o", manifest, "--no-readonly")
        data = json.loads(read(manifest, "r"))
        data["files"]["study/a.py"] = "0" * 64
        with open(manifest, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2)
        code, out, err = run_cli("freeze", "verify", manifest)
        self.assertEqual(code, 1)
        self.assertIn("MANIFEST EDITED", out)


# ---------------------------------------------------------------------------------------------------------------------
# badge
# ---------------------------------------------------------------------------------------------------------------------

UNGUARDED = {"note": external.NOTE_UNGUARDED, "commands": [["node", "criteria.js"]]}


class TestBadge(TempCase):
    @classmethod
    def setUpClass(cls):
        cls.envelope = certificate.run_gate(A4_FIXED)

    def envelope_with(self, verdict=None, notes=None, mode=None):
        body = copy.deepcopy(self.envelope["body"])
        if verdict is not None:
            body["verdict"] = verdict
        if notes is not None:
            body["study_notes"] = notes
        if mode is not None:
            body["mode"] = mode
        return certificate.make_envelope(body)

    def write(self, envelope, name="cert.json"):
        path = self.path(name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle)
        return path

    def test_the_endpoint_json_of_a_real_certificate(self):
        self.assertEqual(self.envelope["body"]["verdict"], "FALSIFIABLE")
        out = self.path("badge.json")
        code, stdout, err = run_cli("badge", self.write(self.envelope), "--out", out)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(read(out, "r")), {"schemaVersion": 1, "label": "truth gate",
                                                      "message": "FALSIFIABLE", "color": "brightgreen"})
        self.assertEqual(list(json.loads(read(out, "r"))), ["schemaVersion", "label", "message", "color"])

    def test_without_out_the_json_is_printed(self):
        code, stdout, err = run_cli("badge", self.write(self.envelope))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["message"], "FALSIFIABLE")

    def test_colours_and_the_unguarded_label(self):
        table = (
            ("FALSIFIABLE", [], "FALSIFIABLE", "brightgreen"),
            ("FALSIFIABLE", [UNGUARDED], "FALSIFIABLE (unguarded)", "green"),
            ("WEAK", [], "WEAK", "yellow"),
            ("WEAK", [UNGUARDED], "WEAK (unguarded)", "yellow"),
            ("NOT_FALSIFIABLE", [], "NOT_FALSIFIABLE", "red"),
            ("NOT_FALSIFIABLE", [UNGUARDED], "NOT_FALSIFIABLE (unguarded)", "red"),
            ("UNDEFINED", [], "UNDEFINED", "red"),
            ("UNTESTED", [], "UNTESTED", "red"),
        )
        for verdict, notes, message, color in table:
            with self.subTest(verdict=verdict, unguarded=bool(notes)):
                payload = badge_payload(self.envelope_with(verdict, notes))
                self.assertEqual((payload["message"], payload["color"]), (message, color))
        # another note does not make a badge unguarded
        died = [{"note": "EXTERNAL_DIED", "commands": [["x"]]}]
        self.assertEqual(badge_payload(self.envelope_with("FALSIFIABLE", died))["message"], "FALSIFIABLE")

    def test_a_hash_mismatch_exits_5_and_writes_nothing(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["body"]["verdict"] = "FALSIFIABLE" if envelope["body"]["verdict"] != "FALSIFIABLE" else "WEAK"
        out = self.path("badge.json")
        code, stdout, err = run_cli("badge", self.write(envelope), "--out", out)
        self.assertEqual(code, 5)
        self.assertIn("MISMATCH", stdout)
        self.assertFalse(os.path.exists(out))
        envelope = copy.deepcopy(self.envelope)
        envelope["body_sha256"] = "0" * 64
        self.assertEqual(run_cli("badge", self.write(envelope))[0], 5)

    def test_the_hash_is_checked_before_the_quick_refusal(self):
        envelope = self.envelope_with(mode="quick")
        envelope["body"]["verdict"] = "WEAK"  # altered after the hash was made
        self.assertEqual(run_cli("badge", self.write(envelope))[0], 5)

    def test_a_quick_mode_certificate_is_refused_with_exit_4(self):
        out = self.path("badge.json")
        quick = certificate.run_gate(A4_FIXED, quick=True)
        self.assertEqual(quick["body"]["mode"], "quick")
        code, stdout, err = run_cli("badge", self.write(quick), "--out", out)
        self.assertEqual(code, 4)
        self.assertIn("quick", err)
        self.assertFalse(os.path.exists(out))

    def test_not_a_certificate_exits_4(self):
        junk = self.path("junk.json")
        with open(junk, "w", encoding="utf-8") as handle:
            handle.write("[1, 2")
        self.assertEqual(run_cli("badge", junk)[0], 4)
        self.assertEqual(run_cli("badge", self.write({"body": 1, "body_sha256": "x"}))[0], 4)
        self.assertEqual(run_cli("badge", self.write({"nope": 1}))[0], 4)
        self.assertEqual(run_cli("badge", self.path("missing.json"))[0], 4)

    def test_a_real_certificate_with_a_command_criterion_says_unguarded(self):
        study = self.path("cmd")
        os.makedirs(study)
        for name, text in (("fake_tg.py", FAKE), ("w.py", "import numpy as np\n\n\ndef plus(rng):\n    return {'x': rng.normal(2.0, 1.0, 30)}\n\n\n"
                                                         "def minus(rng):\n    return {'x': rng.normal(0.0, 1.0, 30)}\n")):
            with open(os.path.join(study, name), "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
        manifest = {
            "study": {"name": "cmd"}, "data": {"rows": ["x"]},
            "worlds": {"plus": {"python": "w.py:plus"}, "minus": {"python": "w.py:minus", "change": "mean 2 -> 0"}},
            "criteria": [{"id": "C", "command": [sys.executable, "fake_tg.py", "mean"]}],
            "controls": [{"id": "neg", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}],
            "external": {"uses": ["fake_tg.py"]}, "budget": {"samples": 30, "quick_samples": 5},
        }
        path = os.path.join(study, "truthgate.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle)
        cert = self.path("cmd.kapi.json")
        code, out, err = run_cli("check", path, "--out", cert)
        self.assertIn(code, (0, 1, 2), err)
        self.assertIn("K6_EXTERNAL_UNGUARDED", out)
        code, out, err = run_cli("badge", cert)
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["message"].endswith(" (unguarded)"), payload)
        self.assertEqual(payload["message"].split(" ")[0], json.loads(read(cert, "r"))["body"]["verdict"])


# ---------------------------------------------------------------------------------------------------------------------
# explain
# ---------------------------------------------------------------------------------------------------------------------

FLAG_NAME = re.compile(r"^(K[1-8]_[A-Z0-9_]+|NONDETERMINISTIC|BAD_RETURN|SUGGESTED_UNREVIEWED|EXTERNAL_DIED)(:.*)?$")
FAMILY_HEADS = re.compile(r"^(HIGH_RATE|K5_INCONCLUSIVE):$")


def emitted_names():
    """Every flag and note name the code can emit: the flag tables, plus every string literal of the package that has
    the shape of a flag name (a literal or the head of an f-string), so that a flag outside the tables is found too."""
    names = set()
    for table in (checks.MANDATORY_FLAGS, checks.MANDATORY_FLAGS_SCHEMA2, checks.CAPPING_FLAGS,
                  checks.CAPPING_FLAGS_SCHEMA2, checks.INFORMATIONAL_FLAGS, checks.INFORMATIONAL_FLAGS_SCHEMA2,
                  checks.SUPPRESSIBLE_FLAGS, checks.UNTESTED_FLAGS, checks.STUDY_LEVEL_FLAGS, k8.K8_FLAGS):
        names |= set(table)
    names |= set(checks.MANDATORY_PREFIXES) | set(checks.CAPPING_PREFIXES)
    names |= {external.NOTE_UNGUARDED, external.NOTE_DIED, passes.SUGGESTED_UNREVIEWED}
    package = os.path.join(ROOT, "truth_gate")
    for name in sorted(os.listdir(package)):
        if not name.endswith(".py") or name == "explain.py":
            continue
        with open(os.path.join(package, name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        exported = {c.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                    and any(getattr(t, "id", None) == "__all__" for t in node.targets)
                    for c in ast.walk(node.value) if isinstance(c, ast.Constant)}  # identifiers, not flags
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value not in exported:
                if FLAG_NAME.match(node.value) or FAMILY_HEADS.match(node.value):
                    names.add(node.value)
    return names


class TestExplain(unittest.TestCase):
    def test_every_flag_and_note_the_code_can_emit_is_explained(self):
        names = emitted_names()
        self.assertGreaterEqual(len(names), 30)
        for required in ("K1_UNDEFINED", "K8_NOT_INVARIANT", "K8_SOME_CHANGES", "K8_INCONCLUSIVE", "SUGGESTED_UNREVIEWED",
                         "K6_EXTERNAL_UNGUARDED", "EXTERNAL_DIED", "HIGH_RATE:", "K5_INCONCLUSIVE:", "K2_MINUS_UNREAD"):
            self.assertIn(required, names)
        missing = [n for n in sorted(names) if explain_module.explain(n if not n.endswith(":") else n + "x") is None]
        self.assertEqual(missing, [])

    def test_no_explanation_describes_a_name_the_code_does_not_emit(self):
        emitted = emitted_names()
        stale = [k for k in explain_module.EXPLANATIONS if k not in emitted]
        self.assertEqual(stale, [])

    def test_every_flag_the_toy_studies_raise_is_explained(self):
        for flag, (raising, _) in FLAG_TOYS.items():
            b = _helpers.body(raising)
            raised = set(b["study_flags"]) | {f for c in b["components"] for f in c["flags"]}
            raised = {f for f in raised if f.startswith(flag.replace(":*", ""))} or raised
            for name in raised:
                with self.subTest(toy=raising, flag=name):
                    self.assertIsNotNone(explain_module.explain(name))

    def test_each_entry_has_meaning_cause_and_a_protocol_rule_that_exists(self):
        with open(os.path.join(PROTOCOL, "PROTOCOL.md"), encoding="utf-8") as handle:
            protocol = handle.read()
        items = len(re.findall(r"(?m)^(\d+)\. \*\*", protocol.split("## 2. The run")[0]))
        self.assertEqual(items, 16)
        for key, (meaning, cause, rule) in explain_module.EXPLANATIONS.items():
            with self.subTest(key=key):
                self.assertTrue(meaning.strip() and cause.strip() and rule.strip())
                self.assertTrue("§" in rule or rule.startswith("No "), rule)
                for number in re.findall(r"§1\.(\d+)", rule):
                    self.assertTrue(1 <= int(number) <= items, rule)
        self.assertIn("## 4. The repair loop", protocol)
        self.assertIn("## 5. Automated checkers", protocol)

    def test_the_kind_comes_from_the_code_tables(self):
        kinds = {
            "K4_NO_CONTROL": "mandatory", "K8_NOT_INVARIANT": "mandatory", "HIGH_RATE:probe:noise": "mandatory",
            "K4_WAIVED": "capping", "K8_INCONCLUSIVE": "capping", "SUGGESTED_UNREVIEWED": "capping",
            "K5_INCONCLUSIVE:probe:noise": "capping", "K2_MINUS_UNREAD": "information", "K8_SOME_CHANGES": "information",
            "BAD_RETURN": "information", "K6_LEAK_ATTEMPT": "study-level", "NONDETERMINISTIC": "study-level",
            "K2_MINUS_IDENTICAL": "UNTESTED", "K1_UNDEFINED": "UNDEFINED", "K6_EXTERNAL_UNGUARDED": "study note",
            "EXTERNAL_DIED": "study note",
        }
        for name, kind in kinds.items():
            with self.subTest(name=name):
                self.assertIn(kind, explain_module.explain(name).splitlines()[0])

    def test_the_command_line(self):
        code, out, err = run_cli("explain", "K4_NO_CONTROL")
        self.assertEqual(code, 0, err)
        for label in ("Meaning:", "Usual cause:", "Protocol rule:"):
            self.assertIn(label, out)
        self.assertIn("§1.5", out)
        self.assertEqual(run_cli("explain", "k4_no_control")[1], out)  # case does not matter
        code, out, err = run_cli("explain", "HIGH_RATE:probe:noise")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("HIGH_RATE:probe:noise"))
        self.assertEqual(run_cli("explain", "HIGH_RATE")[0], 0)
        code, out, err = run_cli("explain", "NO_SUCH_FLAG")
        self.assertEqual(code, 4)
        self.assertIn("K4_NO_CONTROL", err)  # the known names are listed


if __name__ == "__main__":
    unittest.main()
