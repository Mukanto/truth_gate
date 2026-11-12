"""Evaluation harness for the pre-registered criteria P1a ... P4 (spec sections 12.3 - 12.5).

This module is NOT part of the ``kapi`` package and contains no evaluation case.  It only
computes the primary criteria from a results table.

A results table is a list of dicts with the fields::

    case_id, set ("E1"|"E2"|"E3"), fault_type, expected_checks (list),
    faulty_verdict, faulty_flags (list), fixed_verdict,
    faulty_hash_runs (list of 2 hashes), fixed_hash_runs (list of 2 hashes)

Interpretation choices (spec section 12 leaves them open; the strict reading is used):

* *Flag match.* An expected check is "raised" if it equals a raised flag, or is the prefix of a
  parametrised flag (``HIGH_RATE`` matches ``HIGH_RATE:control:x``).
* *P1c types.* E2 rows count under their ``fault_type``; E1 and E3 rows count under every one of
  their expected checks.  A type is detected if at least one detected row (spec 12.3) carries it.
  P1c holds when every type has a detection.  An empty table is "not evaluated".
* *P4 denominator.* Each case contributes two runs-pairs (faulty and fixed twin); the denominator
  is therefore twice the number of rows.  A pair that does not consist of exactly two equal,
  non-empty hashes counts as not identical.
* *Baselines* (12.5) are idealised: the hypothetical gate emits its constant verdict and, for the
  faulty version, raises exactly the expected checks, so that only the verdict decides.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional

TUTTU = "Tuttu"
TUTMADI = "Tutmadı"
NOT_EVALUATED = "not evaluated"

DETECTING_VERDICTS = ("NOT_FALSIFIABLE", "UNDEFINED")
CLEARED_VERDICTS = ("FALSIFIABLE", "WEAK")
SETS = ("E1", "E2", "E3")
LEAK_CHECK = "K6_LEAK_ATTEMPT"

THRESHOLDS = {"P1a": 0.90, "P1b": 0.80, "P1c": 1.0, "P2a": 0.90, "P2b": 0.80, "P3": 1.0, "P4": 1.0}


def check_raised(expected: str, flags) -> bool:
    """True if ``expected`` equals a raised flag or is the prefix of a parametrised flag."""
    return any(f == expected or f.startswith(expected + ":") for f in flags)


def is_detected(row: dict) -> bool:
    """Spec 12.3: verdict NOT_FALSIFIABLE/UNDEFINED and at least one expected check raised."""
    return row["faulty_verdict"] in DETECTING_VERDICTS and any(
        check_raised(e, row["faulty_flags"]) for e in row["expected_checks"]
    )


def is_cleared(row: dict) -> bool:
    """Spec 12.3: the fixed twin is FALSIFIABLE or WEAK."""
    return row["fixed_verdict"] in CLEARED_VERDICTS


def _identical_pair(pair) -> bool:
    return isinstance(pair, (list, tuple)) and len(pair) == 2 and bool(pair[0]) and pair[0] == pair[1]


def _result(name: str, numerator: int, denominator: int) -> dict:
    threshold = THRESHOLDS[name]
    if denominator == 0:
        return {"value": None, "numerator": 0, "denominator": 0, "threshold": threshold, "outcome": NOT_EVALUATED}
    ok = Fraction(numerator, denominator) >= Fraction(str(threshold))
    return {
        "value": numerator / denominator,
        "numerator": numerator,
        "denominator": denominator,
        "threshold": threshold,
        "outcome": TUTTU if ok else TUTMADI,
    }


def _validate(rows: list) -> None:
    for row in rows:
        if row["set"] not in SETS:
            raise ValueError(f"unknown set {row['set']!r} in case {row.get('case_id')!r}")


def fault_types(rows: list) -> dict:
    """Map each P1c type to whether it has at least one detection."""
    types: dict = {}
    for row in rows:
        detected = is_detected(row)
        if row["set"] == "E2":
            keys = [f"E2:{row['fault_type']}"]
        else:
            keys = [f"check:{e}" for e in row["expected_checks"]]
        for key in keys:
            types[key] = types.get(key, False) or detected
    return types


def evaluate_table(rows: list) -> dict:
    """Compute P1a, P1b, P1c, P2a, P2b, P3, P4 (spec 12.4) from a results table."""
    _validate(rows)
    e2 = [r for r in rows if r["set"] == "E2"]
    types = fault_types(rows)
    leak_rows = [r for r in rows if LEAK_CHECK in r["expected_checks"]]
    pairs = [p for r in rows for p in (r["faulty_hash_runs"], r["fixed_hash_runs"])]
    return {
        "P1a": _result("P1a", sum(map(is_detected, rows)), len(rows)),
        "P1b": _result("P1b", sum(map(is_detected, e2)), len(e2)),
        "P1c": _result("P1c", sum(types.values()), len(types)),
        "P2a": _result("P2a", sum(map(is_cleared, rows)), len(rows)),
        "P2b": _result("P2b", sum(map(is_cleared, e2)), len(e2)),
        "P3": _result("P3", sum(map(is_detected, leak_rows)), len(leak_rows)),
        "P4": _result("P4", sum(map(_identical_pair, pairs)), len(pairs)),
    }


def constant_gate_table(rows: list, verdict: str) -> list:
    """The table a gate that always answers ``verdict`` would produce (spec 12.5, idealised)."""
    out = []
    for row in rows:
        clone = dict(row)
        clone["faulty_verdict"] = verdict
        clone["faulty_flags"] = list(row["expected_checks"])
        clone["fixed_verdict"] = verdict
        clone["faulty_hash_runs"] = ["h", "h"]
        clone["fixed_hash_runs"] = ["h", "h"]
        out.append(clone)
    return out


def meets_p1(results: dict) -> bool:
    """P1 holds if P1a is Tuttu and every evaluated P1b / P1c is Tuttu."""
    return results["P1a"]["outcome"] == TUTTU and all(
        results[k]["outcome"] in (TUTTU, NOT_EVALUATED) for k in ("P1b", "P1c")
    )


def meets_p2(results: dict) -> bool:
    """P2 holds if P2a is Tuttu and P2b is Tuttu or not evaluated."""
    return results["P2a"]["outcome"] == TUTTU and results["P2b"]["outcome"] in (TUTTU, NOT_EVALUATED)


def baselines(rows: list) -> dict:
    """Reference baselines of spec 12.5 computed on the given table."""
    out = {}
    for name, verdict in (("always_not_falsifiable", "NOT_FALSIFIABLE"), ("always_falsifiable", "FALSIFIABLE")):
        res = evaluate_table(constant_gate_table(rows, verdict))
        out[name] = {"criteria": res, "meets_P1": meets_p1(res), "meets_P2": meets_p2(res)}
    return out


def format_report(results: dict) -> str:
    """One line per criterion: name, value, counts, threshold, outcome."""
    lines = []
    for name in ("P1a", "P1b", "P1c", "P2a", "P2b", "P3", "P4"):
        r = results[name]
        value = "n/a" if r["value"] is None else f"{r['value']:.3f}"
        lines.append(f"{name}: {r['outcome']} ({r['numerator']}/{r['denominator']} = {value}, threshold {r['threshold']})")
    return "\n".join(lines)
