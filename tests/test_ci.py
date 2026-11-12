"""Truth_Gate 0.4, stage (e): ``truth_gate.ci``, the logic of the GitHub Action (spec 0.6, section 10), and the shape of
``action.yml``.  Every test runs with a fake environment: temporary ``GITHUB_STEP_SUMMARY`` and ``GITHUB_OUTPUT`` files."""

import contextlib
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import unittest

import _helpers
from test_external import FAKE
from truth_gate import ci, cli
from truth_gate.freeze import main as freeze_main

ROOT = _helpers.ROOT
MANIFESTS = os.path.join(ROOT, "tests", "manifests")
ACTION = os.path.join(ROOT, "action.yml")


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def run_ci(env, argv=()):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ci.main(list(argv), env)
    return code, out.getvalue(), err.getvalue()


class CiCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_ci_")
        self.addCleanup(self.cleanup)
        for name in ("trial_example.toml", "synthetic_trial.csv"):
            shutil.copy(os.path.join(MANIFESTS, name), self.dir)
        self.summary = os.path.join(self.dir, "summary.md")
        self.output = os.path.join(self.dir, "output.txt")
        self.target = os.path.join(self.dir, "trial_example.toml")

    def cleanup(self):
        def writable(func, path, *_):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(self.dir, onexc=writable)

    def env(self, **extra):
        env = {"GITHUB_STEP_SUMMARY": self.summary, "GITHUB_OUTPUT": self.output, "TG_TARGET": self.target,
               "TG_QUICK": "true"}
        env.update(extra)
        return env

    def edit_manifest(self, old, new):
        text = read(self.target)
        self.assertIn(old, text)
        with open(self.target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text.replace(old, new))

    def outputs(self):
        return dict(line.split("=", 1) for line in read(self.output).splitlines()) if os.path.exists(self.output) else {}


class TestRun(CiCase):
    def test_a_passing_study_exits_0_and_writes_the_summary_and_the_output(self):
        code, out, err = run_ci(self.env())
        self.assertEqual(code, 0, err)
        cert = os.path.join(self.dir, "trial_example.kapi.json")
        self.assertEqual(self.outputs(), {"certificate": cert})
        self.assertTrue(os.path.isabs(self.outputs()["certificate"]))
        stored = json.loads(read(cert))
        summary = read(self.summary)
        self.assertIn("**Verdict: FALSIFIABLE**", summary)
        self.assertIn("| C1 | FALSIFIABLE | - |", summary)
        self.assertIn("quick (not certifiable)", summary)
        self.assertIn(stored["body_sha256"], summary)
        self.assertIn("Result: passed.", summary)
        self.assertIn("COMPONENT", out)  # the CLI's table reaches the job log

    def test_full_mode_when_quick_is_false_or_empty(self):
        for quick in ("false", "", "FALSE"):
            with self.subTest(quick=quick):
                self.assertEqual(run_ci(self.env(TG_QUICK=quick))[0], 0)
                self.assertEqual(json.loads(read(self.outputs()["certificate"]))["body"]["mode"], "full")

    def test_quick_true_writes_a_quick_certificate(self):
        self.assertEqual(run_ci(self.env(TG_QUICK="True"))[0], 0)
        self.assertEqual(json.loads(read(self.outputs()["certificate"]))["body"]["mode"], "quick")

    def test_inputs_can_come_from_arguments_instead_of_the_environment(self):
        env = {"GITHUB_STEP_SUMMARY": self.summary, "GITHUB_OUTPUT": self.output}
        code, out, err = run_ci(env, ["--target", self.target, "--quick", "true", "--fail-on", ""])
        self.assertEqual(code, 0, err)
        self.assertIn("certificate", self.outputs())

    def test_without_the_github_files_it_still_runs(self):
        code, out, err = run_ci({"TG_TARGET": self.target, "TG_QUICK": "true"})
        self.assertEqual(code, 0, err)

    def test_summary_is_appended_not_replaced(self):
        with open(self.summary, "w", encoding="utf-8") as handle:
            handle.write("earlier step\n")
        run_ci(self.env())
        self.assertTrue(read(self.summary).startswith("earlier step\n"))
        self.assertIn("## Truth_Gate", read(self.summary))


