"""Evaluation harness for Kapi v0.2: criteria P1a, P1b, P1c, P2, P3, P4', P5, R1, R2 (spec 0.4, delta 4.2 - 4.3).

``eval/harness.py`` (v0) is left unchanged; this module reuses its detection and clearance rules.  It contains no
evaluation case and reads no file.

Results table: a list of dicts with the v0 fields::

    case_id, set, fault_type, expected_checks (list), faulty_verdict, faulty_flags (list), fixed_verdict,
    faulty_hash_runs, fixed_hash_runs

and these additional fields:

* ``set``: ``"E4"`` for the new independent set; ``"R-E1"``, ``"R-E2"`` or ``"R-E3"`` for the regression sets (the
  v0 sets E1, E2, E3 re-run unchanged).  The regression marker is therefore carried by ``set``; no separate field.
* ``fault_class`` (optional): ``"fp_inflation"`` marks the false-positive-inflation class (P1b).
* ``expect_fixed`` (optional): ``"WEAK"`` marks a fixed twin that is designed to be legitimately WEAK (P5).
* ``fixed_flags`` (list): flags of the fixed twin's first run (informational, not used by a criterion).
* ``faulty_runs`` and ``fixed_runs``: for each of the two files of the case, a list of exactly two dicts
  ``{verdict, flags, body_sha256}``, one per run (needed for P4').  A missing or malformed list fails P4' for
  that file (fail closed).

Criteria (E4 rows unless stated; every one is reported as ``{value, numerator, denominator, threshold, outcome}``
with outcome "Tuttu", "Tutmadı" or "not evaluated"):

* P1a  detected faulty / faulty >= 0.90.            * P1b  detected within ``fp_inflation`` >= 0.80.
* P1c  no E4 fault type has zero detections.        * P2   cleared fixed / fixed >= 0.90.
* P3   every E4 case expecting ``K6_LEAK_ATTEMPT`` is detected (1.0); none -> "not evaluated".
* P4'  each file of R and E4 is run twice: if run 1 contains ``K6_NONREPRODUCIBLE`` or ``NONDETERMINISTIC``, the file
  passes iff both runs contain every such flag of run 1 and have the same verdict; otherwise it passes iff both runs
  have the same non-empty ``body_sha256``.  Pass rate 1.0 (denominator: number of files).
* P5   among E4 pairs with ``expect_fixed == "WEAK"``, the fixed verdict is exactly WEAK in >= 0.80; fewer than four
  such pairs -> "not evaluated" (the counts are still reported).
* R1   every R faulty case is detected (1.0).       * R2   every R fixed twin is cleared (1.0).

Detection and clearance are unchanged from spec 0.3 section 12.3 (a family such as ``HIGH_RATE`` matches any
``HIGH_RATE:<stream>``).  An empty denominator gives "not evaluated".
"""

from __future__ import annotations

from fractions import Fraction

from . import harness as v0

TUTTU, TUTMADI, NOT_EVALUATED = v0.TUTTU, v0.TUTMADI, v0.NOT_EVALUATED

E4_SET = "E4"
R_SETS = ("R-E1", "R-E2", "R-E3")
SETS = (E4_SET,) + R_SETS
FP_CLASS = "fp_inflation"
WEAK_TWIN = "WEAK"
LEAK_CHECK = v0.LEAK_CHECK
NONREPRODUCIBILITY_FLAGS = ("K6_NONREPRODUCIBLE", "NONDETERMINISTIC")
MIN_WEAK_PAIRS = 4

THRESHOLDS = {"P1a": 0.90, "P1b": 0.80, "P1c": 1.0, "P2": 0.90, "P3": 1.0, "P4prime": 1.0, "P5": 0.80, "R1": 1.0, "R2": 1.0}
DISPLAY = {"P4prime": "P4'"}
ORDER = ("P1a", "P1b", "P1c", "P2", "P3", "P4prime", "P5", "R1", "R2")


