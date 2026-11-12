"""Evaluation harness for Kapi v0.3: criteria Q1 ... Q6, P4', R1, R2 (spec 0.5, delta 4.2 - 4.3).

``eval/harness.py`` (v0) and ``eval/harness_v02.py`` are left unchanged; this module reuses their detection and clearance
rules.  It contains no evaluation case and reads no file.

Results table: a list of dicts.  Every row has::

    case_id, set, faulty_verdict, faulty_flags (list), faulty_runs

and these fields, which depend on the set:

* ``set``: ``"E5"`` for the new independent set; ``"R-E1"`` ... ``"R-E4"`` for the regression sets (the v0 sets E1, E2, E3
  and the v0.2 set E4, re-run unchanged).
* E5 rows: ``case_type`` (``"W"`` identical minus, ``"U"`` unread change, ``"T"`` trap, ``"N"`` near-identical),
  ``expected_checks`` (list, faulty side), ``expected_verdict`` (informational, faulty side), ``fixed_verdict`` (``None``
  when the case has no fixed twin, as a trap may), ``fixed_flags``, ``fixed_runs``, optionally ``fixed_expected_verdict``
  and ``paired`` (True for a stochastic, False for a deterministic study; used only for the composition report).
* R rows: the v0.2 fields ``fault_type``, ``expected_checks``, ``fixed_verdict``, ``fixed_flags``, ``fixed_runs``.
* ``faulty_runs`` and ``fixed_runs``: a list of exactly two dicts ``{verdict, flags, body_sha256}`` per file, one per run
  (P4').  A missing or malformed list fails P4' for that file (fail closed).

Criteria (each reported as ``{value, numerator, denominator, threshold, outcome}`` with outcome "Tuttu", "Tutmadı" or
"not evaluated"):

* Q1  W faulty cases detected / all W faulty cases >= 0.90.  A W faulty case is detected iff its verdict is UNTESTED and
  ``K2_MINUS_IDENTICAL`` is raised.  Needs at least 5 W cases.
* Q2  every U faulty case is detected and none is UNTESTED (1.0).  Needs at least 4 U cases.
* Q3  every T case is NOT_FALSIFIABLE or UNDEFINED and not UNTESTED (1.0; verdict only, as written in delta 4.3).
  Needs at least 3 T cases.
* Q4  every N faulty case is detected and none is UNTESTED (1.0).  Needs at least 2 N cases.
* Q5  ``K2_MINUS_UNREAD`` is raised on >= 0.80 of the U faulty cases.  Needs at least 4 U cases.
* Q6  cleared E5 fixed twins / all E5 fixed twins >= 0.90 (not evaluated without a fixed twin).
* P4' each file of R and E5 is run twice, with the rule of 0.4 delta 4.3 (``harness_v02.run_passes``); pass rate 1.0.
* R1  every R faulty case is detected (1.0).    * R2  every R fixed twin is cleared (1.0).

Detection (delta 4.2): a U, T or N faulty case is detected iff its verdict is NOT_FALSIFIABLE or UNDEFINED and at least
one expected check is raised; an informational flag (``K2_MINUS_UNREAD``, ``BAD_RETURN``) never counts as an expected
check, so it is dropped from the list before matching (an empty list detects nothing).  A fixed twin is cleared iff its
verdict is FALSIFIABLE or WEAK (UNTESTED is not cleared).  R cases use spec 0.3 section 12.3 unchanged, so an R faulty
case that becomes UNTESTED is not detected.  A family such as ``HIGH_RATE`` matches any ``HIGH_RATE:<stream>``.
"""

from __future__ import annotations

from fractions import Fraction

from . import harness as v0
from . import harness_v02 as v02

TUTTU, TUTMADI, NOT_EVALUATED = v0.TUTTU, v0.TUTMADI, v0.NOT_EVALUATED

E5_SET = "E5"
R_SETS = ("R-E1", "R-E2", "R-E3", "R-E4")
SETS = (E5_SET,) + R_SETS
CASE_TYPES = ("W", "U", "T", "N")
IDENTICAL_FLAG = "K2_MINUS_IDENTICAL"
UNREAD_FLAG = "K2_MINUS_UNREAD"
INFORMATIONAL_FLAGS = (UNREAD_FLAG, "BAD_RETURN")
UNTESTED = "UNTESTED"
DETECTING_VERDICTS = v0.DETECTING_VERDICTS  # NOT_FALSIFIABLE, UNDEFINED
CLEARED_VERDICTS = v0.CLEARED_VERDICTS  # FALSIFIABLE, WEAK

MIN_CASES = {"Q1": ("W", 5), "Q2": ("U", 4), "Q3": ("T", 3), "Q4": ("N", 2), "Q5": ("U", 4)}
THRESHOLDS = {"Q1": 0.90, "Q2": 1.0, "Q3": 1.0, "Q4": 1.0, "Q5": 0.80, "Q6": 0.90, "P4prime": 1.0, "R1": 1.0, "R2": 1.0}
DISPLAY = {"P4prime": "P4'"}
ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "P4prime", "R1", "R2")


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
        if row["set"] == E5_SET and row.get("case_type") not in CASE_TYPES:
            raise ValueError(f"unknown case_type {row.get('case_type')!r} in case {row.get('case_id')!r}")


