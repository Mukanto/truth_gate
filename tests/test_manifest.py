"""Truth_Gate 0.4, stage (b): the manifest (spec 0.6, sections 1.2, 3, 11): parser, validation, data readers, exit codes."""

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

import _helpers
from truth_gate import certificate, cli
from truth_gate.common import ManifestError
from truth_gate.data_io import parse_csv, parse_json, parse_npz, sample_table
from truth_gate.manifest import parse_manifest
from truth_gate.mutations import declaration_rng

MANIFESTS = os.path.join(_helpers.ROOT, "tests", "manifests")

WORLD_PY = '''
import numpy as np


def plus(rng):
    return {"x": rng.normal(2.0, 1.0, 30), "g": np.array(["a", "b"] * 15)}


def minus(rng):
    return {"x": rng.normal(0.0, 1.0, 30), "g": np.array(["a", "b"] * 15)}


def transform(d, rng):
    return {**d, "x": -d["x"]}


def mutate(d, rng):
    return {**d, "x": 0.5 * d["x"]}


def crit(d):
    return bool(np.mean(d["x"]) > 1.0)


def scalar_world(rng):
    return {"s": np.array(1.0)}
'''


def base():
    """A valid manifest as a dict (written as JSON, which has the same structure as TOML)."""
    return {
        "study": {"name": "t"},
        "worlds": {
            "plus": {"python": "w.py:plus"},
            "minus": {"python": "w.py:minus", "change": "mean 2 -> 0"},
        },
        "criteria": [{"id": "C", "pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}],
        "controls": [{"id": "neg", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}],
    }


def parse_file(path):
    with open(path, "rb") as handle:
        return parse_manifest(path, handle.read())


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Workspace(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_manifest_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.write("w.py", WORLD_PY)

    def write(self, name, text, binary=False):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8", "newline": ""})) as handle:
            handle.write(text)
        return path

    def manifest(self, d, name="truthgate.json"):
        return self.write(name, json.dumps(d))

    def parse(self, d):
        path = self.manifest(d)
        with open(path, "rb") as handle:
            return parse_manifest(path, handle.read())

    def check(self, d, *extra):
        path = d if isinstance(d, str) else self.manifest(d)
        out = os.path.join(self.dir, "cert.json")
        code, stdout, stderr = run_cli("check", path, "--out", out, *extra)
        cert = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as handle:
                cert = json.load(handle)
        return code, stdout, stderr, cert

    def assertInvalid(self, d, needle):
        """The manifest is rejected before any certificate: ManifestError naming ``needle``."""
        with self.assertRaises(ManifestError) as caught:
            self.parse(d)
        self.assertIn(needle, str(caught.exception))
        return caught.exception


# ---------------------------------------------------------------------------------------------------------------------
# Data readers (spec 3.3)
# ---------------------------------------------------------------------------------------------------------------------

class TestCsvDialect(unittest.TestCase):
    def read(self, text, declared=None, delimiter=",", encoding="utf-8"):
        raw = text.encode(encoding) if isinstance(text, str) else text
        return parse_csv(raw, "w", declared or {}, delimiter)

    def test_byte_order_mark_is_ignored(self):
        table = self.read("﻿a,b\n1,2\n")
        self.assertEqual(list(table.data), ["a", "b"])

    def test_header_row_is_required(self):
        with self.assertRaisesRegex(ManifestError, "no data rows"):
            self.read("a,b\n")
        with self.assertRaisesRegex(ManifestError, "empty"):
            self.read("")
        with self.assertRaisesRegex(ManifestError, "empty column name"):
            self.read("a,\n1,2\n")
        with self.assertRaisesRegex(ManifestError, "duplicate"):
            self.read("a,a\n1,2\n")

    def test_delimiter_and_decimal_separator(self):
        table = self.read("a;b\n1.5;2\n", delimiter=";")
        np.testing.assert_array_equal(table.data["a"], [1.5])
        table = self.read("a;b\n1,5;2\n", delimiter=";")  # a decimal comma is not a number: the column is a str
        self.assertEqual(table.data["a"].dtype.kind, "U")
        with self.assertRaisesRegex(ManifestError, "not a float"):
            self.read("a;b\n1,5;2\n", {"a": {"type": "float"}}, delimiter=";")
        with self.assertRaisesRegex(ManifestError, "delimiter"):
            self.read("a,b\n1,2\n", delimiter=",,")

    def test_quotes_and_line_endings(self):
        table = self.read('a,b\r\n"x,y",1\r\n"z",2\r\n')
        self.assertEqual(list(table.data["a"]), ["x,y", "z"])

    def test_ragged_rows_and_bad_encoding(self):
        with self.assertRaisesRegex(ManifestError, "data row 3"):
            self.read("a,b\n1,2\n3\n")
        with self.assertRaisesRegex(ManifestError, "UTF-8"):
            self.read(b"a,b\n\xff,1\n")

    def test_missing_values(self):
        table = self.read("a\n1\n\nNA\nNaN\nnan\n2\n")  # R-31: a blank line inside a single-column file is missing
        self.assertEqual(table.n_rows, 6)
        np.testing.assert_array_equal(np.isnan(table.data["a"]), [False, True, True, True, True, False])
        table = self.read("a,b\n,1\nNA,2\n")  # an empty cell is a missing value
        self.assertTrue(np.all(np.isnan(table.data["a"])))

    def test_blank_lines_after_the_last_data_line_are_ignored(self):
        """R-31 (audit F2)."""
        for tail in ("", "\n", "\n\n\n", "\r\n\r\n"):
            with self.subTest(tail=tail):
                self.assertEqual(self.read("a,b\n1,2\n3,4\n" + tail).n_rows, 2)
                self.assertEqual(self.read("a\n1\n2\n" + tail).n_rows, 2)

    def test_a_blank_line_between_data_lines_is_a_missing_value_in_a_single_column_file(self):
        table = self.read("a\n1\n\n3\n\n\n")  # the blank line in the middle counts, the trailing ones do not
        self.assertEqual(table.n_rows, 3)
        np.testing.assert_array_equal(np.isnan(table.data["a"]), [False, True, False])
        string_table = self.read("s\nx\n\ny\n")
        self.assertEqual(list(string_table.data["s"]), ["x", "", "y"])

    def test_a_blank_line_in_a_declared_int_single_column_file_is_a_missing_value_error(self):
        with self.assertRaisesRegex(ManifestError, "missing"):
            self.read("a\n1\n\n3\n", {"a": {"type": "int"}})

    def test_a_blank_line_between_data_lines_is_a_validation_error_with_several_columns(self):
        with self.assertRaisesRegex(ManifestError, "data row 3 is a blank line"):
            self.read("a,b\n1,2\n\n3,4\n")

    def test_a_blank_first_line_and_a_file_of_blank_lines_are_errors(self):
        with self.assertRaisesRegex(ManifestError, "first line is blank"):
            self.read("\na\n1\n")
        with self.assertRaisesRegex(ManifestError, "empty"):
            self.read("\n\n")

    def test_auto_detection(self):
        table = self.read("b,f,s,i,n\ntrue,1.5,x,1,NA\nFALSE,2,y,2,NA\nTrue,NA,z,3,NaN\nfalse,-3e2,w,4,\n")
        self.assertEqual(table.data["b"].dtype, np.dtype(bool))
        self.assertEqual(list(table.data["b"]), [True, False, True, False])
        self.assertEqual(table.data["f"].dtype, np.dtype(np.float64))
        self.assertTrue(np.isnan(table.data["f"][2]))
        self.assertEqual(table.data["f"][3], -300.0)
        self.assertEqual(table.data["s"].dtype.kind, "U")
        self.assertEqual(table.data["i"].dtype, np.dtype(np.float64))  # auto-detection never produces int
        self.assertEqual(table.data["n"].dtype, np.dtype(np.float64))  # an all-missing column is float64

    def test_bool_tokens_are_exactly_the_six_spellings(self):
        table = self.read("b\ntrue\nfalse\nTRUE\nFALSE\nTrue\nFalse\n")
        self.assertEqual(table.data["b"].dtype, np.dtype(bool))
        self.assertEqual(self.read("b\ntrue\nyes\n").data["b"].dtype.kind, "U")
        self.assertEqual(self.read("b\ntrue\n\n1\n").data["b"].dtype.kind, "U")  # a missing cell is not a bool
        self.assertEqual(self.read("b\ntrue\ntRUE\n").data["b"].dtype.kind, "U")

    def test_numbers_are_plain_decimal_numbers(self):
        for text in ("1e3", "-.5", "+2.", "007"):
            with self.subTest(text=text):
                self.assertEqual(self.read(f"a\n{text}\n").data["a"].dtype, np.dtype(np.float64))
        for text in ("inf", "1_000", "0x10", "1 2", " 1"):
            with self.subTest(text=text):
                self.assertEqual(self.read(f"a\n{text}\n").data["a"].dtype.kind, "U")

    def test_declared_types_are_enforced(self):
        decl = {"f": {"type": "float"}, "i": {"type": "int"}, "b": {"type": "bool"}, "s": {"type": "str"}}
        table = self.read("f,i,b,s\n1,2,true,NA\nNA,-3,False,\n", decl)
        self.assertEqual(table.data["f"].dtype, np.dtype(np.float64))
        self.assertTrue(np.isnan(table.data["f"][1]))
        self.assertEqual(table.data["i"].dtype, np.dtype(np.int64))
        self.assertEqual(list(table.data["i"]), [2, -3])
        self.assertEqual(list(table.data["b"]), [True, False])
        self.assertEqual(list(table.data["s"]), ["NA", ""])  # a declared str column keeps its text
        for text, key, message in (("f,i,b,s\nabc,1,true,x\n", "f", "not a float"),
                                   ("f,i,b,s\n1,1.5,true,x\n", "i", "not an integer"),
                                   ("f,i,b,s\n1,,true,x\n", "i", "missing"),
                                   ("f,i,b,s\n1,NA,true,x\n", "i", "missing"),
                                   ("f,i,b,s\n1,1,yes,x\n", "b", "not a bool"),
                                   ("f,i,b,s\n1,1,,x\n", "b", "not a bool"),
                                   ("f,i,b,s\n1,99999999999999999999,true,x\n", "i", "int64")):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ManifestError, message) as caught:
                    self.read(text, decl)
                self.assertIn(f"column {key!r}", str(caught.exception))

    def test_every_column_is_row_aligned(self):
        table = self.read("a,b\n1,2\n3,4\n")
        self.assertEqual(table.row_keys, ("a", "b"))
        self.assertEqual(table.n_rows, 2)


class TestJsonAndNpz(unittest.TestCase):
    def test_json_object_of_arrays(self):
        raw = json.dumps({"x": [1.5, 2.5], "n": [1, 2], "b": [True, False], "s": ["u", "v"], "m": [[1, 2], [3, 4]],
                          "k": 3.0, "f": [1, None]}).encode()
        table = parse_json(raw, "w", {}, ["x", "n"])
        self.assertEqual(table.data["x"].dtype, np.dtype(np.float64))
        self.assertEqual(table.data["n"].dtype, np.dtype(np.int64))
        self.assertEqual(table.data["b"].dtype, np.dtype(bool))
        self.assertEqual(table.data["s"].dtype.kind, "U")
        self.assertEqual(table.data["m"].shape, (2, 2))
        self.assertEqual(table.data["k"].shape, ())
        self.assertTrue(np.isnan(table.data["f"][1]))
        self.assertEqual((table.row_keys, table.n_rows), (("x", "n"), 2))

    def test_json_errors(self):
        for raw, rows, needle in ((b"[1]", [], "object"), (b"{}", [], "object"), (b"nope", [], "JSON"),
                                  (json.dumps({"x": [1, "a"]}).encode(), [], "mixed"),
                                  (json.dumps({"x": [[1], [1, 2]]}).encode(), [], "ragged"),
                                  (json.dumps({"x": [1, 2], "y": [1]}).encode(), ["x", "y"], "first-axis"),
                                  (json.dumps({"x": [1, 2]}).encode(), ["zzz"], "zzz"),
                                  (json.dumps({"x": 1}).encode(), ["x"], "first axis")):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ManifestError, needle):
                    parse_json(raw, "w", {}, rows)

    def test_json_declared_types(self):
        decl = {"a": {"type": "float"}, "b": {"type": "int"}}
        table = parse_json(json.dumps({"a": [1, 2], "b": [1, 2]}).encode(), "w", decl, [])
        self.assertEqual(table.data["a"].dtype, np.dtype(np.float64))
        with self.assertRaisesRegex(ManifestError, "integers"):
            parse_json(json.dumps({"b": [1.5]}).encode(), "w", decl, [])
        with self.assertRaisesRegex(ManifestError, "float"):
            parse_json(json.dumps({"a": ["x"]}).encode(), "w", decl, [])

    def npz(self, **arrays):
        buffer = io.BytesIO()
        np.savez(buffer, **arrays)
        return buffer.getvalue()

    def test_npz(self):
        raw = self.npz(x=np.arange(3.0), n=np.arange(3), s=np.array(["a", "b", "c"]), k=np.array(2.0))
        table = parse_npz(raw, "w", {}, ["x", "n"])
        self.assertEqual(table.data["n"].dtype.kind, "i")
        self.assertEqual((table.row_keys, table.n_rows), (("x", "n"), 3))
        table = parse_npz(raw, "w", {"n": {"type": "float"}}, [])
        self.assertEqual(table.data["n"].dtype, np.dtype(np.float64))
        for bad_raw, decl, rows, needle in (
                (b"not an archive", {}, [], "NPZ"),
                (raw, {"x": {"type": "int"}}, [], "does not fit"),
                (raw, {"s": {"type": "float"}}, [], "does not fit"),
                (self.npz(c=np.array([1 + 2j])), {}, [], "unsupported"),
                (raw, {}, ["x", "k"], "first axis")):
            with self.subTest(needle=needle):
                with self.assertRaisesRegex(ManifestError, needle):
                    parse_npz(bad_raw, "w", decl, rows)


class TestSampling(unittest.TestCase):
    def table(self):
        return parse_csv(b"a,b\n1,x\n2,y\n3,z\n4,w\n5,v\n6,u\n", "w", {}, ",")

    def test_bootstrap_is_n_rows_with_replacement_with_one_index_for_all_keys(self):
        table = self.table()
        out = sample_table(table, np.random.default_rng(2), "bootstrap", None)
        self.assertEqual(out["a"].shape, (6,))
        idx = np.random.default_rng(2).integers(0, 6, size=6)
        np.testing.assert_array_equal(out["a"], table.data["a"][idx])
        np.testing.assert_array_equal(out["b"], table.data["b"][idx])  # the same rows in every column

    def test_subsample_is_round_fraction_n_rows_without_replacement(self):
        out = sample_table(self.table(), np.random.default_rng(3), "subsample", 0.5)
        self.assertEqual(out["a"].shape, (3,))
        self.assertEqual(len(set(out["a"])), 3)
        self.assertEqual(sample_table(self.table(), np.random.default_rng(3), "subsample", 0.34)["a"].shape, (round(0.34 * 6),))

    def test_none_is_the_table_itself_and_never_aliases(self):
        table = self.table()
        out = sample_table(table, np.random.default_rng(0), "none", None)
        np.testing.assert_array_equal(out["a"], table.data["a"])
        out["a"][0] = 99.0
        self.assertEqual(table.data["a"][0], 1.0)

    def test_keys_that_are_not_row_aligned_are_copied_unchanged(self):
        raw = json.dumps({"x": [1.0, 2.0, 3.0], "tag": [7.0]}).encode()
        table = parse_json(raw, "w", {}, ["x"])
        out = sample_table(table, np.random.default_rng(0), "bootstrap", None)
        np.testing.assert_array_equal(out["tag"], [7.0])
        self.assertEqual(out["x"].shape, (3,))


# ---------------------------------------------------------------------------------------------------------------------
# Parser and validation errors (exit 4)
# ---------------------------------------------------------------------------------------------------------------------

class TestParse(Workspace):
    def test_base_manifest_parses(self):
        m = self.parse(base())
        self.assertEqual(m.name, "t")
        self.assertEqual(sorted(m.worlds), ["minus", "plus"])
        self.assertEqual(m.suggested_count, 0)

    def test_unknown_keys_are_named(self):
        cases = [
            (lambda d: d.update(zzz={}), "zzz"),
            (lambda d: d["study"].update(zzz=1), "study.zzz"),
            (lambda d: d.update(data={"zzz": 1}), "data.zzz"),
            (lambda d: d.update(data={"columns": {"a": {"type": "str", "zzz": 1}}}), "data.columns.a.zzz"),
            (lambda d: d["worlds"]["plus"].update(zzz=1), "worlds.plus.zzz"),
            (lambda d: d["criteria"][0].update(zzz=1), "criteria[0].zzz"),
            (lambda d: d["controls"][0].update(zzz=1), "controls[0].zzz"),
            (lambda d: d.update(premises=[{"id": "p", "role": "tested", "criteria": ["C"],
                                           "mutations": [{"op": "sign_flip", "column": "x"}], "zzz": 1}]), "premises[0].zzz"),
            (lambda d: d.update(budget={"zzz": 1}), "budget.zzz"),
            (lambda d: d.update(targets={"zzz": 1}), "targets.zzz"),
            (lambda d: d.update(external={"zzz": 1}), "external.zzz"),
            (lambda d: d.update(invariances=[{"id": "i", "criteria": ["C"], "reason": "r",
                                              "mutations": [{"op": "permute_rows"}], "zzz": 1}]), "invariances[0].zzz"),
            (lambda d: d["controls"][0]["mutations"][0].update(zzz=1), "controls[0].mutations[0].zzz"),
        ]
        for edit, needle in cases:
            with self.subTest(needle=needle):
                d = base()
                edit(d)
                self.assertInvalid(d, needle)

    def test_type_errors_name_the_key(self):
        cases = [
            (lambda d: d["study"].update(name=5), "study.name"),
            (lambda d: d["study"].update(deterministic="yes"), "study.deterministic"),
            (lambda d: d["study"].update(regimes="all"), "study.regimes"),
            (lambda d: d["study"].update(relational=[["a"]]), "study.relational[0]"),
            (lambda d: d.update(budget={"samples": 2.5}), "budget.samples"),
            (lambda d: d.update(budget={"samples": True}), "budget.samples"),
            (lambda d: d.update(targets={"power": "high"}), "targets.power"),
            (lambda d: d.update(criteria={}), "criteria"),
            (lambda d: d["criteria"][0].update(id=3), "criteria[0].id"),
            (lambda d: d["criteria"][0].update(tolerances={"t": [1.0]}), "criteria[0].tolerances.t"),
            (lambda d: d["criteria"][0].update(tolerances=[1.0, 2.0]), "criteria[0].tolerances"),
            (lambda d: d["criteria"][0].update(regime=1), "criteria[0].regime"),
            (lambda d: d["controls"][0].update(criteria="C"), "controls[0].criteria"),
            (lambda d: d.update(data={"rows": "x"}), "data.rows"),
            (lambda d: d.update(data={"rows_exchangeable": "yes"}), "data.rows_exchangeable"),
        ]
        for edit, needle in cases:
            with self.subTest(needle=needle):
                d = base()
                edit(d)
                self.assertInvalid(d, needle)

    def test_missing_study_table_and_name(self):
        d = base()
        del d["study"]
        self.assertInvalid(d, "study")
        d = base()
        del d["study"]["name"]
        self.assertInvalid(d, "study.name")

    def test_syntax_errors(self):
        for name, text, needle in (("a.toml", "[study\nname = 1", "TOML"), ("b.json", "{nope", "JSON"),
                                   ("c.json", "[1, 2]", "table")):
            with self.subTest(name=name):
                path = self.write(name, text)
                with self.assertRaisesRegex(ManifestError, needle):
                    parse_file(path)
        path = self.write("d.json", b"\xff\xfe", binary=True)
        with self.assertRaisesRegex(ManifestError, "UTF-8"):
            parse_file(path)

    def test_datetimes_and_non_finite_numbers_are_errors_in_toml_and_json(self):
        toml_base = '[study]\nname = "t"\n[worlds.plus]\npython = "w.py:plus"\n[worlds.minus]\npython = "w.py:minus"\nchange = "c"\n'
        extra_toml = {
            "datetime": '[[criteria]]\nid = "C"\npattern = "threshold"\nx = "x"\nstat = "mean"\nop = ">"\nvalue = 1979-05-27T07:32:00Z\n',
            "date": '[[criteria]]\nid = "C"\npattern = "threshold"\nx = "x"\nstat = "mean"\nop = ">"\nvalue = 1979-05-27\n',
            "inf": '[[criteria]]\nid = "C"\npattern = "threshold"\nx = "x"\nstat = "mean"\nop = ">"\nvalue = inf\n',
            "nan": '[[criteria]]\nid = "C"\npattern = "threshold"\nx = "x"\nstat = "mean"\nop = ">"\nvalue = nan\n',
            "in a list": '[[criteria]]\nid = "C"\npattern = "largest_true"\ngrid = [1.0, inf]\ny = "x"\nop = ">"\nthreshold = 1\n'
                         'compare_to = { value = 1 }\ncmp = "=="\n',
        }
        for name, extra in extra_toml.items():
            with self.subTest(name=name):
                path = self.write("t.toml", toml_base + extra)
                with self.assertRaises(ManifestError) as caught:
                    parse_file(path)
                self.assertRegex(str(caught.exception), r"criteria\[0\]")
        d = json.dumps(base()).replace('"value": 1.0', '"value": NaN')  # Python's json accepts the NaN literal
        path = self.write("n.json", d)
        with self.assertRaisesRegex(ManifestError, "non-finite"):
            parse_file(path)

    def test_world_rules(self):
        def with_world(**kw):
            d = base()
            d["worlds"]["extra"] = kw
            return d

        self.assertInvalid(with_world(), "worlds.extra")  # no source
        self.assertInvalid(with_world(python="w.py:plus", derive="plus", mutations=[{"op": "permute_rows"}]), "exactly one")
        self.assertInvalid(with_world(derive="ghost", mutations=[{"op": "sign_flip", "column": "x"}]), "unknown world 'ghost'")
        self.assertInvalid(with_world(derive="plus"), "worlds.extra.mutations")
        self.assertInvalid(with_world(python="w.py:plus", mutations=[{"op": "sign_flip", "column": "x"}]), "mutations")
        self.assertInvalid(with_world(python="w.py:plus", provenance="p"), "provenance")
        self.assertInvalid(with_world(python="w.py:plus", resample="none"), "resample")
        d = base()
        del d["worlds"]["minus"]["change"]
        self.assertInvalid(d, "worlds.minus.change")

    def test_derivation_cycles(self):
        m = [{"op": "sign_flip", "column": "x"}]
        d = base()
        d["worlds"].update(a={"derive": "b", "mutations": m}, b={"derive": "a", "mutations": m})
        self.assertInvalid(d, "cycle")
        d = base()
        d["worlds"].update(a={"derive": "a", "mutations": m})
        self.assertInvalid(d, "cycle")
        d = base()
        d["worlds"].update(a={"derive": "b", "mutations": m}, b={"derive": "c", "mutations": m},
                           c={"derive": "a", "mutations": m})
        self.assertInvalid(d, "cycle")

    def test_python_references(self):
        for ref, needle in (("w.py", "file.py:function"), ("w.py:", "file.py:function"), ("w.py:not an id", "function"),
                            ("missing.py:plus", "not found"), (3, "string")):
            with self.subTest(ref=ref):
                d = base()
                d["worlds"]["plus"]["python"] = ref
                self.assertInvalid(d, "worlds.plus.python")
        m = self.parse(base())
        self.assertEqual(len(m.python_files), 1)

    def test_row_operations_need_row_aligned_keys(self):
        d = base()
        d["controls"][0]["mutations"] = [{"op": "shuffle", "column": "x"}]
        self.assertInvalid(d, "row operation")
        d["data"] = {"rows": ["x", "g"]}
        self.parse(d)  # fine once the row-aligned keys are declared
        for op in ({"op": "subsample", "fraction": 0.5}, {"op": "permute_rows"},
                   {"op": "null_effect", "outcome": "x", "group": "g", "reference": "a"}):
            with self.subTest(op=op["op"]):
                d = base()
                d["worlds"]["derived"] = {"derive": "plus", "mutations": [op]}
                self.assertInvalid(d, "worlds.derived.mutations")
                d["data"] = {"rows": ["x", "g"]}
                self.parse(d)
        d = base()
        d["premises"] = [{"id": "p", "role": "tested", "criteria": ["C"], "mutations": [{"op": "permute_rows"}]}]
        self.assertInvalid(d, "premises[0].mutations")

    def test_criteria_rules(self):
        d = base()
        d["criteria"][0]["command"] = ["prog"]
        self.assertInvalid(d, "criteria[0]")  # two kinds
        d = base()
        del d["criteria"][0]["pattern"]
        self.assertInvalid(d, "exactly one")
        d = base()
        d["criteria"][0]["components"] = ["a"]
        self.assertInvalid(d, "criteria[0].components")
        d = base()
        d["criteria"][0] = {"id": "C", "python": "w.py:crit", "x": "x"}
        self.assertInvalid(d, "criteria[0].x")
        d = base()
        d["criteria"][0] = {"id": "C", "command": []}
        self.assertInvalid(d, "criteria[0].command")
        d["criteria"][0] = {"id": "C", "command": [""]}
        self.assertInvalid(d, "criteria[0].command")
        d["criteria"][0] = {"id": "C", "pattern": "threshold", "x": "x", "stat": "mean", "op": ">"}
        self.assertInvalid(d, "criteria[0].value")

    def test_python_criterion_accepts_components_and_regime(self):
        d = base()
        d["study"]["regimes"] = ["all", "r2"]
        d["criteria"][0] = {"id": "C", "python": "w.py:crit", "components": ["a", "b"], "regime": "r2",
                            "control_waiver": "reason", "tolerances": {"t": [0.5, 1.0]}}
        m = self.parse(d)
        self.assertEqual(m.criteria[0].components, ["a", "b"])
        self.assertEqual(m.criteria[0].tolerances, {"t": (0.5, 1.0)})

    def test_control_and_premise_rules(self):
        d = base()
        d["controls"][0]["python"] = "w.py:transform"
        self.assertInvalid(d, "controls[0]")
        d = base()
        d["controls"][0] = {"id": "c", "criteria": ["C"]}
        self.assertInvalid(d, "exactly one")
        d = base()
        d["controls"][0] = {"id": "c", "criteria": ["C"], "world": "ghost"}
        self.assertInvalid(d, "controls[0].world")
        d["controls"][0] = {"id": "c", "criteria": ["C"], "world": "minus"}
        self.parse(d)
        d["controls"][0] = {"id": "c", "criteria": ["C"], "python": "w.py:transform"}
        self.parse(d)
        d = base()
        prem = {"id": "p", "role": "tested", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}
        d["premises"] = [{**prem, "python": "w.py:mutate"}]
        self.assertInvalid(d, "premises[0]")
        d["premises"] = [{**prem, "magnitude": [1.0]}]
        self.assertInvalid(d, "premises[0].magnitude")
        d["premises"] = [{**prem, "magnitude": [0.5, 1.0]}]
        self.assertEqual(self.parse(d).premises[0].magnitude, (0.5, 1.0))
        d["premises"] = [{k: v for k, v in prem.items() if k != "role"}]
        self.assertInvalid(d, "premises[0].role")

    def test_data_columns_and_external_validation(self):
        d = base()
        d["data"] = {"columns": {"a": {"type": "complex"}}}
        self.assertInvalid(d, "data.columns.a.type")
        d["data"] = {"columns": {"a": {"type": "str", "role": "boss"}}}
        self.assertInvalid(d, "data.columns.a.role")
        d["data"] = {"columns": {"a": {"role": "id"}}}
        self.assertInvalid(d, "data.columns.a.type")
        d["data"] = {"columns": {"a": {"type": "float", "role": "outcome"}, "b": {"type": "int"}}}
        self.parse(d)
        d = base()
        d["external"] = {"uses": ["nope.txt"]}
        self.assertInvalid(d, "external.uses[0]")
        d["external"] = {"startup_timeout_s": -1}
        self.assertInvalid(d, "external.startup_timeout_s")
        d["external"] = {"uses": ["w.py"], "env": ["HOME"], "startup_timeout_s": 5, "request_timeout_s": 2.5}
        self.parse(d)
        d = base()
        d["study"]["allow_paths"] = ["nope.txt"]
        self.assertInvalid(d, "study.allow_paths[0]")

    def test_invariance_validation(self):
        inv = {"id": "i", "criteria": ["C"], "reason": "row order is irrelevant", "mutations": [{"op": "permute_rows"}]}
        d = base()
        d["data"] = {"rows": ["x"]}
        d["invariances"] = [{k: v for k, v in inv.items() if k != "reason"}]
        self.assertInvalid(d, "invariances[0].reason")
        d["invariances"] = [{**inv, "reason": "  "}]
        self.assertInvalid(d, "invariances[0].reason")
        d["invariances"] = [{**inv, "mutations": []}]
        self.assertInvalid(d, "invariances[0].mutations")
        d["data"] = {}
        d["invariances"] = [inv]
        self.assertInvalid(d, "invariances[0].mutations")  # no row-aligned keys

    def test_file_world_rules(self):
        self.write("d.csv", "x,g\n1.0,a\n2.0,b\n3.0,a\n4.0,b\n")

        def with_file(**kw):
            d = base()
            d["worlds"]["plus"] = {"file": "d.csv", "provenance": "synthetic", **kw}
            return d

        self.parse(with_file())
        self.assertInvalid(with_file(provenance=""), "worlds.plus.provenance")
        self.assertInvalid(with_file(provenance="TODO"), "worlds.plus.provenance")
        d = with_file()
        del d["worlds"]["plus"]["provenance"]
        self.assertInvalid(d, "worlds.plus.provenance")
        self.assertInvalid(with_file(file="missing.csv"), "worlds.plus.file")
        self.write("d.txt", "x,y")
        self.assertInvalid(with_file(file="d.txt"), "data files must be")
        self.assertInvalid(with_file(resample="sideways"), "worlds.plus.resample")
        self.assertInvalid(with_file(resample="none"), "worlds.plus.resample")  # only for deterministic studies
        self.assertInvalid(with_file(resample="subsample"), "worlds.plus.fraction")
        self.assertInvalid(with_file(resample="subsample", fraction=1.0), "worlds.plus.fraction")
        self.assertInvalid(with_file(resample="subsample", fraction=0.0), "worlds.plus.fraction")
        self.assertInvalid(with_file(fraction=0.5), "worlds.plus.fraction")
        self.assertEqual(self.parse(with_file(resample="subsample", fraction=0.5)).worlds["plus"].fraction, 0.5)
        self.assertInvalid(with_file(delimiter="ab"), "single character")
        d = with_file()
        d["study"]["deterministic"] = True
        self.assertEqual(self.parse(d).worlds["plus"].resample, "none")
        d["worlds"]["plus"]["resample"] = "bootstrap"
        self.assertInvalid(d, "worlds.plus.resample")
        d["worlds"]["plus"] = {"file": "d.csv", "provenance": "synthetic", "resample": "none", "fraction": 0.5}
        self.assertInvalid(d, "worlds.plus.fraction")
        d = with_file()
        d["data"] = {"columns": {"ghost": {"type": "float"}}}
        self.assertInvalid(d, "ghost")  # a declared column that is not in the file
        d["data"] = {"columns": {"x": {"type": "int"}}}
        self.assertInvalid(d, "column 'x'")  # 1.0 is not an integer

    def test_json_and_npz_worlds_need_row_keys_to_be_resampled(self):
        self.write("d.json", json.dumps({"x": [1.0, 2.0, 3.0], "g": ["a", "b", "a"]}))
        d = base()
        d["worlds"]["plus"] = {"file": "d.json", "provenance": "synthetic"}
        self.assertInvalid(d, "row-aligned keys")
        d["data"] = {"rows": ["x", "g"]}
        self.assertEqual(self.parse(d).worlds["plus"].row_keys, ("x", "g"))
        d["worlds"]["plus"]["delimiter"] = ";"
        self.assertInvalid(d, "delimiter")

    def test_invariances_and_rows_exchangeable_are_executed_by_stage_d(self):
        # Stage (d) implemented K8 (tests/test_k8.py); the keys parse and run instead of stopping with exit 4.
        d2 = base()
        d2["data"] = {"rows": ["x"]}
        d2["invariances"] = [{"id": "i", "criteria": ["C"], "reason": "r", "mutations": [{"op": "permute_rows"}]}]
        d3 = base()
        d3["data"] = {"rows_exchangeable": True, "rows": ["x"]}
        for key, manifest in (("invariances", d2), ("data.rows_exchangeable", d3)):
            with self.subTest(key=key):
                self.assertTrue(self.parse(manifest))
                code, out, err, cert = self.check(manifest)
                self.assertIn(code, (0, 1, 2), err)
                self.assertIsNotNone(cert)

    def test_validation_errors_are_manifest_errors(self):
        d = base()
        d["criteria"][0] = {"id": "C", "command": ["node"], "zzz": 1}
        with self.assertRaises(ManifestError) as caught:
            self.parse(d)
        self.assertIn("zzz", str(caught.exception))


# ---------------------------------------------------------------------------------------------------------------------
# The exit 4 / exit 3 boundary (spec 1.2)
# ---------------------------------------------------------------------------------------------------------------------

class TestExitCodeBoundary(Workspace):
    def test_manifest_errors_exit_4_without_a_certificate(self):
        d = base()
        d["worlds"]["plus"]["zzz"] = 1
        code, out, err, cert = self.check(d)
        self.assertEqual(code, 4)
        self.assertIsNone(cert)
        self.assertIn("worlds.plus.zzz", err)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "truthgate.kapi.json")))

    def test_study_errors_exit_3_with_an_undefined_certificate(self):
        def no_criteria(d):
            d["criteria"] = []
            d["controls"] = []

        def duplicate_ids(d):
            d["criteria"].append(copy.deepcopy(d["criteria"][0]))

        def unknown_criterion(d):
            d["controls"][0]["criteria"] = ["ghost"]

        def no_plus(d):
            del d["worlds"]["plus"]
            d["worlds"]["minus"] = {"python": "w.py:minus", "change": "c"}

        def no_minus(d):
            del d["worlds"]["minus"]

        def zero_samples(d):
            d["budget"] = {"samples": 0}

        def bad_role(d):
            d["premises"] = [{"id": "p", "role": "bogus", "criteria": ["C"],
                              "mutations": [{"op": "sign_flip", "column": "x"}]}]

        def empty_name(d):
            d["study"]["name"] = ""

        def duplicate_control(d):
            d["controls"].append(copy.deepcopy(d["controls"][0]))

        def duplicate_premise(d):
            prem = {"id": "p", "role": "tested", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}
            d["premises"] = [prem, copy.deepcopy(prem)]

        def undeclared_regime(d):
            d["criteria"][0]["regime"] = "nowhere"

        for edit in (no_criteria, duplicate_ids, unknown_criterion, no_plus, no_minus, zero_samples, bad_role, empty_name,
                     duplicate_control, duplicate_premise, undeclared_regime):
            with self.subTest(edit=edit.__name__):
                d = base()
                edit(d)
                code, out, err, cert = self.check(d)
                self.assertEqual(code, 3, err)
                self.assertEqual(cert["body"]["verdict"], "UNDEFINED")
                self.assertEqual(cert["body"]["input_kind"], "manifest")
                self.assertEqual(cert["body"]["load_error"]["type"], "StudyError")
                self.assertIn("message", cert["body"]["load_error"])
                self.assertEqual(cert["body"]["components"], [])
                self.assertIn("manifest", cert["body"])
                self.assertEqual(certificate.validate_envelope(cert), [])

    def test_errors_while_loading_python_references_exit_3(self):
        self.write("boom.py", "raise RuntimeError('at import')\n")
        d = base()
        d["worlds"]["plus"]["python"] = "boom.py:plus"
        code, out, err, cert = self.check(d)
        self.assertEqual(code, 3)
        self.assertEqual(cert["body"]["load_error"], {"type": "RuntimeError"})  # no message for other exceptions
        d = base()
        d["worlds"]["plus"]["python"] = "w.py:nothing_here"
        code, out, err, cert = self.check(d)
        self.assertEqual(code, 3)
        self.assertEqual(cert["body"]["load_error"]["type"], "StudyError")
        self.assertIn("nothing_here", cert["body"]["load_error"]["message"])
        self.write("notfn.py", "plus = 3\n")
        d["worlds"]["plus"]["python"] = "notfn.py:plus"
        self.assertEqual(self.check(d)[0], 3)

    def test_missing_manifest_file_is_a_usage_error(self):
        code, out, err = run_cli("check", os.path.join(self.dir, "nope.toml"))
        self.assertEqual(code, 4)

    def test_verify_of_a_manifest_with_a_manifest_error_exits_4(self):
        good = self.manifest(base(), "good.json")
        out = os.path.join(self.dir, "c.json")
        self.assertEqual(run_cli("check", good, "--out", out)[0], 0)
        bad = base()
        bad["zzz"] = 1
        code, stdout, stderr = run_cli("verify", out, self.manifest(bad, "bad.json"))
        self.assertEqual(code, 4)
        self.assertIn("zzz", stderr)