class TestFailOn(CiCase):
    def break_the_control(self):
        # a control that changes nothing cannot make the criterion fail: K4_CONTROL_ALSO_HOLDS, mandatory
        self.edit_manifest('mutations = [ { op = "shuffle", column = "group" } ]',
                           'mutations = [ { op = "offset", column = "yield", value = 0.001 } ]')

    def test_a_verdict_in_fail_on_fails_with_the_clis_code(self):
        self.break_the_control()
        code, out, err = run_ci(self.env())
        self.assertEqual(code, 2, out + err)
        summary = read(self.summary)
        self.assertIn("**Verdict: NOT_FALSIFIABLE**", summary)
        self.assertIn("K4_CONTROL_ALSO_HOLDS", summary)
        self.assertIn("Result: **failed** (exit code 2)", summary)
        self.assertIn("the verdict NOT_FALSIFIABLE is in fail-on", summary)
        self.assertIn("certificate", self.outputs())  # the artifact is uploaded on failure too

    def test_a_verdict_not_in_fail_on_passes(self):
        self.break_the_control()
        self.assertEqual(run_ci(self.env(TG_FAIL_ON="UNDEFINED,UNTESTED"))[0], 0)
        self.assertEqual(run_ci(self.env(TG_FAIL_ON=""))[0], 0)

    def test_the_default_fail_on_is_the_spec_default(self):
        self.assertEqual(ci.DEFAULT_FAIL_ON, "NOT_FALSIFIABLE,UNDEFINED,UNTESTED")
        self.assertEqual(ci.parse_fail_on(None), ("NOT_FALSIFIABLE", "UNDEFINED", "UNTESTED"))
        self.assertEqual(ci.parse_fail_on(" WEAK , UNDEFINED ,"), ("WEAK", "UNDEFINED"))
        self.assertEqual(ci.parse_fail_on(""), ())

    def test_decide_with_hand_made_bodies(self):
        body = {"verdict": "UNTESTED", "components": [{"id": "C", "verdict": "UNTESTED", "flags": []}]}
        self.assertEqual(ci.decide(body, ("UNTESTED",))[0], 6)
        self.assertEqual(ci.decide(body, ("UNDEFINED",))[0], 0)
        body["verdict"] = "UNDEFINED"
        self.assertEqual(ci.decide(body, ("UNDEFINED",))[0], 3)
        body["verdict"] = "WEAK"
        self.assertEqual(ci.decide(body, ("WEAK",))[0], 1)
        body["verdict"] = "FALSIFIABLE"
        self.assertEqual(ci.decide(body, ci.parse_fail_on(None))[0], 0)


class TestSuggestedUnreviewed(CiCase):
    def mark_suggested(self):
        self.edit_manifest("[[controls]]", '[[controls]]\norigin = "suggested"')

    def test_fails_whatever_fail_on_says(self):
        self.mark_suggested()
        for fail_on in ("NOT_FALSIFIABLE,UNDEFINED,UNTESTED", "", "UNDEFINED", "WEAK"):
            with self.subTest(fail_on=fail_on):
                code, out, err = run_ci(self.env(TG_FAIL_ON=fail_on))
                self.assertEqual(code, 1, out + err)
                summary = read(self.summary)
                self.assertIn("SUGGESTED_UNREVIEWED", summary)
        self.assertIn("whatever fail-on says", out)

    def test_the_flag_is_on_the_component_and_the_certificate_still_goes_to_the_output(self):
        self.mark_suggested()
        run_ci(self.env())
        stored = json.loads(read(self.outputs()["certificate"]))
        self.assertIn("SUGGESTED_UNREVIEWED", stored["body"]["components"][0]["flags"])
        self.assertEqual(stored["body"]["verdict"], "WEAK")

    def test_removing_the_origin_key_clears_it(self):
        self.mark_suggested()
        self.assertEqual(run_ci(self.env())[0], 1)
        self.edit_manifest('[[controls]]\norigin = "suggested"', "[[controls]]")
        self.assertEqual(run_ci(self.env())[0], 0)

    def test_has_unreviewed_reads_the_flag_and_the_count(self):
        self.assertTrue(ci.has_unreviewed({"components": [{"flags": ["SUGGESTED_UNREVIEWED"]}]}))
        self.assertTrue(ci.has_unreviewed({"components": [], "suggested_unreviewed": 2}))
        self.assertFalse(ci.has_unreviewed({"components": [{"flags": ["K2_LOW_POWER"]}], "suggested_unreviewed": 0}))
        self.assertFalse(ci.has_unreviewed({}))


