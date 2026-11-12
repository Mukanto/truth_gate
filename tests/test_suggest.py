"""Truth_Gate 0.4, stage (d): ``suggest`` (spec 0.6, section 8) and the review cap SUGGESTED_UNREVIEWED."""

import contextlib
import io
import json
import os
import re
import shutil
import tempfile
import tomllib
import unittest

import _helpers
from truth_gate import certificate, cli
from truth_gate.common import ManifestError
from truth_gate.manifest import parse_manifest
from truth_gate.patterns import PATTERN_NAMES
from truth_gate.suggest import WARNING_LINES

CSV = os.path.join(_helpers.ROOT, "tests", "manifests", "synthetic_trial.csv")


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def uncomment(block_lines):
    return "\n".join(re.sub(r"^# ?", "", line) for line in block_lines)


class SuggestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_suggest_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.csv = os.path.join(self.dir, "trial.csv")
        with open(CSV, encoding="utf-8", newline="") as handle:  # the trial file plus a numeric `dose` column
            rows = handle.read().splitlines()
        with open(self.csv, "w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join([rows[0] + ",dose"] + [f"{r},{0.5 * i}" for i, r in enumerate(rows[1:])]) + "\n")
        self.out = os.path.join(self.dir, "truthgate.toml")

    def suggest(self, *extra, out=None):
        return run_cli("suggest", self.csv, *extra, "--out", out or self.out)

    def text(self, out=None):
        with open(out or self.out, encoding="utf-8") as handle:
            return handle.read()

    def write_manifest(self, text, name="edited.toml"):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        return path

    def reviewed(self, text):
        """The manifest with a provenance written in (a human step)."""
        return text.replace('provenance = "TODO"', 'provenance = "a pilot file simulated for this test"')

    def check(self, path):
        cert = os.path.join(self.dir, "cert.json")
        if os.path.exists(cert):
            os.remove(cert)
        code, out, err = run_cli("check", path, "--out", cert)
        body = None
        if os.path.exists(cert):
            with open(cert, encoding="utf-8") as handle:
                body = json.load(handle)["body"]
        return code, out, err, body

    def templates(self, text):
        """The commented criterion templates as ``{id: [lines]}``."""
        lines = text.split("\n")
        out = {}
        for i, line in enumerate(lines):
            if line == "# [[criteria]]":
                cid = re.match(r'# id = "(.*)"', lines[i + 1]).group(1)
                j = i + 1
                while j < len(lines) and lines[j].startswith("# ") and lines[j] != "# [[criteria]]":
                    j += 1
                out[cid] = lines[i:j]
        return out


class TestOutput(SuggestCase):
    ARGS = ("--outcome", "yield", "--group", "group", "--reference", "control")

    def test_prints_and_comments_the_warning(self):
        code, out, err = self.suggest(*self.ARGS)
        self.assertEqual(code, 0, err)
        for line in WARNING_LINES:
            self.assertIn(line, out)
            self.assertIn("# " + line, self.text())
        self.assertIn("NOT the real study data", out)
        self.assertTrue(self.text().startswith("# truth-gate suggest"))

    def test_the_output_parses_as_toml_with_inferred_types_and_given_roles(self):
        self.suggest(*self.ARGS)
        parsed = tomllib.loads(self.text())
        self.assertEqual(parsed["data"]["columns"], {
            "plot": {"type": "str"}, "group": {"type": "str", "role": "group"},
            "yield": {"type": "float", "role": "outcome"}, "dose": {"type": "float"},
        })
        self.assertNotIn("rows_exchangeable", parsed["data"])
        self.assertEqual(parsed["worlds"]["plus"], {"file": "trial.csv", "provenance": "TODO", "resample": "bootstrap",
                                                    "origin": "suggested"})
        minus = parsed["worlds"]["minus"]
        self.assertEqual(minus["derive"], "plus")
        self.assertEqual(minus["mutations"], [{"op": "null_effect", "outcome": "yield", "group": "group",
                                               "reference": "control"}])
        self.assertEqual(minus["origin"], "suggested")
        self.assertEqual([(c["id"], c["mutations"]) for c in parsed["controls"]],
                         [("labels_shuffled", [{"op": "shuffle", "column": "group"}])])

    def test_no_active_criterion(self):
        self.suggest(*self.ARGS)
        self.assertNotIn("criteria", tomllib.loads(self.text()))

    def test_every_generated_declaration_carries_origin_suggested(self):
        self.suggest(*self.ARGS, "--effect", "dose")  # a second control, from the effect column
        parsed = tomllib.loads(self.text())
        entries = list(parsed["worlds"].values()) + parsed["controls"]
        self.assertGreaterEqual(len(entries), 4)
        for entry in entries:
            self.assertEqual(entry.get("origin"), "suggested", entry)

    def test_rows_exchangeable_only_with_the_flag(self):
        self.suggest(*self.ARGS)
        self.assertNotIn("rows_exchangeable", tomllib.loads(self.text())["data"])
        self.assertRegex(self.text(), r"(?m)^# rows_exchangeable = true")
        other = os.path.join(self.dir, "ex.toml")
        self.suggest(*self.ARGS, "--exchangeable", out=other)
        self.assertIs(tomllib.loads(self.text(other))["data"]["rows_exchangeable"], True)

    def test_the_minus_world_falls_back_to_shuffling_the_effect_columns(self):
        code, out, err = self.suggest("--effect", "dose")
        self.assertEqual(code, 0, err)
        parsed = tomllib.loads(self.text())
        self.assertEqual(parsed["worlds"]["minus"]["mutations"], [{"op": "shuffle", "columns": ["dose"]}])
        self.assertEqual(parsed["data"]["columns"]["dose"]["role"], "effect")
        self.assertEqual(parsed["controls"], [{"id": "effects_negated", "criteria": [], "origin": "suggested",
                                               "mutations": [{"op": "sign_flip", "column": "dose"}]}])
        self.assertIn("alternative minus", self.text())  # the other candidates are comments

    def test_several_effect_columns_give_one_joint_shuffle(self):  # R-22
        code, out, err = self.suggest("--effect", "dose", "yield")
        self.assertEqual(code, 0, err)
        parsed = tomllib.loads(self.text())
        self.assertEqual(parsed["worlds"]["minus"]["mutations"], [{"op": "shuffle", "columns": ["dose", "yield"]}])
        self.assertEqual(parsed["controls"][0]["mutations"],
                         [{"op": "sign_flip", "column": "dose"}, {"op": "sign_flip", "column": "yield"}])
        path = self.write_manifest(self.reviewed(self.text()))  # the joint op is a valid mutation
        with open(path, "rb") as handle:
            spec = parse_manifest(path, handle.read())
        self.assertEqual(spec.worlds["minus"].mutations[0]["columns"], ["dose", "yield"])

    def test_the_joint_shuffle_is_also_the_commented_alternative_with_a_group(self):  # R-22
        with open(self.csv, "w", encoding="utf-8", newline="") as handle:
            handle.write("g,y,d1,d2" + chr(10) + chr(10).join(["a,1.0,1.0,2.0", "b,2.0,2.0,3.0", "a,3.0,3.0,4.0", "b,4.0,4.0,5.0"]) + chr(10))
        code, out, err = self.suggest("--outcome", "y", "--group", "g", "--reference", "a", "--effect", "d1", "d2")
        self.assertEqual(code, 0, err)
        self.assertIn('# alternative minus (replace `mutations`): joint shuffle of the effect columns: '
                      'mutations = [ { op = "shuffle", columns = ["d1", "d2"] } ]', self.text())

    def test_every_pattern_is_a_commented_template_with_column_names_filled_in(self):
        self.suggest(*self.ARGS)
        templates = self.templates(self.text())
        self.assertEqual(len(templates), len(PATTERN_NAMES))
        shown = {re.search(r'pattern = "(\w+)"', "\n".join(lines)).group(1) for lines in templates.values()}
        self.assertEqual(shown, set(PATTERN_NAMES))
        for cid, lines in templates.items():
            joined = "\n".join(lines)
            self.assertIn('origin = "suggested"', joined)
            self.assertIn('"yield"', joined, cid)  # the outcome column is filled in
        self.assertIn('a_where = { column = "group", equals = "treated" }', "\n".join(templates["C_difference"]))
        self.assertIn('b_where = { column = "group", equals = "control" }', "\n".join(templates["C_difference"]))

    def test_every_template_is_valid_once_uncommented(self):
        self.suggest(*self.ARGS, "--effect", "dose")
        base = self.reviewed(self.text())
        for cid, lines in self.templates(self.text()).items():
            with self.subTest(template=cid):
                path = self.write_manifest(base + "\n" + uncomment(lines) + "\n")
                with open(path, "rb") as handle:
                    spec = parse_manifest(path, handle.read())  # a ManifestError would fail the test
                self.assertEqual([c.id for c in spec.criteria], [cid])
                self.assertEqual(spec.criteria[0].origin, "suggested")

    def test_the_data_path_is_relative_to_the_manifest(self):
        sub = os.path.join(self.dir, "sub")
        os.makedirs(sub)
        other = os.path.join(sub, "m.toml")
        self.suggest(*self.ARGS, out=other)
        self.assertEqual(tomllib.loads(self.text(other))["worlds"]["plus"]["file"], "../trial.csv")

    def test_unusual_column_names_are_quoted(self):
        with open(self.csv, "w", encoding="utf-8", newline="") as handle:
            handle.write('my col,"g,1",y\n1.0,a,2.0\n2.0,b,3.0\n3.0,a,4.0\n4.0,b,5.0\n')
        code, out, err = self.suggest("--effect", "my col", "--outcome", "y", "--group", "g,1", "--reference", "a")
        self.assertEqual(code, 0, err)
        parsed = tomllib.loads(self.text())
        self.assertEqual(parsed["data"]["columns"]["my col"], {"type": "float", "role": "effect"})
        self.assertEqual(parsed["data"]["columns"]["g,1"]["role"], "group")

    def test_an_integer_group_column_is_declared_int_with_an_integer_reference(self):
        with open(self.csv, "w", encoding="utf-8", newline="") as handle:
            handle.write("g,y\n0,1.0\n1,2.0\n0,3.0\n1,4.0\n")
        code, out, err = self.suggest("--outcome", "y", "--group", "g", "--reference", "0")
        self.assertEqual(code, 0, err)
        parsed = tomllib.loads(self.text())
        self.assertEqual(parsed["data"]["columns"]["g"], {"type": "int", "role": "group"})
        self.assertEqual(parsed["worlds"]["minus"]["mutations"][0]["reference"], 0)
        path = self.write_manifest(self.reviewed(self.text()))
        with open(path, "rb") as handle:
            parse_manifest(path, handle.read())


class TestStages(SuggestCase):
    """The pre-registered path of section 8: exit 4, then exactly the zero-criteria StudyError (exit 3), then it runs."""

    ARGS = ("--outcome", "yield", "--group", "group", "--reference", "control")

    def test_exit_4_until_provenance_is_set(self):
        self.suggest(*self.ARGS)
        code, out, err, body = self.check(self.out)
        self.assertEqual(code, 4)
        self.assertIn("provenance", err)
        self.assertIsNone(body)
        with open(self.out, "rb") as handle:
            with self.assertRaises(ManifestError):
                parse_manifest(self.out, handle.read())

    def test_then_exactly_the_zero_criteria_study_error(self):
        self.suggest(*self.ARGS)
        path = self.write_manifest(self.reviewed(self.text()))
        code, out, err, body = self.check(path)
        self.assertEqual(code, 3, err)
        self.assertEqual(body["verdict"], "UNDEFINED")
        self.assertEqual(body["load_error"], {"type": "StudyError", "message": "a study needs at least one criterion"})
        self.assertEqual(body["suggested_unreviewed"], 3)  # plus, minus and the control

    def test_runs_once_a_criterion_is_added_and_every_component_is_capped_until_origin_keys_are_deleted(self):
        self.suggest(*self.ARGS, "--exchangeable")
        text = self.reviewed(self.text())
        difference = uncomment(self.templates(text)["C_difference"])
        path = self.write_manifest(text.replace('criteria = []                  # TODO', 'criteria = ["C_difference"]  # TODO')
                                   + "\n" + difference + "\n")
        code, out, err, body = self.check(path)
        self.assertIn(code, (0, 1, 2), err)
        self.assertEqual(body["suggested_unreviewed"], 4)  # plus, minus, the control and the criterion
        for comp in body["components"]:
            self.assertIn("SUGGESTED_UNREVIEWED", comp["flags"])
            self.assertIn(comp["verdict"], ("WEAK", "NOT_FALSIFIABLE"))
        self.assertIn("SUGGESTED_UNREVIEWED", out)
        # a reviewed manifest: delete the origin keys
        cleaned = re.sub(r'(?m)^origin = "suggested"\r?\n', "", read_text(path))
        path2 = self.write_manifest(cleaned, "reviewed.toml")
        code, out, err, body = self.check(path2)
        self.assertEqual(body["suggested_unreviewed"], 0)
        for comp in body["components"]:
            self.assertNotIn("SUGGESTED_UNREVIEWED", comp["flags"])
        self.assertEqual(body["verdict"], "FALSIFIABLE", body["components"])

    def test_the_cap_is_at_most_weak_for_an_otherwise_clean_study(self):
        self.suggest(*self.ARGS)
        text = self.reviewed(self.text())
        text = text.replace('criteria = []                  # TODO', 'criteria = ["C_difference"]  # TODO')
        path = self.write_manifest(text + "\n" + uncomment(self.templates(text)["C_difference"]) + "\n")
        code, out, err, body = self.check(path)
        self.assertEqual(code, 1, out + err)
        self.assertEqual(body["verdict"], "WEAK")
        self.assertEqual(body["components"][0]["flags"], ["SUGGESTED_UNREVIEWED"])


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class TestUsageErrors(SuggestCase):
    def test_exit_4_for_a_bad_call_and_nothing_is_written(self):
        cases = {
            "group without reference": ("--outcome", "yield", "--group", "group"),
            "reference without group": ("--outcome", "yield", "--reference", "control"),
            "group without outcome": ("--group", "group", "--reference", "control"),
            "no candidate": ("--outcome", "yield"),
            "unknown column": ("--effect", "nope"),
            "reference not in the column": ("--outcome", "yield", "--group", "group", "--reference", "ghost"),
            "float group": ("--outcome", "group", "--group", "yield", "--reference", "1"),
            "two roles": ("--outcome", "yield", "--effect", "yield", "--group", "group", "--reference", "control"),
            "text effect": ("--effect", "group"),
        }
        for label, args in cases.items():
            with self.subTest(label):
                code, out, err = self.suggest(*args)
                self.assertEqual(code, 4, label)
                self.assertTrue(err.strip())
                self.assertFalse(os.path.exists(self.out))

    def test_an_existing_output_is_never_overwritten(self):
        with open(self.out, "w", encoding="utf-8") as handle:
            handle.write("keep me")
        code, out, err = self.suggest("--effect", "dose")
        self.assertEqual(code, 4)
        self.assertEqual(self.text(), "keep me")

    def test_missing_or_bad_data_file(self):
        self.assertEqual(run_cli("suggest", os.path.join(self.dir, "none.csv"), "--effect", "x", "--out", self.out)[0], 4)
        bad = os.path.join(self.dir, "bad.csv")
        with open(bad, "w", encoding="utf-8") as handle:
            handle.write("a,b\n1\n")
        self.assertEqual(run_cli("suggest", bad, "--effect", "a", "--out", self.out)[0], 4)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