# ---------------------------------------------------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------------------------------------------------

class TestSectionThreePointOneExample(Workspace):
    """The group-difference example of spec section 3.1 (its CSV is synthetic, under tests/manifests/)."""

    def test_the_example_as_written_runs_end_to_end_with_k8(self):
        # Stage (d): rows_exchangeable = true adds the built-in permute_rows invariance (K8); the example is FALSIFIABLE.
        out_path = os.path.join(self.dir, "x.json")
        code, out, err = run_cli("check", os.path.join(MANIFESTS, "trial_example.toml"), "--out", out_path)
        self.assertEqual(code, 0, out + err)
        with open(out_path, encoding="utf-8") as handle:
            body = json.load(handle)["body"]
        self.assertEqual(body["verdict"], "FALSIFIABLE")
        self.assertEqual(body["m_k8"], 2)
        self.assertEqual(sorted(body["k8"]), ["builtin:permute_rows"])
        self.assertEqual(body["mutations"]["invariances"], [{"id": "builtin:permute_rows", "ops": ["permute_rows"]}])

    def test_the_example_runs_end_to_end_without_the_exchangeability_line(self):
        out_path = os.path.join(self.dir, "trial.json")
        code, stdout, err = run_cli("check", os.path.join(MANIFESTS, "trial_run.toml"), "--out", out_path)
        self.assertEqual(code, 0, stdout + err)
        self.assertIn("C1", stdout)
        self.assertIn("FALSIFIABLE", stdout)
        with open(out_path, encoding="utf-8") as handle:
            envelope = json.load(handle)
        body = envelope["body"]
        self.assertEqual(certificate.validate_envelope(envelope), [])
        self.assertEqual(body["verdict"], "FALSIFIABLE")
        self.assertEqual(body["input_kind"], "manifest")
        self.assertEqual(body["tool"], "truth-gate")
        self.assertEqual(body["leak_log"], [])
        self.assertEqual(body["suggested_unreviewed"], 0)
        self.assertEqual(body["study_notes"], [])
        counts = body["components"][0]["counts"]
        self.assertEqual(counts["world:plus"]["holds"], 200)
        self.assertEqual(counts["world:minus"]["holds"], 0)
        self.assertEqual(body["study"]["worlds"]["minus"]["derived_from"], "plus")
        self.assertEqual(body["study"]["worlds"]["minus"]["change"], "no effect: treated yields are drawn from control plots")
        # the manifest field (spec 11)
        with open(os.path.join(MANIFESTS, "trial_run.toml"), "rb") as handle:
            manifest_bytes = handle.read()
        with open(os.path.join(MANIFESTS, "synthetic_trial.csv"), "rb") as handle:
            csv_bytes = handle.read()
        rec = body["manifest"]
        self.assertEqual(rec["sha256"], hashlib.sha256(manifest_bytes).hexdigest())
        self.assertEqual(body["study"]["module_sha256"], rec["sha256"])
        self.assertEqual(rec["data_files"], [{"path": "synthetic_trial.csv", "sha256": hashlib.sha256(csv_bytes).hexdigest()}])
        self.assertEqual(rec["provenance"], {"plus": "simulated from last season's control plots plus a 0.8 t/ha effect"})
        self.assertEqual(rec["parsed"]["criteria"][0]["pattern"], "difference")
        self.assertEqual(rec["python_files"], [])
        self.assertEqual(body["mutations"], {
            "worlds": [{"id": "minus", "ops": ["null_effect"]}],
            "controls": [{"id": "labels_shuffled", "ops": ["shuffle"]}], "premises": [], "invariances": [],
        })
        self.assertEqual(sorted(body["pattern_stats"]), ["C1"])

    def test_the_certificate_verifies_and_is_reproducible(self):
        out_path = os.path.join(self.dir, "trial.json")
        manifest = os.path.join(MANIFESTS, "trial_run.toml")
        self.assertEqual(run_cli("check", manifest, "--out", out_path)[0], 0)
        code, stdout, err = run_cli("verify", out_path, manifest)
        self.assertEqual(code, 0, stdout + err)
        self.assertIn("OK", stdout)

    def test_quick_mode_uses_the_quick_budget(self):
        out_path = os.path.join(self.dir, "quick.json")
        code, stdout, err = run_cli("check", os.path.join(MANIFESTS, "trial_run.toml"), "--out", out_path, "--quick")
        with open(out_path, encoding="utf-8") as handle:
            body = json.load(handle)["body"]
        self.assertEqual(body["mode"], "quick")
        self.assertEqual(body["components"][0]["counts"]["world:plus"]["n"], 20)

    def test_the_same_manifest_as_json_gives_the_same_study(self):
        import tomllib
        with open(os.path.join(MANIFESTS, "trial_run.toml"), "rb") as handle:
            parsed = tomllib.load(handle)
        shutil.copy(os.path.join(MANIFESTS, "synthetic_trial.csv"), self.dir)
        path = self.write("trial.json", json.dumps(parsed))
        code, stdout, err, cert = self.check(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(cert["body"]["components"][0]["counts"]["world:plus"]["holds"], 200)

    def test_a_sample_run_from_another_working_directory(self):
        # paths are relative to the manifest's folder, not to the working directory
        previous = os.getcwd()
        os.chdir(self.dir)
        try:
            code, stdout, err = run_cli("check", os.path.join(MANIFESTS, "trial_run.toml"), "--out",
                                        os.path.join(self.dir, "c.json"))
        finally:
            os.chdir(previous)
        self.assertEqual(code, 0, stdout + err)


class TestSuggestedUnreviewed(Workspace):
    def test_origin_caps_every_component_at_weak(self):
        d = base()
        code, out, err, cert = self.check(d)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(cert["body"]["suggested_unreviewed"], 0)
        self.assertNotIn("SUGGESTED_UNREVIEWED", cert["body"]["components"][0]["flags"])
        d["controls"][0]["origin"] = "suggested"
        code, out, err, cert = self.check(d)
        body = cert["body"]
        self.assertEqual(code, 1, out + err)  # WEAK
        self.assertEqual(body["verdict"], "WEAK")
        self.assertEqual(body["suggested_unreviewed"], 1)
        self.assertEqual(body["components"][0]["verdict"], "WEAK")
        self.assertIn("SUGGESTED_UNREVIEWED", body["components"][0]["flags"])
        self.assertIn("SUGGESTED_UNREVIEWED", out)

    def test_count_covers_every_declaration_kind_and_the_flag_is_on_every_component(self):
        d = base()
        d["criteria"].append({"id": "C2", "pattern": "threshold", "x": "x", "stat": "max", "op": ">", "value": 1.0,
                              "origin": "suggested"})
        d["controls"][0]["criteria"] = ["C", "C2"]
        d["worlds"]["minus"]["origin"] = "suggested"
        d["premises"] = [{"id": "p", "role": "assumed", "criteria": ["C"], "origin": "suggested",
                          "mutations": [{"op": "scale", "column": "x", "factor": 0.5}]}]
        code, out, err, cert = self.check(d)
        self.assertEqual(cert["body"]["suggested_unreviewed"], 3)
        for comp in cert["body"]["components"]:
            self.assertIn("SUGGESTED_UNREVIEWED", comp["flags"])

    def test_it_never_hides_a_worse_verdict(self):
        d = base()
        d["controls"][0]["origin"] = "suggested"
        d["worlds"]["plus"] = {"python": "w.py:minus"}  # plus never holds: the criterion is not falsifiable
        code, out, err, cert = self.check(d)
        self.assertEqual(cert["body"]["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(code, 2)

    def test_the_flag_class_is_capping_and_not_mandatory(self):
        from truth_gate import checks
        self.assertTrue(checks.is_capping("SUGGESTED_UNREVIEWED"))
        self.assertFalse(checks.is_mandatory("SUGGESTED_UNREVIEWED"))
        self.assertEqual(checks.component_verdict(["SUGGESTED_UNREVIEWED"]), "WEAK")
        self.assertEqual(checks.component_verdict(["K2_MINUS_IDENTICAL", "SUGGESTED_UNREVIEWED"]), "UNTESTED")
        self.assertEqual(checks.component_verdict(["K1_UNDEFINED", "SUGGESTED_UNREVIEWED"]), "UNDEFINED")
        self.assertEqual(len(checks.CAPPING_FLAGS), 4)  # the 0.3 set is untouched


class TestPythonReferencesAndGuard(Workspace):
    def test_python_files_are_hashed_and_allow_listed(self):
        d = base()
        d["controls"][0] = {"id": "neg", "criteria": ["C"], "python": "w.py:transform"}
        d["premises"] = [{"id": "p", "role": "assumed", "criteria": ["C"], "python": "w.py:mutate"}]
        code, out, err, cert = self.check(d)
        self.assertIn(code, (0, 1), out + err)
        files = cert["body"]["manifest"]["python_files"]
        with open(os.path.join(self.dir, "w.py"), "rb") as handle:
            self.assertEqual(files, [{"path": "w.py", "sha256": hashlib.sha256(handle.read()).hexdigest()}])
        self.assertEqual(cert["body"]["leak_log"], [])
        self.assertEqual(cert["body"]["mutations"]["controls"], [])  # python transforms have no listed ops

    def test_the_guard_is_armed_for_referenced_files_and_for_the_passes(self):
        self.write("secret.txt", "data")
        self.write("leaky.py", (
            "import numpy as np\n\n\ndef plus(rng):\n    open(" + repr(os.path.join(self.dir, "secret.txt")) + ").read()\n"
            "    return {'x': rng.normal(2.0, 1.0, 30)}\n\n\ndef minus(rng):\n    return {'x': rng.normal(0.0, 1.0, 30)}\n"))
        d = base()
        d["worlds"]["plus"]["python"] = "leaky.py:plus"
        d["worlds"]["minus"]["python"] = "leaky.py:minus"
        code, out, err, cert = self.check(d)
        body = cert["body"]
        self.assertIn("K6_LEAK_ATTEMPT", body["study_flags"])
        self.assertTrue(any(os.path.basename(e["target"]) == "secret.txt" for e in body["leak_log"]))
        self.assertNotEqual(body["verdict"], "FALSIFIABLE")

    def test_allow_paths_are_hashed_like_in_0_3(self):
        self.write("table.txt", "1 2 3")
        d = base()
        d["study"]["allow_paths"] = ["table.txt"]
        code, out, err, cert = self.check(d)
        self.assertEqual(cert["body"]["study"]["allowed_files"],
                         [{"path": "table.txt", "sha256": hashlib.sha256(b"1 2 3").hexdigest()}])

    def test_deterministic_mutation_draws_use_the_declaration_seed_and_are_the_same_at_every_index(self):
        self.write("z.py", "import numpy as np\n\n\ndef plus(rng):\n    return {'x': np.array([0.0])}\n")
        d = {
            "study": {"name": "t", "deterministic": True},
            "worlds": {"plus": {"python": "z.py:plus"}, "minus": {"python": "z.py:plus", "change": "none"}},
            "criteria": [{"id": "C", "pattern": "threshold", "x": "x", "stat": "first", "op": ">", "value": 0.0}],
            "controls": [{"id": "noisy", "criteria": ["C"], "mutations": [{"op": "noise", "column": "x", "sd": 1.0}]}],
            "budget": {"base_seed": 4242},
        }
        code, out, err, cert = self.check(d)
        body = cert["body"]
        self.assertNotIn("NONDETERMINISTIC", body["study_flags"])
        expected = int(declaration_rng(4242, "control:noisy").normal(0.0, 1.0, size=1)[0] > 0.0)
        self.assertEqual(body["components"][0]["counts"]["control:noisy"]["holds"], expected)
        self.assertEqual(body["components"][0]["counts"]["control:noisy"]["n"], 1)

    def test_a_derived_world_pairs_with_plus_in_stochastic_mode(self):
        # the identical-minus check pairs the minus sample with the plus generator: a derived world from plus whose only
        # mutation changes the criterion's key differs; one that changes an unread key is reported as unread
        d = base()
        d["worlds"]["minus"] = {"derive": "plus", "change": "g shuffled", "mutations": [{"op": "constant", "column": "g", "value": "z"}]}
        code, out, err, cert = self.check(d)
        comp = cert["body"]["components"][0]
        self.assertTrue(comp["minus_check"]["paired"])
        self.assertFalse(comp["minus_check"]["identical"])
        self.assertEqual(comp["minus_check"]["changed_keys"], ["g"])
        self.assertIn("K2_MINUS_UNREAD", comp["flags"])


class TestPackageRules(unittest.TestCase):
    MODULES = ("common", "data_io", "manifest", "mutations", "passes", "patterns")
    FORBIDDEN = {"subprocess", "socket", "urllib", "http", "requests", "ftplib", "smtplib", "scipy", "ctypes"}

    def test_new_modules_use_only_the_standard_library_and_numpy_and_never_write_files(self):
        allowed = set(sys.stdlib_module_names) | {"numpy"}
        for name in self.MODULES:
            path = os.path.join(_helpers.ROOT, "truth_gate", name + ".py")
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            roots = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    roots.add(node.module.split(".")[0])
                elif isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
                    mode = ast.literal_eval(node.args[1]) if len(node.args) > 1 else "r"
                    self.assertNotRegex(str(mode), "[wax+]", f"{name} opens a file for writing")
            self.assertLessEqual(roots, allowed, name)
            self.assertFalse(roots & self.FORBIDDEN, name)

    def test_the_kapi_shim_aliases_the_new_modules(self):
        import importlib
        import kapi
        for name in self.MODULES:
            self.assertIs(importlib.import_module("kapi." + name), importlib.import_module("truth_gate." + name))
            self.assertIs(getattr(kapi, name), importlib.import_module("truth_gate." + name))


if __name__ == "__main__":
    unittest.main()