class TestFreeze(CiCase):
    def make_freeze(self):
        freeze = os.path.join(self.dir, "FREEZE.json")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(freeze_main(["write", self.target, os.path.join(self.dir, "synthetic_trial.csv"),
                                          "-o", freeze, "--no-readonly"]), 0)
        return freeze

    def test_a_holding_freeze_is_reported_and_passes(self):
        freeze = self.make_freeze()
        code, out, err = run_ci(self.env(TG_FREEZE=freeze))
        self.assertEqual(code, 0, err)
        self.assertIn("FREEZE OK", out)
        self.assertIn("**FREEZE OK**", read(self.summary))

    def test_a_broken_freeze_exits_5_and_still_writes_the_certificate_output(self):
        freeze = self.make_freeze()
        with open(os.path.join(self.dir, "synthetic_trial.csv"), "a", encoding="utf-8", newline="") as handle:
            handle.write("p99,control,1.0\n")
        code, out, err = run_ci(self.env(TG_FREEZE=freeze))
        self.assertEqual(code, 5, out + err)
        summary = read(self.summary)
        self.assertIn("**FREEZE BROKEN**", summary)
        self.assertIn("MODIFIED: synthetic_trial.csv", summary)
        self.assertIn("the freeze does not hold", summary)
        self.assertIn("certificate", self.outputs())

    def test_an_unreadable_freeze_manifest_exits_4(self):
        code, out, err = run_ci(self.env(TG_FREEZE=os.path.join(self.dir, "none.json")))
        self.assertEqual(code, 4)
        self.assertIn("failed to run", read(self.summary))

    def test_a_freeze_failure_outranks_a_verdict_failure(self):
        freeze = self.make_freeze()
        with open(os.path.join(self.dir, "synthetic_trial.csv"), "a", encoding="utf-8", newline="") as handle:
            handle.write("p99,control,1.0\n")
        self.edit_manifest('mutations = [ { op = "shuffle", column = "group" } ]',
                           'mutations = [ { op = "offset", column = "yield", value = 0.001 } ]')
        code, out, err = run_ci(self.env(TG_FREEZE=freeze))
        self.assertEqual(code, 5, out + err)
        self.assertIn("is in fail-on", read(self.summary))  # both reasons are listed


class TestBadInput(CiCase):
    def test_missing_target_exits_4(self):
        code, out, err = run_ci({"GITHUB_STEP_SUMMARY": self.summary, "TG_TARGET": " "})
        self.assertEqual(code, 4)
        self.assertIn("target is required", err)
        self.assertIn("target is required", read(self.summary))

    def test_unknown_fail_on_verdict_and_bad_quick_exit_4(self):
        code, out, err = run_ci(self.env(TG_FAIL_ON="NOT_FALSIFIABLE,BROKEN"))
        self.assertEqual(code, 4)
        self.assertIn("BROKEN", err)
        code, out, err = run_ci(self.env(TG_QUICK="yes"))
        self.assertEqual(code, 4)
        self.assertIn("quick", err)
        self.assertFalse(os.path.exists(self.output))

    def test_a_missing_target_file_exits_4_without_a_certificate_output(self):
        code, out, err = run_ci(self.env(TG_TARGET=os.path.join(self.dir, "nothing.toml")))
        self.assertEqual(code, 4)
        self.assertFalse(os.path.exists(self.output))
        self.assertIn("did not produce a certificate", read(self.summary))

    def test_a_manifest_error_exits_4_without_a_certificate_output(self):
        self.edit_manifest('provenance = "simulated', 'bogus_key = 1\nprovenance = "simulated')
        code, out, err = run_ci(self.env())
        self.assertEqual(code, 4, out + err)
        self.assertFalse(os.path.exists(self.output))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "trial_example.kapi.json")))

    def test_a_stale_certificate_is_not_taken_for_this_runs(self):
        stale = os.path.join(self.dir, "trial_example.kapi.json")
        with open(stale, "w", encoding="utf-8") as handle:
            json.dump({"body": {"verdict": "FALSIFIABLE", "components": []}, "body_sha256": "x"}, handle)
        self.edit_manifest('provenance = "simulated', 'bogus_key = 1\nprovenance = "simulated')
        code, out, err = run_ci(self.env())
        self.assertEqual(code, 4)
        self.assertFalse(os.path.exists(self.output))


