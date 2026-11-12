"""Criterion patterns (spec 0.6, section 4).

A pattern criterion is declared in the manifest, compiled once by :class:`Pattern` and evaluated on data dicts.  Each
pattern returns HOLDS, FAILS or UNDEFINED.  The three rules of the spec that matter most for the engine:

* every key a pattern references (including every part of ``all_of`` / ``any_of``) is looked up *before* anything is
  evaluated; a missing key raises ``KeyError``, so the whole criterion is UNDEFINED, as for any exception in 0.3;
* UNDEFINED when a selection is empty, a value used is not finite, a denominator is zero or the types do not fit;
* ``==`` exists only for ``stat = "count"`` and in ``largest_true``.

Besides the outcome, a pattern can report the statistics it computed (``record``), which the ``pattern_stats`` pass
(``passes.py``) summarises.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from .common import (
    NUMERIC_KINDS, OPERATORS, STD_OPS, NotApplicable, check_keys, fail, get_bool, get_int, get_number, get_op, get_str,
    is_finite_number, is_int, join, parse_selection, selection_mask,
)

HOLDS = "HOLDS"
FAILS = "FAILS"
UNDEFINED = "UNDEFINED"

STATS = ("mean", "median", "min", "max", "sum", "std", "quantile", "first", "last", "count", "fraction_true")
CRITERION_KEYS = frozenset({"id", "regime", "control_waiver", "tolerances", "components", "origin"})
LEAF_NAMES = ("threshold", "difference", "ratio_band", "within", "rate", "ci_excludes", "largest_true", "monotone")
COMBINATOR_NAMES = ("all_of", "any_of")
PATTERN_NAMES = LEAF_NAMES + COMBINATOR_NAMES
_RETURN = {HOLDS: True, FAILS: False, UNDEFINED: None}


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def _finite(arr: np.ndarray) -> None:
    if not bool(np.all(np.isfinite(arr))):
        raise NotApplicable("a value is not finite")


def apply_stat(arr: np.ndarray, stat: str, q: Optional[float] = None) -> float:
    """The statistic ``stat`` of the flattened ``arr`` as a float; ``NotApplicable`` when it is not defined."""
    flat = np.ravel(arr)
    if flat.size == 0:  # R-32 (audit F3): "UNDEFINED when a selection is empty" holds for count too
        raise NotApplicable("empty selection")
    if stat == "count":
        return float(flat.size)
    if stat == "fraction_true":
        if flat.dtype.kind != "b":
            raise NotApplicable("fraction_true needs a non-empty bool selection")
        return float(np.mean(flat))
    if flat.dtype.kind not in NUMERIC_KINDS:
        raise NotApplicable("the statistic needs a numeric selection")
    if flat.size == 0:
        raise NotApplicable("empty selection")
    if stat == "first":
        value = flat[0]
    elif stat == "last":
        value = flat[-1]
    else:
        flat = flat.astype(np.float64, copy=False)
        _finite(flat)
        if stat == "mean":
            value = np.mean(flat)
        elif stat == "median":
            value = np.median(flat)
        elif stat == "min":
            value = np.min(flat)
        elif stat == "max":
            value = np.max(flat)
        elif stat == "sum":
            value = np.sum(flat)
        elif stat == "std":
            if flat.size < 2:
                raise NotApplicable("std needs at least two values")
            value = np.std(flat, ddof=1)
        elif stat == "quantile":
            value = np.quantile(flat, q)
        else:  # pragma: no cover - validated at parse time
            raise NotApplicable(f"unknown statistic {stat!r}")
    value = float(value)
    if not np.isfinite(value):
        raise NotApplicable("the statistic is not finite")
    return value


def _stat_rows(mat: np.ndarray, stat: str, q: Optional[float]) -> np.ndarray:
    """The statistic of every row of a 2-D array (bootstrap replicates)."""
    if stat == "count":
        return np.full(mat.shape[0], float(mat.shape[1]))
    if stat == "fraction_true":
        if mat.dtype.kind != "b":
            raise NotApplicable("fraction_true needs a bool selection")
        return mat.mean(axis=1)
    if mat.dtype.kind not in NUMERIC_KINDS:
        raise NotApplicable("the statistic needs a numeric selection")
    if stat == "first":
        return mat[:, 0].astype(np.float64)
    if stat == "last":
        return mat[:, -1].astype(np.float64)
    if stat == "mean":
        return mat.mean(axis=1)
    if stat == "median":
        return np.median(mat, axis=1)
    if stat == "min":
        return mat.min(axis=1)
    if stat == "max":
        return mat.max(axis=1)
    if stat == "sum":
        return mat.sum(axis=1)
    if stat == "std":
        return mat.std(axis=1, ddof=1)
    return np.quantile(mat, q, axis=1)


def _numeric_flat(arr: np.ndarray) -> np.ndarray:
    """Flattened float64 copy of a numeric selection (finite, non-empty)."""
    flat = np.ravel(arr)
    if flat.dtype.kind not in NUMERIC_KINDS:
        raise NotApplicable("a numeric selection is needed")
    if flat.size == 0:
        raise NotApplicable("empty selection")
    flat = flat.astype(np.float64)
    _finite(flat)
    return flat


def _outcome(condition: Any) -> str:
    return HOLDS if bool(condition) else FAILS


# --------------------------------------------------------------------------
# Arguments with selections
# --------------------------------------------------------------------------

def _index_positions(index: list, length: int) -> np.ndarray:
    """The positions of an ``_index`` selection; one outside the array makes the leaf UNDEFINED (R-32, audit F4).

    A data condition, not a missing key: it must raise nothing but ``NotApplicable``, so that the Kleene logic of
    ``all_of`` / ``any_of`` and the ``pattern_stats`` pass see an UNDEFINED leaf and nothing else.
    """
    if max(index) >= length:
        raise NotApplicable("an index position is out of range")
    return np.asarray(index, dtype=np.intp)


class Arg:
    """A data argument (a key) with its optional selection (spec section 4, "Selections")."""

    def __init__(self, table: dict, name: str, where: str) -> None:
        self.name = name
        self.key = get_str(table, name, where)
        self.where: Optional[dict] = None
        self.index: Optional[list] = None
        w_key, i_key = f"{name}_where", f"{name}_index"
        if w_key in table and i_key in table:
            fail(join(where, i_key), f"`{w_key}` and `{i_key}` cannot be combined on one argument")
        if w_key in table:
            self.where = parse_selection(table[w_key], join(where, w_key))
        if i_key in table:
            idx = table[i_key]
            if not isinstance(idx, list) or not idx or not all(is_int(v) and v >= 0 for v in idx):
                fail(join(where, i_key), "must be a non-empty list of non-negative integers")
            self.index = list(idx)

    @staticmethod
    def option_names(name: str) -> tuple:
        return (f"{name}_where", f"{name}_index")

    def keys(self) -> list:
        return [self.key] + ([self.where["column"]] if self.where else [])

    def get(self, data: dict) -> np.ndarray:
        arr = data[self.key]
        if self.where is not None:
            mask = selection_mask(data, self.where)
            if arr.ndim < 1 or arr.shape[0] != mask.shape[0]:
                raise NotApplicable("the selection column and the argument differ in length")
            arr = arr[mask]
        if self.index is not None:
            if arr.ndim < 1:
                raise NotApplicable("an index selection needs an array with a first axis")
            arr = arr[_index_positions(self.index, arr.shape[0])]
        return arr


def _arg_options(*names: str) -> tuple:
    out: list = []
    for name in names:
        out.extend(Arg.option_names(name))
    return tuple(out)


def _parse_stat(table: dict, where: str) -> tuple:
    stat = get_str(table, "stat", where)
    if stat not in STATS:
        fail(join(where, "stat"), f"must be one of {', '.join(STATS)}")
    q = None
    if stat == "quantile":
        q = get_number(table, "q", where, lo=0, hi=1)
    elif "q" in table:
        fail(join(where, "q"), "only valid with stat = \"quantile\"")
    return stat, q


def _parse_op_value(table: dict, where: str, stat: str) -> tuple:
    allowed = STD_OPS + (("==",) if stat == "count" else ())
    op = get_op(table, "op", where, allowed)
    value = get_number(table, "value", where)
    if op == "==" and not is_int(value):
        fail(join(where, "value"), "`==` compares integers: the value must be an integer")
    return op, value


# --------------------------------------------------------------------------
# Leaf patterns
# --------------------------------------------------------------------------

class Leaf:
    """A pattern that computes statistics and compares them."""

    name = ""

    def args(self) -> list:
        return []

    def keys(self) -> list:
        out: list = []
        for arg in self.args():
            out.extend(arg.keys())
        return out

    def thresholds(self) -> dict:  # pragma: no cover - overridden
        return {}

    def compute(self, data: dict) -> tuple:  # pragma: no cover - overridden
        raise NotImplementedError


class Threshold(Leaf):
    name = "threshold"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "x", "stat", "op", "value"), ("q",) + _arg_options("x"))
        self.x = Arg(table, "x", where)
        self.stat, self.q = _parse_stat(table, where)
        self.op, self.value = _parse_op_value(table, where, self.stat)

    def args(self) -> list:
        return [self.x]

    def thresholds(self) -> dict:
        return {"op": self.op, "value": self.value}

    def compute(self, data: dict) -> tuple:
        s = apply_stat(self.x.get(data), self.stat, self.q)
        return _outcome(OPERATORS[self.op](s, self.value)), {"stat": s}


class Difference(Leaf):
    name = "difference"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "a", "b", "stat", "op", "value"),
                   ("q", "paired") + _arg_options("a", "b"))
        self.a, self.b = Arg(table, "a", where), Arg(table, "b", where)
        self.stat, self.q = _parse_stat(table, where)
        self.op, self.value = _parse_op_value(table, where, self.stat)
        self.paired = get_bool(table, "paired", where, False)

    def args(self) -> list:
        return [self.a, self.b]

    def thresholds(self) -> dict:
        return {"op": self.op, "value": self.value, "paired": self.paired}

    def compute(self, data: dict) -> tuple:
        a, b = self.a.get(data), self.b.get(data)
        if self.paired:
            fa, fb = _numeric_flat(a), _numeric_flat(b)
            if fa.shape != fb.shape:
                raise NotApplicable("paired arguments differ in length")
            s = apply_stat(fa - fb, self.stat, self.q)
        else:
            s = apply_stat(a, self.stat, self.q) - apply_stat(b, self.stat, self.q)
        if not np.isfinite(s):
            raise NotApplicable("the difference is not finite")
        return _outcome(OPERATORS[self.op](s, self.value)), {"difference": float(s)}


class RatioBand(Leaf):
    name = "ratio_band"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "a", "b", "stat", "lo", "hi"), ("q",) + _arg_options("a", "b"))
        self.a, self.b = Arg(table, "a", where), Arg(table, "b", where)
        self.stat, self.q = _parse_stat(table, where)
        self.lo = get_number(table, "lo", where)
        self.hi = get_number(table, "hi", where)
        if self.lo > self.hi:
            fail(join(where, "lo"), "must not exceed `hi`")

    def args(self) -> list:
        return [self.a, self.b]

    def thresholds(self) -> dict:
        return {"lo": self.lo, "hi": self.hi}

    def compute(self, data: dict) -> tuple:
        sa = apply_stat(self.a.get(data), self.stat, self.q)
        sb = apply_stat(self.b.get(data), self.stat, self.q)
        if sb == 0:
            raise NotApplicable("the denominator is zero")
        r = sa / sb
        if not np.isfinite(r):
            raise NotApplicable("the ratio is not finite")
        return _outcome(self.lo <= r <= self.hi), {"ratio": float(r)}


class Within(Leaf):
    name = "within"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "a", "b", "tol"), ("mode", "stat", "q") + _arg_options("a", "b"))
        self.a, self.b = Arg(table, "a", where), Arg(table, "b", where)
        self.tol = get_number(table, "tol", where, lo=0)
        self.mode = get_str(table, "mode", where, required=False, default="stat")
        if self.mode not in ("stat", "all"):
            fail(join(where, "mode"), "must be \"stat\" or \"all\"")
        if self.mode == "stat":
            self.stat, self.q = _parse_stat(table, where)
        else:
            self.stat = self.q = None
            for key in ("stat", "q"):
                if key in table:
                    fail(join(where, key), "not valid with mode = \"all\"")

    def args(self) -> list:
        return [self.a, self.b]

    def thresholds(self) -> dict:
        return {"tol": self.tol, "mode": self.mode}

    def compute(self, data: dict) -> tuple:
        a, b = self.a.get(data), self.b.get(data)
        if self.mode == "stat":
            d = abs(apply_stat(a, self.stat, self.q) - apply_stat(b, self.stat, self.q))
            if not np.isfinite(d):
                raise NotApplicable("the difference is not finite")
            return _outcome(d <= self.tol), {"abs_difference": float(d)}
        fa, fb = _numeric_flat(a), _numeric_flat(b)
        if fa.shape != fb.shape:
            raise NotApplicable("the arguments differ in length")
        d = float(np.max(np.abs(fa - fb)))
        if not np.isfinite(d):
            raise NotApplicable("the difference is not finite")
        return _outcome(d <= self.tol), {"max_abs_difference": d}


class Rate(Leaf):
    """Fraction of the selected rows of the condition column that meet the condition.

    Post-freeze revision R-3: ``rate`` has no data argument to prefix, so its optional selection is an unprefixed
    ``where`` / ``index`` applied to the rows of the condition column (``where`` is evaluated on the row-aligned keys of
    the sample, then ``index`` keeps positions of what is left, as for the prefixed selections).
    """

    name = "rate"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "condition", "op", "value"), ("where", "index"))
        cond = table["condition"]
        cwhere = join(where, "condition")
        check_keys(cond, cwhere, ("column", "op", "value"))
        self.column = get_str(cond, "column", cwhere)
        self.cond_op = get_op(cond, "op", cwhere)
        self.cond_value = get_number(cond, "value", cwhere)
        self.op = get_op(table, "op", where)
        self.value = get_number(table, "value", where)
        self.where: Optional[dict] = None
        self.index: Optional[list] = None
        if "where" in table and "index" in table:
            fail(join(where, "index"), "`where` and `index` cannot be combined")
        if "where" in table:
            self.where = parse_selection(table["where"], join(where, "where"))
        if "index" in table:
            idx = table["index"]
            if not isinstance(idx, list) or not idx or not all(is_int(v) and v >= 0 for v in idx):
                fail(join(where, "index"), "must be a non-empty list of non-negative integers")
            self.index = list(idx)

    def keys(self) -> list:
        return [self.column] + ([self.where["column"]] if self.where else [])

    def thresholds(self) -> dict:
        out = {"op": self.op, "value": self.value,
               "condition": {"column": self.column, "op": self.cond_op, "value": self.cond_value}}
        if self.where is not None:
            out["where"] = dict(self.where)
        if self.index is not None:
            out["index"] = list(self.index)
        return out

    def compute(self, data: dict) -> tuple:
        col = data[self.column]
        if col.dtype.kind not in NUMERIC_KINDS:
            raise NotApplicable("the condition needs a numeric column")
        if self.where is not None:
            mask = selection_mask(data, self.where)
            if col.ndim < 1 or col.shape[0] != mask.shape[0]:
                raise NotApplicable("the selection column and the condition column differ in length")
            col = col[mask]
        if self.index is not None:
            if col.ndim < 1:
                raise NotApplicable("an index selection needs an array with a first axis")
            col = col[_index_positions(self.index, col.shape[0])]
        if col.size == 0:
            raise NotApplicable("empty selection")
        _finite(col.astype(np.float64, copy=False))
        frac = float(np.mean(OPERATORS[self.cond_op](col, self.cond_value)))
        return _outcome(OPERATORS[self.op](frac, self.value)), {"rate": frac}


class CiExcludes(Leaf):
    name = "ci_excludes"
    _CHUNK = 4_000_000  # bootstrap matrix elements per chunk

    def __init__(self, table: dict, where: str) -> None:
        check_keys(
            table, where, ("pattern", "side", "value"),
            ("x", "stat", "q", "a", "b", "paired", "level", "replicates", "B", "seed") + _arg_options("x", "a", "b"),
        )
        self.side = get_str(table, "side", where)
        if self.side not in ("above", "below"):
            fail(join(where, "side"), "must be \"above\" or \"below\"")
        self.value = get_number(table, "value", where)
        self.level = get_number(table, "level", where, required=False, default=0.95, lo=0, hi=1, lo_open=True,
                                hi_open=True)
        self.x = self.a = self.b = None
        self.stat = self.q = None
        self.paired = False
        self.replicates: Optional[str] = None
        self.B = self.seed = None
        if "replicates" in table:
            self.replicates = get_str(table, "replicates", where)
            for key in ("x", "stat", "q", "a", "b", "paired", "B", "seed", "x_where", "x_index", "a_where", "a_index",
                        "b_where", "b_index"):
                if key in table:
                    fail(join(where, key), "not valid together with `replicates`")
            return
        self.B = get_int(table, "B", where, required=False, default=2000, lo=1)
        self.seed = get_int(table, "seed", where, required=False, default=0, lo=0)
        if "x" in table:
            for key in ("a", "b", "paired"):
                if key in table:
                    fail(join(where, key), "not valid together with `x`")
            self.x = Arg(table, "x", where)
            self.stat, self.q = _parse_stat(table, where)
        elif "a" in table and "b" in table:
            for key in ("stat", "q"):
                if key in table:
                    fail(join(where, key), "not valid with `a` and `b` (a difference of means)")
            self.a, self.b = Arg(table, "a", where), Arg(table, "b", where)
            self.paired = get_bool(table, "paired", where, False)
        else:
            fail(where, "needs `x` with `stat`, or `a` and `b`, or `replicates`")

    def args(self) -> list:
        return [arg for arg in (self.x, self.a, self.b) if arg is not None]

    def keys(self) -> list:
        if self.replicates is not None:
            return [self.replicates]
        return super().keys()

    def thresholds(self) -> dict:
        return {"side": self.side, "value": self.value, "level": self.level}

    def _chunks(self, n: int):
        step = max(1, self._CHUNK // max(1, n))
        done = 0
        while done < self.B:
            yield min(step, self.B - done)
            done += step

    def _replicates_bootstrap(self, data: dict) -> np.ndarray:
        rng = np.random.default_rng(self.seed)
        parts = []
        if self.x is not None:
            arr = np.ravel(self.x.get(data))
            if arr.size == 0:
                raise NotApplicable("empty selection")
            if arr.dtype.kind in NUMERIC_KINDS:
                arr = arr.astype(np.float64)
                _finite(arr)
            elif arr.dtype.kind != "b":
                raise NotApplicable("the statistic needs a numeric or bool selection")
            if self.stat == "std" and arr.size < 2:
                raise NotApplicable("std needs at least two values")
            sorted_x = np.sort(arr)
            for rows in self._chunks(sorted_x.size):
                idx = rng.integers(0, sorted_x.size, size=(rows, sorted_x.size))
                parts.append(_stat_rows(sorted_x[idx], self.stat, self.q))
        elif self.paired:
            fa, fb = _numeric_flat(self.a.get(data)), _numeric_flat(self.b.get(data))
            if fa.shape != fb.shape:
                raise NotApplicable("paired arguments differ in length")
            order = np.lexsort((fb, fa))  # pairs sorted lexicographically, resampled as pairs
            diff = (fa - fb)[order]
            for rows in self._chunks(diff.size):
                idx = rng.integers(0, diff.size, size=(rows, diff.size))
                parts.append(diff[idx].mean(axis=1))
        else:
            fa, fb = np.sort(_numeric_flat(self.a.get(data))), np.sort(_numeric_flat(self.b.get(data)))
            for rows in self._chunks(max(fa.size, fb.size)):
                ia = rng.integers(0, fa.size, size=(rows, fa.size))
                ib = rng.integers(0, fb.size, size=(rows, fb.size))
                parts.append(fa[ia].mean(axis=1) - fb[ib].mean(axis=1))
        return np.concatenate(parts)

    def compute(self, data: dict) -> tuple:
        if self.replicates is not None:
            reps = _numeric_flat(data[self.replicates])
        else:
            reps = self._replicates_bootstrap(data)
        _finite(reps)
        alpha = (1.0 - self.level) / 2.0
        lo, hi = (float(v) for v in np.quantile(reps, [alpha, 1.0 - alpha]))
        holds = lo > self.value if self.side == "above" else hi < self.value
        return _outcome(holds), {"ci_lo": lo, "ci_hi": hi}


class LargestTrue(Leaf):
    name = "largest_true"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "grid", "y", "op", "threshold", "compare_to", "cmp"),
                   _arg_options("y"))
        grid = table["grid"]
        if not isinstance(grid, list) or not grid or not all(is_finite_number(v) for v in grid):
            fail(join(where, "grid"), "must be a non-empty literal list of finite numbers")
        self.grid = np.asarray(grid, dtype=np.float64)
        self.y = Arg(table, "y", where)
        self.op = get_op(table, "op", where)
        self.threshold = get_number(table, "threshold", where)
        self.cmp = get_op(table, "cmp", where, ("==", ">=", "<="))
        ref = table["compare_to"]
        rwhere = join(where, "compare_to")
        if not isinstance(ref, dict):
            fail(rwhere, "must be a table")
        self.ref_y: Optional[str] = None
        self.ref_value: Optional[float] = None
        if "value" in ref:
            check_keys(ref, rwhere, ("value",))
            self.ref_value = get_number(ref, "value", rwhere)
        else:
            check_keys(ref, rwhere, ("y", "op", "threshold"))
            self.ref_y = get_str(ref, "y", rwhere)
            self.ref_op = get_op(ref, "op", rwhere)
            self.ref_threshold = get_number(ref, "threshold", rwhere)

    def args(self) -> list:
        return [self.y]

    def keys(self) -> list:
        return super().keys() + ([self.ref_y] if self.ref_y is not None else [])

    def thresholds(self) -> dict:
        out: dict = {"op": self.op, "threshold": self.threshold, "cmp": self.cmp, "grid": [float(g) for g in self.grid]}
        if self.ref_y is not None:
            out["compare_to"] = {"op": self.ref_op, "threshold": self.ref_threshold}
        else:
            out["compare_to"] = {"value": self.ref_value}
        return out

    def _largest(self, curve: np.ndarray, op: str, threshold: float) -> float:
        y = _numeric_flat(curve)
        if y.size != self.grid.size:
            raise NotApplicable("y and grid differ in length")
        qualifying = self.grid[np.asarray(OPERATORS[op](y, threshold), dtype=bool)]
        if qualifying.size == 0:
            raise NotApplicable("no grid value qualifies")
        return float(np.max(qualifying))

    def compute(self, data: dict) -> tuple:
        largest = self._largest(self.y.get(data), self.op, self.threshold)
        if self.ref_y is not None:
            reference = self._largest(data[self.ref_y], self.ref_op, self.ref_threshold)
        else:
            reference = float(self.ref_value)
        return _outcome(OPERATORS[self.cmp](largest, reference)), {"largest": largest, "reference": reference}


class Monotone(Leaf):
    name = "monotone"

    def __init__(self, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "x", "y", "direction"), ("strict", "tol") + _arg_options("x", "y"))
        self.x, self.y = Arg(table, "x", where), Arg(table, "y", where)
        self.direction = get_str(table, "direction", where)
        if self.direction not in ("increasing", "decreasing"):
            fail(join(where, "direction"), "must be \"increasing\" or \"decreasing\"")
        self.strict = get_bool(table, "strict", where, False)
        self.tol = get_number(table, "tol", where, required=False, default=0, lo=0)

    def args(self) -> list:
        return [self.x, self.y]

    def thresholds(self) -> dict:
        return {"direction": self.direction, "strict": self.strict, "tol": self.tol}

    def compute(self, data: dict) -> tuple:
        x, y = _numeric_flat(self.x.get(data)), _numeric_flat(self.y.get(data))
        if x.shape != y.shape:
            raise NotApplicable("x and y differ in length")
        if x.size < 2:
            raise NotApplicable("monotone needs at least two points")
        # R-30 (audit F6): ties in x are ordered against the direction (y descending for "increasing", ascending for
        # "decreasing"), so a difference inside a tie is a step against the direction and the outcome does not depend
        # on the row order.  lexsort sorts by its last key first.
        against = -y if self.direction == "increasing" else y
        y = y[np.lexsort((against, x))]
        steps = np.diff(y)
        if self.direction == "decreasing":
            steps = -steps
        # Largest step against the direction (negative when every step goes the right way).  Non-strict: allowed up to
        # `tol`; strict: the step must stay strictly inside `tol` (with tol = 0, strictly monotone).
        violation = float(np.max(-steps))
        ok = violation < self.tol if self.strict else violation <= self.tol
        return _outcome(ok), {"max_backward_step": violation}


_LEAVES = {cls.name: cls for cls in (Threshold, Difference, RatioBand, Within, Rate, CiExcludes, LargestTrue, Monotone)}


# --------------------------------------------------------------------------
# Combinators and the compiled pattern
# --------------------------------------------------------------------------

class Combinator:
    def __init__(self, name: str, table: dict, where: str) -> None:
        check_keys(table, where, ("pattern", "of"))
        parts = table["of"]
        if not isinstance(parts, list) or not parts:
            fail(join(where, "of"), "must be a non-empty list of pattern tables")
        self.name = name
        self.parts = [_build(part, f"{join(where, 'of')}[{i}]") for i, part in enumerate(parts)]

    def keys(self) -> list:
        out: list = []
        for part in self.parts:
            out.extend(part.keys())
        return out

    def combine(self, outcomes: list) -> str:
        if self.name == "all_of":
            if FAILS in outcomes:
                return FAILS
            return UNDEFINED if UNDEFINED in outcomes else HOLDS
        if HOLDS in outcomes:
            return HOLDS
        return UNDEFINED if UNDEFINED in outcomes else FAILS


def _build(table: Any, where: str):
    if not isinstance(table, dict):
        fail(where, "must be a pattern table")
    name = get_str(table, "pattern", where)
    if name in _LEAVES:
        return _LEAVES[name](table, where)
    if name in COMBINATOR_NAMES:
        return Combinator(name, table, where)
    fail(join(where, "pattern"), f"unknown pattern {name!r}; one of {', '.join(PATTERN_NAMES)}")


class Pattern:
    """A compiled pattern criterion."""

    def __init__(self, table: dict, where: str = "pattern") -> None:
        self.root = _build(table, where)
        seen: set = set()
        self.keys: list = [k for k in self.root.keys() if not (k in seen or seen.add(k))]

    def leaves(self) -> list:
        """``[(path, leaf)]``; parts of ``all_of`` / ``any_of`` are keyed by position path ("0", "1.0", ...)."""
        out: list = []

        def walk(node, path: str) -> None:
            if isinstance(node, Combinator):
                for i, part in enumerate(node.parts):
                    walk(part, f"{path}.{i}" if path else str(i))
            else:
                out.append((path, node))

        walk(self.root, "")
        return out

    def evaluate(self, data: dict, record: Optional[dict] = None) -> str:
        """HOLDS, FAILS or UNDEFINED.  Looks every referenced key up first (``KeyError`` for a missing one).

        ``record``, when given, receives ``path -> (outcome, statistics)`` for every leaf.
        """
        for key in self.keys:
            data[key]
        return self._eval(self.root, data, "", record)

    def _eval(self, node, data: dict, path: str, record: Optional[dict]) -> str:
        if isinstance(node, Combinator):
            outcomes = [
                self._eval(part, data, f"{path}.{i}" if path else str(i), record)
                for i, part in enumerate(node.parts)
            ]
            return node.combine(outcomes)
        try:
            outcome, stats = node.compute(data)
        except NotApplicable:
            outcome, stats = UNDEFINED, {}
        if record is not None:
            record[path] = (outcome, stats)
        return outcome

    def fn(self, data: dict) -> Optional[bool]:
        """Criterion function in the 0.3 convention: True, False or None (UNDEFINED)."""
        return _RETURN[self.evaluate(data)]


__all__ = [
    "CRITERION_KEYS", "FAILS", "HOLDS", "PATTERN_NAMES", "STATS", "UNDEFINED", "Pattern", "apply_stat",
]