def _result(name: str, numerator: int, denominator: int, min_denominator: int = 1) -> dict:
    threshold = THRESHOLDS[name]
    if denominator < min_denominator or denominator == 0:
        value = None if denominator == 0 else numerator / denominator
        return {"value": value, "numerator": numerator, "denominator": denominator,
                "threshold": threshold, "outcome": NOT_EVALUATED}
    ok = Fraction(numerator, denominator) >= Fraction(str(threshold))
    return {"value": numerator / denominator, "numerator": numerator, "denominator": denominator,
            "threshold": threshold, "outcome": TUTTU if ok else TUTMADI}


def _validate(rows: list) -> None:
    for row in rows:
        if row["set"] not in SETS:
            raise ValueError(f"unknown set {row['set']!r} in case {row.get('case_id')!r}")


def is_detected(row: dict) -> bool:
    """Spec 0.3 section 12.3 (unchanged)."""
    return v0.is_detected(row)


def is_cleared(row: dict) -> bool:
    """Spec 0.3 section 12.3 (unchanged)."""
    return v0.is_cleared(row)


def run_passes(runs) -> bool:
    """P4' rule for one file given its two runs ``{verdict, flags, body_sha256}`` (fail closed on malformed input)."""
    if not isinstance(runs, (list, tuple)) or len(runs) != 2:
        return False
    first, second = runs
    try:
        flags1, flags2 = set(first["flags"]), set(second["flags"])
        v1, v2 = first["verdict"], second["verdict"]
        h1, h2 = first["body_sha256"], second["body_sha256"]
    except (KeyError, TypeError):
        return False
    flagged = [f for f in NONREPRODUCIBILITY_FLAGS if f in flags1]
    if flagged:
        return all(f in flags2 for f in flagged) and v1 == v2 and v1 is not None
    return bool(h1) and h1 == h2


def p4prime_files(rows: list) -> list:
    """All ``runs`` lists of R and E4 files: two per row (faulty and fixed)."""
    return [row.get(key) for row in rows for key in ("faulty_runs", "fixed_runs")]


def e4_fault_types(e4: list) -> dict:
    """Map each E4 fault type to whether it has at least one detection (P1c)."""
    types: dict = {}
    for row in e4:
        types[row["fault_type"]] = types.get(row["fault_type"], False) or is_detected(row)
    return types


def evaluate_table(rows: list) -> dict:
    """Compute P1a, P1b, P1c, P2, P3, P4', P5, R1, R2 from a results table."""
    _validate(rows)
    e4 = [r for r in rows if r["set"] == E4_SET]
    reg = [r for r in rows if r["set"] in R_SETS]
    fp = [r for r in e4 if r.get("fault_class") == FP_CLASS]
    leak = [r for r in e4 if LEAK_CHECK in r["expected_checks"]]
    weak_pairs = [r for r in e4 if r.get("expect_fixed") == WEAK_TWIN]
    types = e4_fault_types(e4)
    files = p4prime_files(e4 + reg)
    return {
        "P1a": _result("P1a", sum(map(is_detected, e4)), len(e4)),
        "P1b": _result("P1b", sum(map(is_detected, fp)), len(fp)),
        "P1c": _result("P1c", sum(types.values()), len(types)),
        "P2": _result("P2", sum(map(is_cleared, e4)), len(e4)),
        "P3": _result("P3", sum(map(is_detected, leak)), len(leak)),
        "P4prime": _result("P4prime", sum(map(run_passes, files)), len(files)),
        "P5": _result("P5", sum(r["fixed_verdict"] == "WEAK" for r in weak_pairs), len(weak_pairs), MIN_WEAK_PAIRS),
        "R1": _result("R1", sum(map(is_detected, reg)), len(reg)),
        "R2": _result("R2", sum(map(is_cleared, reg)), len(reg)),
    }


def format_report(results: dict) -> str:
    """One line per criterion: name, outcome, counts, value, threshold."""
    lines = []
    for name in ORDER:
        r = results[name]
        value = "n/a" if r["value"] is None else f"{r['value']:.3f}"
        lines.append(
            f"{DISPLAY.get(name, name)}: {r['outcome']} ({r['numerator']}/{r['denominator']} = {value}, threshold {r['threshold']})"
        )
    return "\n".join(lines)
