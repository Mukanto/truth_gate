"""Mutation library (spec 0.6, section 6).

A mutation is an inline table ``{ op = "...", ... }``.  :func:`validate_mutations` checks the declaration (manifest
time); :func:`apply_mutations` applies a validated list to a *copy* of a sample (evaluation time, never in place).
A mutation that references a missing key or does not fit the data raises an exception, which the engine turns into
UNDEFINED.
"""

from __future__ import annotations

import zlib
from typing import Any

import numpy as np

from .common import (
    NUMERIC_KINDS, NotApplicable, check_keys, check_number, fail, get_number, get_str, get_str_list, is_int, join,
    parse_selection, selection_mask,
)
from .sampling import copy_data

ROW_OPS = frozenset({"shuffle", "subsample", "permute_rows", "null_effect"})
WHERE_OPS = frozenset({"scale", "offset", "constant", "noise", "sign_flip"})  # the ops marked with a dagger
STATS_CONSTANT = ("mean", "median", "first")

_ARGS = {  # op -> (required, optional)
    "shuffle": ((), ("column", "columns")),
    "swap": (("a", "b"), ()),
    "scale": (("column", "factor"), ()),
    "offset": (("column", "value"), ()),
    "constant": (("column",), ("value", "stat")),
    "noise": (("column",), ("sd", "rel_sd")),
    "subsample": (("fraction",), ()),
    "null_effect": (("outcome", "group", "reference"), ()),
    "reverse": (("column",), ()),
    "sign_flip": (("column",), ()),
    "permute_rows": ((), ()),
}
OPS = tuple(_ARGS)


# --------------------------------------------------------------------------
# Validation (manifest time)
# --------------------------------------------------------------------------

def validate_mutations(items: Any, where: str) -> list:
    """Validate a ``mutations = [...]`` list and return normalised copies."""
    if not isinstance(items, list) or not items:
        fail(where, "must be a non-empty list of { op = ... } tables")
    return [_validate_one(item, f"{where}[{i}]") for i, item in enumerate(items)]


def _validate_one(item: Any, where: str) -> dict:
    if not isinstance(item, dict):
        fail(where, "must be a table")
    op = item.get("op")
    if not isinstance(op, str):
        fail(join(where, "op"), "missing required key" if "op" not in item else "must be a string")
    if op not in _ARGS:
        fail(join(where, "op"), f"unknown mutation {op!r}; one of {', '.join(OPS)}")
    required, optional = _ARGS[op]
    extra = ("where",) if op in WHERE_OPS else ()
    check_keys(item, where, ("op",) + tuple(required), tuple(optional) + extra)
    out: dict = {"op": op}
    if "where" in item:
        out["where"] = parse_selection(item["where"], join(where, "where"))
    check = _CHECKS[op]
    check(item, out, where)
    return out


def _check_shuffle(item: dict, out: dict, where: str) -> None:
    if ("column" in item) == ("columns" in item):
        fail(where, "needs exactly one of `column` and `columns`")
    if "column" in item:
        out["column"] = get_str(item, "column", where)
    else:
        out["columns"] = get_str_list(item, "columns", where, required=True, non_empty=True, unique=True)


def _check_swap(item: dict, out: dict, where: str) -> None:
    out["a"], out["b"] = get_str(item, "a", where), get_str(item, "b", where)
    if out["a"] == out["b"]:
        fail(where, "`a` and `b` must differ")


def _check_scale(item: dict, out: dict, where: str) -> None:
    out["column"] = get_str(item, "column", where)
    out["factor"] = get_number(item, "factor", where)
    if out["factor"] == 1:
        fail(join(where, "factor"), "factor = 1 changes nothing (a no-op)")


def _check_offset(item: dict, out: dict, where: str) -> None:
    out["column"] = get_str(item, "column", where)
    out["value"] = get_number(item, "value", where)
    if out["value"] == 0:
        fail(join(where, "value"), "value = 0 changes nothing (a no-op)")


