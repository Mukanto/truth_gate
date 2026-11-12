"""Shared errors and validation helpers of the manifest layer (spec 0.6, sections 3, 4 and 6).

Everything here is pure: no file access, no randomness.  ``ManifestError`` is a problem found from the manifest text
and the environment alone (exit code 4, no certificate); ``NotApplicable`` is raised at evaluation time when the data do
not fit (types, shapes, an empty selection), which a pattern turns into UNDEFINED.
"""

from __future__ import annotations

import math
import operator
from typing import Any, Iterable, Optional

import numpy as np

STD_OPS = (">", ">=", "<", "<=")
OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}
NUMERIC_KINDS = "iuf"


class ManifestError(Exception):
    """A manifest problem found from the text and the environment alone: exit 4, no certificate."""


class NotApplicable(Exception):
    """The data do not fit the operation (types, shapes, empty selection, non-finite value)."""


# --------------------------------------------------------------------------
# Validation helpers (manifest time)
# --------------------------------------------------------------------------

def join(where: str, key: Any) -> str:
    """Dotted path of a key inside a table, for error messages."""
    return f"{where}.{key}" if where else str(key)


def fail(where: str, message: str):
    raise ManifestError(f"{where}: {message}")


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_finite_number(value: Any) -> bool:
    return is_number(value) and math.isfinite(value)


def check_keys(table: Any, where: str, required: Iterable[str] = (), optional: Iterable[str] = ()) -> None:
    """``table`` must be a table with the required keys and no keys outside ``required`` plus ``optional``."""
    if not isinstance(table, dict):
        fail(where, "must be a table")
    allowed = set(required) | set(optional)
    for key in table:
        if key not in allowed:
            fail(join(where, key), "unknown key")
    for key in required:
        if key not in table:
            fail(join(where, key), "missing required key")


def get_str(table: dict, key: str, where: str, *, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    if key not in table:
        if required:
            fail(join(where, key), "missing required key")
        return default
    value = table[key]
    if not isinstance(value, str):
        fail(join(where, key), "must be a string")
    return value


def get_bool(table: dict, key: str, where: str, default: bool) -> bool:
    if key not in table:
        return default
    if not isinstance(table[key], bool):
        fail(join(where, key), "must be true or false")
    return table[key]


def get_number(table: dict, key: str, where: str, *, required: bool = True, default: Any = None,
               lo: Optional[float] = None, hi: Optional[float] = None, lo_open: bool = False,
               hi_open: bool = False) -> Any:
    """A finite number (int or float, not bool), optionally inside an interval."""
    if key not in table:
        if required:
            fail(join(where, key), "missing required key")
        return default
    value = table[key]
    check_number(value, join(where, key), lo=lo, hi=hi, lo_open=lo_open, hi_open=hi_open)
    return value


def check_number(value: Any, where: str, *, lo: Optional[float] = None, hi: Optional[float] = None,
                 lo_open: bool = False, hi_open: bool = False) -> None:
    if not is_number(value):
        fail(where, "must be a number")
    if not math.isfinite(value):
        fail(where, "must be finite")
    if lo is not None and (value <= lo if lo_open else value < lo):
        fail(where, f"must be {'>' if lo_open else '>='} {lo}")
    if hi is not None and (value >= hi if hi_open else value > hi):
        fail(where, f"must be {'<' if hi_open else '<='} {hi}")


def get_int(table: dict, key: str, where: str, *, required: bool = True, default: Any = None,
            lo: Optional[int] = None) -> Any:
    if key not in table:
        if required:
            fail(join(where, key), "missing required key")
        return default
    value = table[key]
    if not is_int(value):
        fail(join(where, key), "must be an integer")
    if lo is not None and value < lo:
        fail(join(where, key), f"must be >= {lo}")
    return value


def get_str_list(table: dict, key: str, where: str, *, required: bool = False, non_empty: bool = False,
                 unique: bool = False) -> list:
    if key not in table:
        if required:
            fail(join(where, key), "missing required key")
        return []
    value = table[key]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        fail(join(where, key), "must be a list of strings")
    if non_empty and not value:
        fail(join(where, key), "must not be empty")
    if unique and len(set(value)) != len(value):
        fail(join(where, key), "must not contain duplicates")
    return list(value)


def get_op(table: dict, key: str, where: str, allowed: Iterable[str] = STD_OPS) -> str:
    op = get_str(table, key, where)
    if op not in tuple(allowed):
        fail(join(where, key), f"must be one of {', '.join(allowed)}")
    return op


# --------------------------------------------------------------------------
# Selections (spec section 4): { column, equals } or { column, op, value }
# --------------------------------------------------------------------------

def parse_selection(sel: Any, where: str) -> dict:
    """Validate a ``where`` selection and return it normalised."""
    if not isinstance(sel, dict):
        fail(where, "must be a table such as { column = ..., equals = ... } or { column = ..., op = ..., value = ... }")
    check_keys(sel, where, ["column"], ["equals", "op", "value"])
    column = get_str(sel, "column", where)
    has_equals = "equals" in sel
    has_cmp = "op" in sel or "value" in sel
    if has_equals == has_cmp:
        fail(where, "needs either `equals` or both `op` and `value`")
    if has_equals:
        if not isinstance(sel["equals"], (str, bool)):
            fail(join(where, "equals"), "must be a string or a bool (`equals` is only for str and bool columns)")
        return {"column": column, "equals": sel["equals"]}
    op = get_op(sel, "op", where)
    value = get_number(sel, "value", where)
    return {"column": column, "op": op, "value": value}


def selection_mask(data: dict, sel: dict) -> np.ndarray:
    """Boolean mask over the first axis; the selection column must exist (``KeyError`` otherwise)."""
    column = data[sel["column"]]
    if column.ndim != 1:
        raise NotApplicable("selection column is not one-dimensional")
    if "equals" in sel:
        target = sel["equals"]
        kind = column.dtype.kind
        if isinstance(target, bool):
            if kind != "b":
                raise NotApplicable("`equals` with a bool needs a bool column")
        elif kind != "U":
            raise NotApplicable("`equals` with a string needs a str column")
        return np.asarray(column == target, dtype=bool)
    if column.dtype.kind not in NUMERIC_KINDS:
        raise NotApplicable("numeric selection needs a numeric column")
    return np.asarray(OPERATORS[sel["op"]](column, sel["value"]), dtype=bool)
