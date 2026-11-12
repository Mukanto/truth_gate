"""Data readers for ``file`` worlds (spec 0.6, section 3.3): CSV, JSON (an object of arrays) and NPZ.

The readers run before the leak guard is armed (spec section 1.2); they read a file once, hash its bytes and parse
those same bytes.  Every problem is a :class:`~truth_gate.common.ManifestError` (exit code 4).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from .common import ManifestError, fail

MISSING = frozenset({"", "NA", "NaN", "nan"})
BOOL_TRUE = frozenset({"true", "TRUE", "True"})
BOOL_FALSE = frozenset({"false", "FALSE", "False"})
_NUMBER = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_INTEGER = re.compile(r"^[+-]?\d+$")
KINDS = {".csv": "csv", ".json": "json", ".npz": "npz"}


@dataclass(frozen=True, eq=False)
class Table:
    """A parsed data file: arrays by key, and the keys that are aligned by row."""

    data: dict
    row_keys: tuple
    n_rows: Optional[int]
    kind: str


def file_kind(path: str) -> str:
    kind = KINDS.get(os.path.splitext(path)[1].lower())
    if kind is None:
        raise ManifestError(f"{path}: data files must be .csv, .json or .npz")
    return kind


def read_bytes(path: str, where: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise ManifestError(f"{where}: cannot read {path} ({type(exc).__name__})") from None


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_table(path: str, where: str, declared: dict, rows: list, delimiter: Optional[str]) -> tuple:
    """Read and parse a data file.  Returns ``(Table, sha256_of_the_bytes)``.

    ``declared`` maps column name to ``{type, role}``; ``rows`` is the ``[data] rows`` list (row-aligned keys of
    JSON and NPZ files; a CSV file is aligned by every column).
    """
    kind = file_kind(path)
    if delimiter is not None and kind != "csv":
        fail(where, "`delimiter` is only valid for CSV files")
    raw = read_bytes(path, where)
    if kind == "csv":
        table = parse_csv(raw, where, declared, "," if delimiter is None else delimiter)
    elif kind == "json":
        table = parse_json(raw, where, declared, rows)
    else:
        table = parse_npz(raw, where, declared, rows)
    for column in declared:
        if column not in table.data:
            fail(where, f"the declared column {column!r} is not in {os.path.basename(path)}")
    return table, sha256_hex(raw)


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------

def parse_csv(raw: bytes, where: str, declared: dict, delimiter: str = ",") -> Table:
    """CSV dialect of spec section 3.3 and R-31: UTF-8 (a BOM is ignored), header row, ``.`` decimals, missing = "", NA, NaN, nan."""
    if not isinstance(delimiter, str) or len(delimiter) != 1 or delimiter in "\r\n\"":
        fail(where, "`delimiter` must be a single character")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail(where, "the file is not valid UTF-8")
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    except csv.Error as exc:
        fail(where, f"CSV syntax error: {exc}")
    while rows and not rows[-1]:  # R-31: blank lines after the last data line are ignored
        rows.pop()
    if not rows:
        fail(where, "the CSV file is empty (a header row is required)")
    header = rows[0]
    if not header:
        fail(where, "the first line is blank (the header row is required)")
    if any(h == "" for h in header):
        fail(where, "the header row has an empty column name")
    if len(set(header)) != len(header):
        fail(where, "the header row has duplicate column names")
    body = rows[1:]
    if not body:
        fail(where, "the CSV file has no data rows")
    for number, row in enumerate(body, start=2):
        if not row:  # R-31: a blank line between data lines is one missing value, or an error with several columns
            if len(header) != 1:
                fail(where, f"data row {number} is a blank line (a blank line is a missing value only in a "
                            "single-column file)")
            body[number - 2] = row = [""]
        if len(row) != len(header):
            fail(where, f"data row {number} has {len(row)} cells, the header has {len(header)}")
    data = {}
    for j, name in enumerate(header):
        cells = [row[j] for row in body]
        decl = declared.get(name)
        if decl is not None:
            data[name] = _convert_declared(cells, decl["type"], f"{where} column {name!r}")
        else:
            data[name] = _convert_detected(cells)
    return Table(data=data, row_keys=tuple(header), n_rows=len(body), kind="csv")


def _is_number(cell: str) -> bool:
    return bool(_NUMBER.match(cell))


def _convert_declared(cells: list, declared_type: str, label: str) -> np.ndarray:
    if declared_type == "float":
        out = []
        for cell in cells:
            if cell in MISSING:
                out.append(math.nan)
            elif _is_number(cell):
                out.append(float(cell))
            else:
                fail(label, f"value {cell!r} is not a float")
        return np.asarray(out, dtype=np.float64)
    if declared_type == "int":
        out = []
        for cell in cells:
            if cell in MISSING:
                fail(label, "a declared int column may not contain missing values")
            if not _INTEGER.match(cell):
                fail(label, f"value {cell!r} is not an integer")
            try:
                out.append(int(cell))
            except ValueError:  # R-33: a cell of more than 4300 digits is refused by Python's int(); a manifest error
                fail(label, f"an integer cell is too long to read ({len(cell)} characters)")
        try:
            return np.asarray(out, dtype=np.int64)
        except OverflowError:
            fail(label, "an integer is outside the int64 range")
    if declared_type == "bool":
        out = []
        for cell in cells:
            if cell in BOOL_TRUE:
                out.append(True)
            elif cell in BOOL_FALSE:
                out.append(False)
            else:
                fail(label, f"value {cell!r} is not a bool (true/false, TRUE/FALSE, True/False)")
        return np.asarray(out, dtype=np.bool_)
    return np.asarray(cells, dtype=str)


def _convert_detected(cells: list) -> np.ndarray:
    """Undeclared column: bool, else float64, else str.  Auto-detection never produces int."""
    if all(c in BOOL_TRUE or c in BOOL_FALSE for c in cells):
        return np.asarray([c in BOOL_TRUE for c in cells], dtype=np.bool_)
    if all(c in MISSING or _is_number(c) for c in cells):
        return np.asarray([math.nan if c in MISSING else float(c) for c in cells], dtype=np.float64)
    return np.asarray(cells, dtype=str)


# --------------------------------------------------------------------------
# JSON and NPZ
# --------------------------------------------------------------------------

def _flatten(value: Any):
    if isinstance(value, list):
        for item in value:
            yield from _flatten(item)
    else:
        yield value


def _json_array(value: Any, decl: Optional[dict], label: str) -> np.ndarray:
    items = list(_flatten(value))
    declared_type = decl["type"] if decl else None
    is_bool = [isinstance(v, bool) for v in items]
    is_str = [isinstance(v, str) for v in items]
    is_int_ = [isinstance(v, int) and not isinstance(v, bool) for v in items]
    is_float = [isinstance(v, float) for v in items]
    is_null = [v is None for v in items]
    if len(items) != sum(is_bool) + sum(is_str) + sum(is_int_) + sum(is_float) + sum(is_null):
        fail(label, "values must be numbers, bools, strings or null")
    try:
        if declared_type == "float":
            if any(is_bool) or any(is_str):
                fail(label, "a declared float column holds numbers (or null for missing)")
            return np.array(value, dtype=np.float64)
        if declared_type == "int":
            if not all(is_int_):
                fail(label, "a declared int column holds integers only")
            return np.array(value, dtype=np.int64)
        if declared_type == "bool":
            if not all(is_bool):
                fail(label, "a declared bool column holds true/false only")
            return np.array(value, dtype=np.bool_)
        if declared_type == "str":
            if not all(is_str):
                fail(label, "a declared str column holds strings only")
            return np.array(value, dtype=str)
        if not items:
            return np.array(value, dtype=np.float64)
        if items and all(is_bool):
            return np.array(value, dtype=np.bool_)
        if items and all(is_str):
            return np.array(value, dtype=str)
        if not any(is_bool) and not any(is_str) and (any(is_float) or any(is_null)):
            return np.array(value, dtype=np.float64)
        if items and all(is_int_):
            return np.array(value, dtype=np.int64)
    except (ValueError, OverflowError):
        fail(label, "the nested lists are ragged or hold out-of-range values")
    fail(label, "mixed value types")


def _check_rows(data: dict, rows: list, where: str) -> tuple:
    """Row-aligned keys of a JSON or NPZ file: the keys of ``[data] rows``, sharing their first-axis length."""
    for key in rows:
        if key not in data:
            fail(where, f"the row-aligned key {key!r} (`[data] rows`) is not in the file")
        if data[key].ndim < 1:
            fail(where, f"the row-aligned key {key!r} has no first axis")
    lengths = {data[key].shape[0] for key in rows}
    if len(lengths) > 1:
        fail(where, "the row-aligned keys (`[data] rows`) differ in first-axis length")
    return tuple(rows), (lengths.pop() if lengths else None)


def parse_json(raw: bytes, where: str, declared: dict, rows: list) -> Table:
    try:
        parsed = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        fail(where, f"the file is not valid JSON ({type(exc).__name__})")
    if not isinstance(parsed, dict) or not parsed:
        fail(where, "a JSON data file must be a non-empty object of arrays")
    data = {key: _json_array(value, declared.get(key), f"{where} key {key!r}") for key, value in parsed.items()}
    row_keys, n = _check_rows(data, rows, where)
    return Table(data=data, row_keys=row_keys, n_rows=n, kind="json")


def _fit_npz(arr: np.ndarray, decl: Optional[dict], label: str) -> np.ndarray:
    kind = arr.dtype.kind
    if kind not in "biufU":
        fail(label, f"unsupported dtype {arr.dtype} (bool, int, float and str arrays only)")
    if decl is None:
        return np.array(arr)
    declared_type = decl["type"]
    ok = {"float": kind in "iuf", "int": kind in "iu", "bool": kind == "b", "str": kind == "U"}[declared_type]
    if not ok:
        fail(label, f"dtype {arr.dtype} does not fit the declared type {declared_type!r}")
    target = {"float": np.float64, "int": np.int64, "bool": np.bool_, "str": None}[declared_type]
    return np.array(arr) if target is None else np.array(arr, dtype=target)


def parse_npz(raw: bytes, where: str, declared: dict, rows: list) -> Table:
    try:
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            loaded = {key: archive[key] for key in archive.files}
    except Exception as exc:  # numpy raises several types for a damaged archive
        fail(where, f"the file is not a readable NPZ archive ({type(exc).__name__})")
    if not loaded:
        fail(where, "the NPZ archive is empty")
    data = {key: _fit_npz(arr, declared.get(key), f"{where} key {key!r}") for key, arr in loaded.items()}
    row_keys, n = _check_rows(data, rows, where)
    return Table(data=data, row_keys=row_keys, n_rows=n, kind="npz")


# --------------------------------------------------------------------------
# Sampling a table (spec section 3.3, "Sampling")
# --------------------------------------------------------------------------

def sample_table(table: Table, rng: np.random.Generator, resample: str, fraction: Optional[float]) -> dict:
    """One sample of a file world.

    ``none``: the table itself (copied).  ``bootstrap``: ``n`` rows with replacement, one row index for every
    row-aligned key.  ``subsample``: ``round(fraction * n)`` rows without replacement (kept in table order).  Keys that
    are not row-aligned are copied unchanged.
    """
    if resample == "none":
        return {key: arr.copy() for key, arr in table.data.items()}
    n = table.n_rows
    if resample == "bootstrap":
        idx = rng.integers(0, n, size=n)
    else:
        k = round(fraction * n)
        if k < 1:
            raise ValueError("the subsample would be empty")
        idx = np.sort(rng.choice(n, size=k, replace=False))
    aligned = set(table.row_keys)
    return {key: (arr[idx] if key in aligned else arr.copy()) for key, arr in table.data.items()}