def _check_constant(item: dict, out: dict, where: str) -> None:
    out["column"] = get_str(item, "column", where)
    if ("value" in item) == ("stat" in item):
        fail(where, "needs exactly one of `value` and `stat`")
    if "value" in item:
        value = item["value"]
        if isinstance(value, (str, bool)):
            out["value"] = value
        else:
            check_number(value, join(where, "value"))
            out["value"] = value
    else:
        if item["stat"] not in STATS_CONSTANT:
            fail(join(where, "stat"), f"must be one of {', '.join(STATS_CONSTANT)}")
        if "where" in item:
            fail(join(where, "stat"), "`stat` together with `where` is not supported (it is not specified whether the "
                                      "statistic is taken over all rows or over the selected rows)")
        out["stat"] = item["stat"]


def _check_noise(item: dict, out: dict, where: str) -> None:
    out["column"] = get_str(item, "column", where)
    if ("sd" in item) == ("rel_sd" in item):
        fail(where, "needs exactly one of `sd` and `rel_sd`")
    key = "sd" if "sd" in item else "rel_sd"
    out[key] = get_number(item, key, where, lo=0, lo_open=True)  # 0 is a no-op, negatives make no sense
    if key == "rel_sd" and "where" in item:
        fail(join(where, "rel_sd"), "`rel_sd` together with `where` is not supported (it is not specified whether the "
                                    "standard deviation is taken over all rows or over the selected rows)")


def _check_subsample(item: dict, out: dict, where: str) -> None:
    check_number(item["fraction"], join(where, "fraction"))
    if item["fraction"] == 1:
        fail(join(where, "fraction"), "fraction = 1 keeps every row (a no-op)")
    if not 0 < item["fraction"] < 1:
        fail(join(where, "fraction"), "must be in (0, 1)")
    out["fraction"] = item["fraction"]


def _check_null_effect(item: dict, out: dict, where: str) -> None:
    out["outcome"], out["group"] = get_str(item, "outcome", where), get_str(item, "group", where)
    ref = item["reference"]
    if not (isinstance(ref, (str, bool)) or is_int(ref)):
        fail(join(where, "reference"), "must be a string, a bool or an integer")
    out["reference"] = ref


def _check_column(item: dict, out: dict, where: str) -> None:
    out["column"] = get_str(item, "column", where)


def _check_none(item: dict, out: dict, where: str) -> None:
    return None


_CHECKS = {
    "shuffle": _check_shuffle, "swap": _check_swap, "scale": _check_scale, "offset": _check_offset,
    "constant": _check_constant, "noise": _check_noise, "subsample": _check_subsample,
    "null_effect": _check_null_effect, "reverse": _check_column, "sign_flip": _check_column,
    "permute_rows": _check_none,
}


def needs_row_keys(mutations: list) -> list:
    """Ops of a validated list that need row-aligned keys (spec section 3.2)."""
    return [m["op"] for m in mutations if m["op"] in ROW_OPS]


def op_names(mutations: list) -> list:
    return [m["op"] for m in mutations]


# --------------------------------------------------------------------------
# Application (evaluation time)
# --------------------------------------------------------------------------

def declaration_rng(base_seed: int, label: str) -> np.random.Generator:
    """Generator of a declared mutation list in a deterministic study (spec section 6).

    Seeded by the base seed and the declaration (``kind:id``), so it is identical at every sample index.
    """
    seq = np.random.SeedSequence([base_seed, zlib.crc32(("mutation:" + label).encode())])
    return np.random.default_rng(seq)


def apply_mutations(data: dict, mutations: list, rng: np.random.Generator, row_keys: tuple) -> dict:
    """Apply validated mutations in order to a copy of ``data``; ``data`` itself is never changed."""
    out = copy_data(data)
    for m in mutations:
        out = _APPLY[m["op"]](out, m, rng, tuple(row_keys))
    return out


def _numeric(arr: np.ndarray) -> None:
    if arr.dtype.kind not in NUMERIC_KINDS:
        raise NotApplicable("the column is not numeric")


def _mask(data: dict, m: dict, arr: np.ndarray):
    if "where" not in m:
        return None
    if arr.ndim < 1:
        raise NotApplicable("a selection needs an array with a first axis")
    mask = selection_mask(data, m["where"])
    if mask.shape[0] != arr.shape[0]:
        raise NotApplicable("the selection column and the target differ in length")
    return mask