class TestPreCommit(CiCase):
    """R-27: ``python -m truth_gate.ci --pre-commit FILE...``, the wrapper of the ``truth-gate-check`` hook."""

    def second_manifest(self, name, old=None, new=None):
        path = os.path.join(self.dir, name)
        shutil.copy(self.target, path)
        if old is not None:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(read(self.target).replace(old, new))
        return path

    def broken_control(self, name):
        return self.second_manifest(name, 'mutations = [ { op = "shuffle", column = "group" } ]',
                                    'mutations = [ { op = "offset", column = "yield", value = 0.001 } ]')

    def broken_manifest(self, name):
        return self.second_manifest(name, 'provenance = "simulated', 'bogus_key = 1\nprovenance = "simulated')

    def folders(self):
        return {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_precommit_")}

    def test_several_files_give_one_line_each_and_exit_0_when_all_hold(self):
        other = self.second_manifest("b_example.toml")
        code, out, err = run_ci({}, ["--pre-commit", self.target, other])
        self.assertEqual(code, 0, out + err)
        lines = out.splitlines()
        self.assertEqual(len(lines), 2, out)
        self.assertEqual(lines[0], f"truth-gate pre-commit: {self.target}: FALSIFIABLE (exit 0)")
        self.assertEqual(lines[1], f"truth-gate pre-commit: {other}: FALSIFIABLE (exit 0)")
        self.assertNotIn("COMPONENT", out)  # the table of `check` is not printed

    def test_no_certificate_is_written_next_to_a_manifest_and_the_temporary_folder_is_removed(self):
        other = self.second_manifest("b_example.toml")
        before = self.folders()
        before_files = sorted(os.listdir(self.dir))
        run_ci({}, ["--pre-commit", self.target, other])
        self.assertEqual(sorted(os.listdir(self.dir)), before_files)  # no *.kapi.json appeared
        self.assertFalse([n for n in os.listdir(self.dir) if n.endswith(".kapi.json")])
        self.assertEqual(self.folders(), before)

    def test_a_certificate_goes_to_a_temporary_folder_outside_the_manifests_folder(self):
        seen = []
        real_main = cli.main

        def spy(argv):
            seen.append(list(argv))
            return real_main(argv)

        original = ci.cli.main
        ci.cli.main = spy
        try:
            run_ci({}, ["--pre-commit", self.target])
        finally:
            ci.cli.main = original
        (argv,) = seen
        self.assertEqual(argv[:3], ["check", self.target, "--quick"])
        out = argv[argv.index("--out") + 1]
        self.assertNotEqual(os.path.dirname(os.path.abspath(out)), os.path.abspath(self.dir))
        self.assertTrue(os.path.abspath(out).startswith(os.path.abspath(tempfile.gettempdir())))

    def test_the_exit_code_is_the_most_severe_one(self):
        good = self.target
        weak_or_worse = self.broken_control("b_control.toml")  # NOT_FALSIFIABLE, exit 2
        bad = self.broken_manifest("c_bad.toml")  # exit 4
        cases = (([good, weak_or_worse], 2), ([weak_or_worse, good], 2), ([good, bad], 4), ([bad, weak_or_worse], 4),
                 ([weak_or_worse, bad, good], 4), ([good], 0))
        for files, expected in cases:
            with self.subTest(files=[os.path.basename(f) for f in files]):
                code, out, err = run_ci({}, ["--pre-commit", *files])
                self.assertEqual(code, expected, out + err)
                self.assertEqual(len(out.splitlines()), len(files))

    def test_a_manifest_error_line_says_why(self):
        bad = self.broken_manifest("c_bad.toml")
        code, out, err = run_ci({}, ["--pre-commit", bad])
        self.assertEqual(code, 4)
        (line,) = out.splitlines()
        self.assertIn("not checked (exit 4)", line)
        self.assertIn("manifest error", line)
        self.assertNotIn("\n", line)

    def test_a_missing_file_is_exit_4_and_the_other_files_are_still_checked(self):
        code, out, err = run_ci({}, ["--pre-commit", os.path.join(self.dir, "nothing.toml"), self.target])
        self.assertEqual(code, 4)
        lines = out.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("not checked (exit 4)", lines[0])
        self.assertIn("FALSIFIABLE (exit 0)", lines[1])

    def test_it_is_quick_mode(self):
        code, out, err = run_ci({}, ["--pre-commit", self.target])
        self.assertEqual(code, 0)
        calls = []
        real_main = cli.main
        original = ci.cli.main
        ci.cli.main = lambda argv: (calls.append(argv), real_main(argv))[1]
        try:
            run_ci({}, ["--pre-commit", self.target])
        finally:
            ci.cli.main = original
        self.assertIn("--quick", calls[0])

    def test_no_files_is_a_pass_and_other_options_are_usage_errors(self):
        self.assertEqual(run_ci({}, ["--pre-commit"])[0], 0)
        for extra in (["--target", self.target], ["--freeze", "F.json"], ["--quick", "true"], ["--fail-on", "WEAK"]):
            with self.subTest(extra=extra):
                code, out, err = run_ci({}, ["--pre-commit", self.target, *extra])
                self.assertEqual(code, 4)
                self.assertIn("--pre-commit takes only FILE arguments", err)
        code, out, err = run_ci({}, [self.target])
        self.assertEqual(code, 4)
        self.assertIn("only valid with --pre-commit", err)

    def test_the_severity_order_follows_r26_then_the_verdict_order(self):
        self.assertEqual(ci.most_severe([]), 0)
        self.assertEqual(ci.most_severe([0, 1]), 1)
        self.assertEqual(ci.most_severe([1, 6, 2, 3]), 3)  # UNDEFINED is the worst verdict, then NOT_FALSIFIABLE, UNTESTED, WEAK
        self.assertEqual(ci.most_severe([1, 6, 2]), 2)
        self.assertEqual(ci.most_severe([1, 6]), 6)
        self.assertEqual(ci.most_severe([3, 5]), 5)  # a broken freeze beats a verdict
        self.assertEqual(ci.most_severe([5, 4, 3]), 4)  # an input or manifest error beats everything

    def test_an_unexpected_exception_exits_4_with_one_line(self):
        original = ci.cli.main

        def boom(argv):
            raise RuntimeError("boom")

        ci.cli.main = boom
        try:
            code, out, err = run_ci({}, ["--pre-commit", self.target])
        finally:
            ci.cli.main = original
        self.assertEqual(code, 4)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertIn("internal error", err)
        self.assertFalse([n for n in os.listdir(self.dir) if n.endswith(".kapi.json")])


class TestNotes(CiCase):
    def test_study_notes_and_the_unguarded_commands_reach_the_summary(self):
        study = os.path.join(self.dir, "cmd")
        os.makedirs(study)
        for name, text in (("fake_tg.py", FAKE), ("w.py", "def plus(rng):\n    return {'x': rng.normal(2.0, 1.0, 30)}\n\n\n"
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
        code, out, err = run_ci(self.env(TG_TARGET=path, TG_FAIL_ON=""))
        self.assertIn(code, (0, 1), out + err)
        summary = read(self.summary)
        self.assertIn("Study notes:", summary)
        self.assertIn("`K6_EXTERNAL_UNGUARDED`", summary)
        self.assertIn("fake_tg.py", summary)

    def test_render_summary_escapes_table_cells(self):
        body = {"verdict": "WEAK", "components": [{"id": "a|b", "verdict": "WEAK", "flags": ["X|Y"]}], "study_flags": [],
                "study_notes": [{"note": "EXTERNAL_DIED", "commands": [["node", "a b.js"]]}]}
        text = ci.render_summary(body, target="t.toml", quick=False, certificate="c.json", sha="abc", check_code=1,
                                 freeze_target=None, freeze_code=None, freeze_text="", reasons=[], exit_code=0)
        self.assertIn("| a\\|b | WEAK | `X\\|Y` |", text)
        self.assertIn("`EXTERNAL_DIED`: `node 'a b.js'`", text)


class TestActionFile(unittest.TestCase):
    """``action.yml`` is a composite action; its shape is checked with the tiny parser of ``yaml_lite``."""

    @classmethod
    def setUpClass(cls):
        from yaml_lite import load
        cls.doc = load(read(ACTION))

    def test_inputs_match_spec_section_10(self):
        inputs = self.doc["inputs"]
        self.assertEqual(set(inputs), {"target", "freeze", "quick", "fail-on"})
        self.assertIs(inputs["target"]["required"], True)
        self.assertIs(inputs["freeze"].get("required", False), False)
        self.assertEqual(inputs["quick"]["default"], "false")
        self.assertEqual(inputs["fail-on"]["default"], ci.DEFAULT_FAIL_ON)

    def test_it_is_a_composite_action_with_the_certificate_output(self):
        self.assertEqual(self.doc["runs"]["using"], "composite")
        self.assertIn("certificate", self.doc["outputs"])
        self.assertIn("steps.tg.outputs.certificate", self.doc["outputs"]["certificate"]["value"])

    def test_third_party_actions_are_pinned_to_a_full_sha_or_an_exact_version(self):
        uses = [s["uses"] for s in self.doc["runs"]["steps"] if "uses" in s]
        self.assertEqual(len(uses), 2)
        for ref in uses:
            name, _, version = ref.partition("@")
            self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", version) or re.fullmatch(r"v\d+\.\d+\.\d+", version), ref)
        self.assertEqual(sorted(u.split("@")[0] for u in uses), ["actions/setup-python", "actions/upload-artifact"])

    def test_steps_install_the_actions_own_checkout_and_run_the_ci_module(self):
        runs = "\n".join(s["run"] for s in self.doc["runs"]["steps"] if "run" in s)
        self.assertIn('pip install "$GITHUB_ACTION_PATH"', runs)
        self.assertIn("python -m truth_gate.ci", runs)
        ci_step = next(s for s in self.doc["runs"]["steps"] if s.get("id") == "tg")
        self.assertEqual(ci_step["shell"], "bash")
        for name, value in (("TG_TARGET", "inputs.target"), ("TG_FREEZE", "inputs.freeze"), ("TG_QUICK", "inputs.quick"),
                            ("TG_FAIL_ON", "inputs.fail-on")):  # inputs reach the script as env, never spliced into it
            self.assertIn(value, ci_step["env"][name])
            self.assertNotIn("${{", ci_step["run"])

    def test_the_certificate_is_uploaded_even_when_the_check_failed(self):
        upload = next(s for s in self.doc["runs"]["steps"] if s.get("uses", "").startswith("actions/upload-artifact"))
        self.assertIn("always()", upload["if"])
        self.assertIn("steps.tg.outputs.certificate", upload["if"])
        self.assertIn("steps.tg.outputs.certificate", upload["with"]["path"])

    def test_the_env_names_the_module_reads_are_the_ones_the_action_sets(self):
        ci_step = next(s for s in self.doc["runs"]["steps"] if s.get("id") == "tg")
        with open(os.path.join(ROOT, "truth_gate", "ci.py"), encoding="utf-8") as handle:
            source = handle.read()
        for name in ci_step["env"]:
            self.assertIn(f'"{name}"', source)


if __name__ == "__main__":
    unittest.main()