# --------------------------------------------------------------------------
# Detection and clearance (delta 4.2)
# --------------------------------------------------------------------------

def is_detected_w(row: dict) -> bool:
    """W faulty case: verdict UNTESTED and ``K2_MINUS_IDENTICAL`` raised."""
    return row["faulty_verdict"] == UNTESTED and IDENTICAL_FLAG in row["faulty_flags"]


def scored_checks(row: dict) -> list:
    """Expected checks that may count for detection: informational flags are dropped (delta 4.2)."""
    return [e for e in row["expected_checks"] if e not in INFORMATIONAL_FLAGS]


def is_detected_nf(row: dict) -> bool:
    """U, T or N faulty case: NOT_FALSIFIABLE/UNDEFINED and at least one scored expected check raised."""
    return row["faulty_verdict"] in DETECTING_VERDICTS and any(
        v0.check_raised(e, row["faulty_flags"]) for e in scored_checks(row)
    )


def is_detected(row: dict) -> bool:
    """Detection of an E5 faulty case by its type, or of an R faulty case by spec 0.3 section 12.3."""
    if row["set"] in R_SETS:
        return v0.is_detected(row)
    if row["case_type"] == "W":
        return is_detected_w(row)
    return is_detected_nf(row)


def is_cleared(row: dict) -> bool:
    """The fixed twin is FALSIFIABLE or WEAK (a missing twin is not cleared)."""
    return row.get("fixed_verdict") in CLEARED_VERDICTS


def has_fixed(row: dict) -> bool:
    return row.get("fixed_verdict") is not None


def not_untested(row: dict) -> bool:
    return row["faulty_verdict"] != UNTESTED


def t_case_ok(row: dict) -> bool:
    """Q3: NOT_FALSIFIABLE or UNDEFINED, and not UNTESTED."""
    return row["faulty_verdict"] in DETECTING_VERDICTS and row["faulty_verdict"] != UNTESTED


def p4prime_files(rows: list) -> list:
    """All ``runs`` lists of R and E5 files: the faulty file of every row and the fixed file of rows that have one."""
    files = []
    for row in rows:
        files.append(row.get("faulty_runs"))
        if has_fixed(row) or row["set"] in R_SETS:
            files.append(row.get("fixed_runs"))
    return files


# --------------------------------------------------------------------------
# Criteria
# --------------------------------------------------------------------------

def composition(e5: list) -> dict:
    """Informational: number of cases (and, if rows carry ``paired``, stochastic/deterministic cases) per type."""
    out = {}
    for t in CASE_TYPES:
        rows = [r for r in e5 if r["case_type"] == t]
        out[t] = {
            "cases": len(rows),
            "with_fixed_twin": sum(map(has_fixed, rows)),
            "stochastic": sum(1 for r in rows if r.get("paired") is True),
            "deterministic": sum(1 for r in rows if r.get("paired") is False),
        }
    return out


def evaluate_table(rows: list) -> dict:
    """Compute Q1 ... Q6, P4', R1, R2 from a results table."""
    _validate(rows)
    e5 = [r for r in rows if r["set"] == E5_SET]
    reg = [r for r in rows if r["set"] in R_SETS]
    by_type = {t: [r for r in e5 if r["case_type"] == t] for t in CASE_TYPES}
    fixed = [r for r in e5 if has_fixed(r)]
    files = p4prime_files(e5 + reg)

    def minimum(name: str) -> int:
        return MIN_CASES[name][1]

    w, u, t, n = (by_type[k] for k in CASE_TYPES)
    results = {
        "Q1": _result("Q1", sum(map(is_detected, w)), len(w), minimum("Q1")),
        "Q2": _result("Q2", sum(is_detected(r) and not_untested(r) for r in u), len(u), minimum("Q2")),
        "Q3": _result("Q3", sum(map(t_case_ok, t)), len(t), minimum("Q3")),
        "Q4": _result("Q4", sum(is_detected(r) and not_untested(r) for r in n), len(n), minimum("Q4")),
        "Q5": _result("Q5", sum(UNREAD_FLAG in r["faulty_flags"] for r in u), len(u), minimum("Q5")),
        "Q6": _result("Q6", sum(map(is_cleared, fixed)), len(fixed)),
        "P4prime": _result("P4prime", sum(map(v02.run_passes, files)), len(files)),
        "R1": _result("R1", sum(map(is_detected, reg)), len(reg)),
        "R2": _result("R2", sum(map(is_cleared, reg)), len(reg)),
    }
    return results


def bookkeeping(rows: list) -> dict:
    """Non-criterion bookkeeping: composition, trap detections and expected-verdict mismatches (informational)."""
    _validate(rows)
    e5 = [r for r in rows if r["set"] == E5_SET]
    fixed = [r for r in e5 if has_fixed(r)]
    return {
        "composition": composition(e5),
        "trap_cases_detected": sum(is_detected(r) for r in e5 if r["case_type"] == "T"),
        "expected_verdict_mismatches": sorted(
            r["case_id"] for r in e5 if r.get("expected_verdict") not in (None, r["faulty_verdict"])
        ),
        "fixed_expected_verdict_mismatches": sorted(
            r["case_id"] for r in fixed if r.get("fixed_expected_verdict") not in (None, r["fixed_verdict"])
        ),
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