def _arith(data: dict, m: dict, fn, to_float: bool) -> dict:
    """Apply ``fn`` to the (selected rows of the) column; ``to_float`` converts an int column to float64 first."""
    arr = data[m["column"]]
    _numeric(arr)
    mask = _mask(data, m, arr)
    base = arr.astype(np.float64) if (to_float and arr.dtype.kind in "iu") else arr.copy()
    if mask is None:
        result = np.asarray(fn(base)).astype(base.dtype, copy=False)
    else:
        result = base.copy()
        result[mask] = np.asarray(fn(base[mask])).astype(base.dtype, copy=False)
    return {**data, m["column"]: np.array(result, copy=True)}


def _scale(data, m, rng, row_keys):
    factor = m["factor"]
    keeps_int = is_int(factor)
    return _arith(data, m, lambda a: a * factor, to_float=not keeps_int)


def _offset(data, m, rng, row_keys):
    value = m["value"]
    keeps_int = is_int(value)
    return _arith(data, m, lambda a: a + value, to_float=not keeps_int)


def _sign_flip(data, m, rng, row_keys):
    return _arith(data, m, lambda a: -a, to_float=False)


def _noise(data, m, rng, row_keys):
    arr = data[m["column"]]
    _numeric(arr)
    if "sd" in m:
        sd = float(m["sd"])
    else:
        if arr.size < 2:
            raise NotApplicable("rel_sd needs at least two values")
        sd = float(m["rel_sd"]) * float(np.std(arr.astype(np.float64), ddof=1))
    if not (np.isfinite(sd) and sd > 0):
        raise NotApplicable("the noise scale is zero or not finite")
    mask = _mask(data, m, arr)
    base = arr.astype(np.float64) if arr.dtype.kind in "iu" else arr.copy()
    if mask is None:
        result = base + rng.normal(0.0, sd, size=base.shape)
    else:
        result = base.copy()
        result[mask] = base[mask] + rng.normal(0.0, sd, size=base[mask].shape)
    return {**data, m["column"]: np.array(result, dtype=base.dtype, copy=True)}


def _fit_value(arr: np.ndarray, value: Any) -> Any:
    """``value`` as a scalar of the column's dtype kind, or ``NotApplicable``."""
    kind = arr.dtype.kind
    if kind == "b":
        if not isinstance(value, (bool, np.bool_)):
            raise NotApplicable("a bool column needs a bool value")
        return bool(value)
    if kind == "U":
        if not isinstance(value, str):
            raise NotApplicable("a str column needs a string value")
        return value
    if isinstance(value, (bool, np.bool_, str)):
        raise NotApplicable("a numeric column needs a number")
    if not np.isfinite(float(value)):
        raise NotApplicable("the value is not finite")
    if kind == "f":
        return float(value)
    if kind in "iu":
        if float(value) != int(value):
            raise NotApplicable("an int column cannot take a non-integer value (the dtype is kept)")
        return int(value)
    raise NotApplicable("unsupported column type")


