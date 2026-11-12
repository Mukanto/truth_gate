"""Post-freeze revisions implemented in stage (c): R-3 (``rate`` selection) and R-9 (``origin``).

See ``docs/design/spec-0.6-REVISIONS-post-freeze.md``.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

import numpy as np

import _helpers  # noqa: F401  (puts the repository root on sys.path)
from truth_gate import cli
from truth_gate.common import ManifestError
from truth_gate.manifest import parse_manifest
from truth_gate.patterns import FAILS, HOLDS, UNDEFINED, Pattern

NAN = float("nan")


def rate(**kw):
    table = {"pattern": "rate", "condition": {"column": "y", "op": ">", "value": 0.0}, "op": ">=", "value": 0.5}
    table.update(kw)
    return table


def ev(table, data, record=None):
    return Pattern(table).evaluate(data, record)


DATA = {
    "y": np.array([1.0, -1.0, 2.0, -2.0, 3.0, 4.0]),
    "g": np.array(["a", "a", "b", "b", "a", "a"]),
    "t": np.array([0, 1, 2, 3, 4, 5]),
    "flag": np.array([True, True, False, False, True, False]),
}


class TestRateSelection(unittest.TestCase):
    """R-3: ``rate`` takes an unprefixed ``where`` / ``index`` over the rows of the condition column."""

    def test_without_a_selection_nothing_changes(self):
        self.assertEqual(ev(rate(value=0.6), DATA), HOLDS)  # 4 of 6 rows are above 0
        self.assertEqual(ev(rate(value=0.7), DATA), FAILS)

    def test_where_equals_selects_rows_of_a_str_column(self):
        # group a: y = 1, -1, 3, 4 -> 3 of 4 above 0
        for value, outcome in ((0.75, HOLDS), (0.76, FAILS)):
            with self.subTest(value=value):
                self.assertEqual(ev(rate(where={"column": "g", "equals": "a"}, value=value), DATA), outcome)
        # group b: y = 2, -2 -> 1 of 2
        record = {}
        ev(rate(where={"column": "g", "equals": "b"}), DATA, record)
        self.assertEqual(record[""][1], {"rate": 0.5})

    def test_where_equals_on_a_bool_column_and_a_numeric_selection(self):
        record = {}
        ev(rate(where={"column": "flag", "equals": True}), DATA, record)  # rows 0, 1, 4: y = 1, -1, 3
        self.assertAlmostEqual(record[""][1]["rate"], 2 / 3)
        record = {}
        ev(rate(where={"column": "t", "op": ">=", "value": 4}), DATA, record)  # rows 4, 5: both above 0
        self.assertEqual(record[""][1], {"rate": 1.0})

    def test_index_keeps_positions(self):
        record = {}
        ev(rate(index=[0, 2, 4, 5]), DATA, record)
        self.assertEqual(record[""][1], {"rate": 1.0})
        record = {}
        ev(rate(index=[1, 3]), DATA, record)
        self.assertEqual(record[""][1], {"rate": 0.0})

    def test_the_selection_applies_to_the_condition_column_only(self):
        # where on one key, the condition on another: the rows are matched by position
        record = {}
        ev(rate(condition={"column": "t", "op": ">", "value": 2}, where={"column": "g", "equals": "b"}), DATA, record)
        self.assertEqual(record[""][1], {"rate": 0.5})  # rows 2, 3: t = 2, 3

    def test_undefined_conditions(self):
        nan_data = {**DATA, "y": np.array([1.0, NAN, 2.0, -2.0, 3.0, 4.0])}
        cases = (
            ("empty where", rate(where={"column": "g", "equals": "zzz"}), DATA),
            ("a string `equals` on a numeric column", rate(where={"column": "t", "equals": "a"}), DATA),
            ("non-finite value", rate(), nan_data),
            ("non-numeric condition column", rate(condition={"column": "g", "op": ">", "value": 0.0}), DATA),
        )
        for name, table, data in cases:
            with self.subTest(name=name):
                self.assertEqual(ev(table, data), UNDEFINED)

    def test_an_index_out_of_range_is_undefined(self):
        """R-32 (audit F4) replaces the earlier behaviour (an IndexError): the leaf itself is UNDEFINED."""
        self.assertEqual(ev(rate(index=[0, 99]), DATA), UNDEFINED)

    def test_a_where_column_of_another_length_is_undefined(self):
        data = {**DATA, "g": np.array(["a", "b"])}
        self.assertEqual(ev(rate(where={"column": "g", "equals": "a"}), data), UNDEFINED)

    def test_a_missing_where_column_raises_before_anything_is_evaluated(self):
        data = {k: v for k, v in DATA.items() if k != "g"}
        with self.assertRaises(KeyError):
            ev(rate(where={"column": "g", "equals": "a"}), data)

    def test_the_where_column_counts_as_a_referenced_key(self):
        pattern = Pattern(rate(where={"column": "g", "equals": "a"}))
        self.assertEqual(pattern.keys, ["y", "g"])
        self.assertEqual(Pattern(rate()).keys, ["y"])

    def test_inside_any_of_a_missing_where_column_still_raises(self):
        table = {"pattern": "any_of", "of": [rate(), rate(where={"column": "nope", "equals": "a"})]}
        with self.assertRaises(KeyError):
            Pattern(table).evaluate(dict(DATA))

    def test_validation(self):
        bad = {
            "both": rate(where={"column": "g", "equals": "a"}, index=[0]),
            "empty index": rate(index=[]),
            "negative index": rate(index=[-1]),
            "float index": rate(index=[1.5]),
            "bool index": rate(index=[True]),
            "where is not a table": rate(where="g"),
            "where has no test": rate(where={"column": "g"}),
            "unknown key": rate(selection=1),
        }
        for name, table in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(ManifestError):
                    Pattern(table)

    def test_thresholds_record_the_selection_only_when_there_is_one(self):
        plain = Pattern(rate()).root.thresholds()
        self.assertNotIn("where", plain)
        self.assertNotIn("index", plain)
        with_where = Pattern(rate(where={"column": "g", "equals": "a"})).root.thresholds()
        self.assertEqual(with_where["where"], {"column": "g", "equals": "a"})
        self.assertEqual(Pattern(rate(index=[0, 1])).root.thresholds()["index"], [0, 1])

    def test_a_rate_with_a_selection_in_a_manifest_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "w.py"), "w", encoding="utf-8") as handle:
                handle.write(
                    "import numpy as np\n"
                    "def plus(rng):\n"
                    "    return {'g': np.array(['a', 'b'] * 20), 'y': np.where(np.arange(40) % 2 == 0, 5.0, -5.0) + rng.normal(0, 1, 40)}\n"
                    "def minus(rng):\n"
                    "    return {'g': np.array(['a', 'b'] * 20), 'y': rng.normal(0, 1, 40)}\n"
                )
            manifest = {
                "study": {"name": "t"}, "data": {"rows": ["g", "y"]},
                "worlds": {"plus": {"python": "w.py:plus"}, "minus": {"python": "w.py:minus", "change": "no signal"}},
                "criteria": [rate(id="C", where={"column": "g", "equals": "a"}, value=0.9, op=">")],
                "controls": [{"id": "neg", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "y"}]}],
            }
            path = os.path.join(tmp, "truthgate.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle)
            out = os.path.join(tmp, "c.json")
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = cli.main(["check", path, "--out", out])
            with open(out, encoding="utf-8") as handle:
                body = json.load(handle)["body"]
        self.assertEqual(code, 0, stdout.getvalue() + stderr.getvalue())
        self.assertEqual(body["components"][0]["counts"]["world:plus"]["holds"], 200)
        part = body["pattern_stats"]["C"]["parts"][""]
        self.assertEqual(part["thresholds"]["where"], {"column": "g", "equals": "a"})


class TestOriginValue(unittest.TestCase):
    """R-9: ``origin`` must equal "suggested"; any other value is a validation error."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_origin_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        with open(os.path.join(self.dir, "w.py"), "w", encoding="utf-8") as handle:
            handle.write("import numpy as np\n"
                         "def plus(rng):\n    return {'x': rng.normal(2.0, 1.0, 20)}\n"
                         "def minus(rng):\n    return {'x': rng.normal(0.0, 1.0, 20)}\n"
                         "def crit(d):\n    return bool(np.mean(d['x']) > 1.0)\n")

    def manifest(self):
        return {
            "study": {"name": "t"},
            "worlds": {"plus": {"python": "w.py:plus"}, "minus": {"python": "w.py:minus", "change": "mean 2 -> 0"}},
            "criteria": [{"id": "C", "python": "w.py:crit"}],
            "controls": [{"id": "neg", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}],
            "premises": [{"id": "p", "role": "assumed", "criteria": ["C"], "mutations": [{"op": "scale", "column": "x", "factor": 2}]}],
            "invariances": [],
        }

    def parse(self, d):
        path = os.path.join(self.dir, "truthgate.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(d, handle)
        with open(path, "rb") as handle:
            return parse_manifest(path, handle.read())

    def places(self, d, value):
        """Every declaration kind that can carry ``origin``."""
        return {
            "worlds.minus": lambda: d["worlds"]["minus"].update(origin=value),
            "criteria[0]": lambda: d["criteria"][0].update(origin=value),
            "controls[0]": lambda: d["controls"][0].update(origin=value),
            "premises[0]": lambda: d["premises"][0].update(origin=value),
        }

    def test_suggested_is_accepted_everywhere(self):
        for where in ("worlds.minus", "criteria[0]", "controls[0]", "premises[0]"):
            with self.subTest(where=where):
                d = self.manifest()
                self.places(d, "suggested")[where]()
                self.assertEqual(self.parse(d).suggested_count, 1)

    def test_any_other_value_is_a_validation_error_naming_the_key(self):
        for value in ("suggest", "Suggested", "reviewed", "", " suggested"):
            for where in ("worlds.minus", "criteria[0]", "controls[0]", "premises[0]"):
                with self.subTest(value=value, where=where):
                    d = self.manifest()
                    self.places(d, value)[where]()
                    with self.assertRaises(ManifestError) as caught:
                        self.parse(d)
                    self.assertIn(where + ".origin", str(caught.exception))
                    self.assertIn('"suggested"', str(caught.exception))

    def test_an_invariance_origin_is_checked_too(self):
        d = self.manifest()
        d["data"] = {"rows": ["x"]}
        d["invariances"] = [{"id": "i", "criteria": ["C"], "reason": "r", "mutations": [{"op": "permute_rows"}],
                             "origin": "yes"}]
        with self.assertRaises(ManifestError) as caught:
            self.parse(d)
        self.assertIn("invariances[0].origin", str(caught.exception))

    def test_a_non_string_origin_is_a_validation_error(self):
        d = self.manifest()
        d["controls"][0]["origin"] = True
        with self.assertRaises(ManifestError):
            self.parse(d)

    def test_the_typo_case_that_motivated_the_revision_exits_4_without_a_certificate(self):
        d = self.manifest()
        d["controls"][0]["origin"] = "suggest"
        path = os.path.join(self.dir, "truthgate.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(d, handle)
        out = os.path.join(self.dir, "c.json")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(["check", path, "--out", out])
        self.assertEqual(code, 4)
        self.assertFalse(os.path.exists(out))
        self.assertIn("origin", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