def _constant(data, m, rng, row_keys):
    arr = data[m["column"]]
    if "stat" in m:
        if arr.size == 0:
            raise NotApplicable("the column is empty")
        if m["stat"] == "first":
            value = arr.flat[0]
        else:
            _numeric(arr)
            flat = arr.astype(np.float64).ravel()
            value = float(np.mean(flat)) if m["stat"] == "mean" else float(np.median(flat))
            if arr.dtype.kind in "iu":  # R-29 (audit F5): mean / median of an int column give a float64 column, so the
                arr = arr.astype(np.float64)  # op never fails depending on whether the statistic happens to be integral
    else:
        value = m["value"]
    value = _fit_value(arr, value)
    mask = _mask(data, m, arr)
    if arr.dtype.kind == "U":  # widen so that a longer string is not truncated silently
        width = max(arr.dtype.itemsize // 4, len(value), 1)
        arr = arr.astype(f"<U{width}")
    result = arr.copy()
    if mask is None:
        result[...] = value
    else:
        result[mask] = value
    return {**data, m["column"]: result}


def _first_axis(arrays: list) -> int:
    n = None
    for arr in arrays:
        if arr.ndim < 1:
            raise NotApplicable("an array without a first axis cannot be permuted")
        if n is None:
            n = arr.shape[0]
        elif arr.shape[0] != n:
            raise NotApplicable("the arrays differ in first-axis length")
    return int(n)


def _shuffle(data, m, rng, row_keys):
    keys = [m["column"]] if "column" in m else list(m["columns"])
    arrays = [data[k] for k in keys]
    perm = rng.permutation(_first_axis(arrays))
    out = dict(data)
    for k, arr in zip(keys, arrays):
        out[k] = arr[perm].copy()
    return out


def _swap(data, m, rng, row_keys):
    a, b = data[m["a"]], data[m["b"]]
    if a.shape != b.shape:
        raise NotApplicable("swap needs two arrays of the same shape")
    return {**data, m["a"]: b.copy(), m["b"]: a.copy()}


def _row_arrays(data: dict, row_keys: tuple) -> tuple:
    if not row_keys:
        raise NotApplicable("the world has no row-aligned keys")
    arrays = [data[k] for k in row_keys]
    return arrays, _first_axis(arrays)


def _subsample(data, m, rng, row_keys):
    arrays, n = _row_arrays(data, row_keys)
    k = round(m["fraction"] * n)
    if k < 1:
        raise NotApplicable("the subsample would be empty")
    idx = np.sort(rng.choice(n, size=k, replace=False))
    out = dict(data)
    for key, arr in zip(row_keys, arrays):
        out[key] = arr[idx].copy()
    return out


def _permute_rows(data, m, rng, row_keys):
    arrays, n = _row_arrays(data, row_keys)
    perm = rng.permutation(n)
    out = dict(data)
    for key, arr in zip(row_keys, arrays):
        out[key] = arr[perm].copy()
    return out


def _null_effect(data, m, rng, row_keys):
    outcome, group = data[m["outcome"]], data[m["group"]]
    if outcome.ndim < 1 or group.ndim != 1 or outcome.shape[0] != group.shape[0]:
        raise NotApplicable("outcome and group must share the first axis, and group must be one-dimensional")
    ref = m["reference"]
    kind = group.dtype.kind
    if isinstance(ref, bool):
        fits = kind == "b"
    elif isinstance(ref, str):
        fits = kind == "U"
    else:
        fits = kind in "iu"
    if not fits:
        raise NotApplicable("the group column does not fit the reference value")
    is_ref = np.asarray(group == ref, dtype=bool)
    ref_rows = np.flatnonzero(is_ref)
    other_rows = np.flatnonzero(~is_ref)
    if ref_rows.size == 0:
        raise NotApplicable("no row carries the reference group")
    result = outcome.copy()
    if other_rows.size:
        draws = rng.integers(0, ref_rows.size, size=other_rows.size)
        result[other_rows] = outcome[ref_rows[draws]]
    return {**data, m["outcome"]: result}


def _reverse(data, m, rng, row_keys):
    arr = data[m["column"]]
    if arr.ndim < 1:
        raise NotApplicable("an array without a first axis cannot be reversed")
    return {**data, m["column"]: arr[::-1].copy()}


_APPLY = {
    "shuffle": _shuffle, "swap": _swap, "scale": _scale, "offset": _offset, "constant": _constant, "noise": _noise,
    "subsample": _subsample, "null_effect": _null_effect, "reverse": _reverse, "sign_flip": _sign_flip,
    "permute_rows": _permute_rows,
}


class MutationSet:
    """A validated mutation list as a callable ``(data, rng) -> data`` (world, control or premise transform).

    Stochastic study: draws come from the generator the engine passes (stream and sample of the call).
    Deterministic study: draws come from :func:`declaration_rng`, created afresh at every call, so the result is the
    same at every sample index (spec section 6).
    """

    def __init__(self, label: str, mutations: list, row_keys: tuple, deterministic: bool, base_seed: int) -> None:
        self.label = label
        self.mutations = mutations
        self.row_keys = tuple(row_keys)
        self.deterministic = deterministic
        self.base_seed = base_seed

    def __call__(self, data: dict, rng: np.random.Generator) -> dict:
        draw = declaration_rng(self.base_seed, self.label) if self.deterministic else rng
        return apply_mutations(data, self.mutations, draw, self.row_keys)


__all__ = [
    "OPS", "ROW_OPS", "MutationSet", "apply_mutations", "declaration_rng", "needs_row_keys", "op_names",
    "validate_mutations",
]
