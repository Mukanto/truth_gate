"""Runner for the pre-registered Kapı v0.3 evaluation (spec 0.5, delta 4).  The v0 and v0.2 runners are untouched.

Usage (from the project root)::

    py -B evaluation/run_eval_v03.py --regression evaluation/cases/E1E3 evaluation/cases/E2 evaluation/cases/E4 \\
        --sets evaluation/cases/E5 --out evaluation/results/RESULTS_v0_3.json

``--regression`` lists the regression sets R (E1E3, E2 and E4, unchanged cases, re-run as R-E1 ... R-E4); ``--sets`` lists
the new independent set E5.

Order of work:

1. Refuse to start if the output file already exists (exit 2).
2. Verify the freeze record ``FREEZE_v0_3.json`` (created by the main session at freeze time; the runner aborts if it is
   missing) with the same rules as the v0.2 runner: every recorded file under ``kapi/``, ``eval/`` and ``spec/`` must have
   its recorded SHA-256, no unrecorded ``.py`` file may exist in ``kapi/`` or ``eval/``, and the recorded core hash must
   be reproduced (exit 2 otherwise).
3. Verify every case set against its ``CASES_SHA256.json`` and read its ``manifest.json`` (exit 2 otherwise).
4. Only then import the frozen ``kapi`` package and run ``run_gate(file, quick=False)`` twice on every file.
5. Build the results table for ``eval/harness_v03.py``, evaluate Q1 ... R2, write everything to ``--out`` (created
   exclusively, never overwritten) and print the report.

Manifest formats:

* R sets: as for the v0.2 runner, one entry per case with ``case_id, set, fault_type, expected_checks, origin,
  faulty_file, fixed_file`` (and optionally ``fault_class``, ``expect_fixed``).  ``set`` must be E1, E2, E3 or E4.
* E5: one entry per FILE with ``case_id``, ``case_type`` (W, U, T or N), ``role`` (``"faulty"`` or ``"fixed"``),
  ``expected_verdict``, ``expected_checks`` and ``file``.  A case needs exactly one faulty entry and at most one fixed entry (a trap
  may have no fixed twin); ``case_type`` must agree within a case; a faulty entry needs a non-empty ``expected_checks``.
  The table row of a case takes ``expected_checks`` and ``expected_verdict`` from the faulty entry and
  ``fixed_expected_verdict`` from the fixed entry.

Exit codes: 0 done, 2 integrity abort, 4 usage error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import hash_cases  # noqa: E402  (same directory)
import run_eval_v02 as base  # noqa: E402  (frozen v0.2 runner, reused unchanged)

Abort = base.Abort
FREEZE_NAME = "FREEZE_v0_3.json"
DEFAULT_FREEZE = os.path.join(ROOT, FREEZE_NAME)
REGRESSION_SETS = ("E1", "E2", "E3", "E4")
CASE_TYPES = ("W", "U", "T", "N")
ROLES = ("faulty", "fixed")
VERDICT_NAMES = ("FALSIFIABLE", "WEAK", "UNTESTED", "NOT_FALSIFIABLE", "UNDEFINED")
REQUIRED_E5_KEYS = ("case_id", "case_type", "role", "expected_verdict", "expected_checks", "file")


def verify_freeze(freeze_path: str, root: str) -> str:
    """Same checks as the v0.2 runner (``FREEZE_v0_3.json`` has the layout of ``FREEZE_v0_2.json``)."""
    return base.verify_freeze(freeze_path, root)


def load_regression_set(set_dir: str) -> tuple:
    """Verify one R case set and return ``(manifest, hash_file_sha256)``."""
    return base.load_set(set_dir, REGRESSION_SETS)


def load_e5_set(set_dir: str) -> tuple:
    """Verify one E5 case set and return ``(cases, hash_file_sha256)``; ``cases`` groups the file entries by case."""
    if not os.path.isdir(set_dir):
        raise Abort(f"case set is not a directory: {set_dir}")
    problems = hash_cases.verify_set(set_dir)
    if problems:
        raise Abort(f"case set {set_dir} failed hash verification: " + "; ".join(problems))
    try:
        with open(os.path.join(set_dir, "manifest.json"), "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Abort(f"cannot read manifest of {set_dir}: {type(exc).__name__}")
    if not isinstance(manifest, list) or not manifest:
        raise Abort(f"manifest of {set_dir} must be a non-empty list")
    recorded = set(hash_cases.list_set_files(set_dir))
    cases: dict = {}
    for entry in manifest:
        missing = [k for k in REQUIRED_E5_KEYS if not isinstance(entry, dict) or k not in entry]
        if missing:
            raise Abort(f"manifest entry in {set_dir} lacks {missing}")
        cid = entry["case_id"]
        if entry["case_type"] not in CASE_TYPES:
            raise Abort(f"{cid}: case_type {entry['case_type']!r} is not one of {list(CASE_TYPES)}")
        if entry["role"] not in ROLES:
            raise Abort(f"{cid}: role {entry['role']!r} is not one of {list(ROLES)}")
        if entry["expected_verdict"] not in VERDICT_NAMES:
            raise Abort(f"{cid}: expected_verdict {entry['expected_verdict']!r} is not a verdict")
        if not isinstance(entry["expected_checks"], list) or (entry["role"] == "faulty" and not entry["expected_checks"]):
            raise Abort(f"{cid}: expected_checks must be a list (non-empty for the faulty file)")
        if entry["file"] not in recorded:
            raise Abort(f"{cid}: file {entry['file']!r} is not a hashed file of {set_dir}")
        case = cases.setdefault(cid, {"case_type": entry["case_type"], "faulty": None, "fixed": None})
        if case["case_type"] != entry["case_type"]:
            raise Abort(f"{cid}: case_type differs between the files of the case")
        if case[entry["role"]] is not None:
            raise Abort(f"{cid}: more than one {entry['role']} entry")
        case[entry["role"]] = entry
    for cid, case in cases.items():
        if case["faulty"] is None:
            raise Abort(f"{cid}: no faulty entry")
    files = [e["file"] for c in cases.values() for e in (c["faulty"], c["fixed"]) if e is not None]
    if len(files) != len(set(files)):
        raise Abort(f"a file is listed twice in the manifest of {set_dir}")
    with open(os.path.join(set_dir, hash_cases.HASH_FILE), "rb") as fh:
        hash_file_sha = base._sha256_bytes(fh.read())
    return cases, hash_file_sha


class _PairedSpy:
    """Wraps ``run_gate`` and remembers ``minus_check.paired`` of the last certificate (composition report only)."""

    def __init__(self, run_gate):
        self.run_gate = run_gate
        self.paired = None

    def __call__(self, path, quick=False):
        envelope = self.run_gate(path, quick=quick)
        try:
            self.paired = envelope["body"]["components"][0]["minus_check"]["paired"]
        except (KeyError, IndexError, TypeError):
            self.paired = None
        return envelope


def run_e5_cases(cases: dict, set_dir: str, run_gate) -> list:
    """Run both files (where present) of every E5 case twice and build the harness rows."""
    records = []
    for cid, case in cases.items():
        spy = _PairedSpy(run_gate)
        faulty = base._side(spy, os.path.join(set_dir, case["faulty"]["file"]), case["faulty"]["file"])
        paired = spy.paired
        fixed = None
        if case["fixed"] is not None:
            fixed = base._side(run_gate, os.path.join(set_dir, case["fixed"]["file"]), case["fixed"]["file"])
        row = {
            "case_id": cid,
            "set": "E5",
            "case_type": case["case_type"],
            "expected_checks": list(case["faulty"]["expected_checks"]),
            "expected_verdict": case["faulty"]["expected_verdict"],
            "paired": paired,
            "faulty_verdict": faulty["runs"][0]["verdict"],
            "faulty_flags": list(faulty["runs"][0]["flags"]),
            "faulty_hash_runs": [r["body_sha256"] for r in faulty["runs"]],
            "faulty_runs": base._harness_runs(faulty),
            "fixed_verdict": None,
            "fixed_flags": [],
            "fixed_hash_runs": [],
            "fixed_runs": None,
        }
        if fixed is not None:
            row.update(
                fixed_verdict=fixed["runs"][0]["verdict"],
                fixed_flags=list(fixed["runs"][0]["flags"]),
                fixed_hash_runs=[r["body_sha256"] for r in fixed["runs"]],
                fixed_runs=base._harness_runs(fixed),
                fixed_expected_verdict=case["fixed"]["expected_verdict"],
            )
        records.append({"case_id": cid, "set": "E5", "case_type": case["case_type"], "faulty": faulty, "fixed": fixed,
                        "table_row": row})
    return records


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="run_eval_v03", description="Run the pre-registered Kapı v0.3 evaluation.")
    parser.add_argument("--regression", nargs="+", required=True, help="regression case sets (E1E3, E2 and E4)")
    parser.add_argument("--sets", nargs="+", required=True, help="new case sets (E5)")
    parser.add_argument("--out", required=True, help="results JSON to create (never overwritten)")
    parser.add_argument("--freeze", default=DEFAULT_FREEZE, help=f"freeze record (default: project {FREEZE_NAME})")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 4 if exc.code else 0

    try:
        if os.path.exists(args.out):
            raise Abort(f"output file already exists: {args.out}")
        core_sha = verify_freeze(args.freeze, ROOT)
        loaded = []  # (set_dir, manifest or cases, hash_file_sha, regression)
        for set_dir in args.regression:
            manifest, hash_file_sha = load_regression_set(set_dir)
            loaded.append((set_dir, manifest, hash_file_sha, True))
        for set_dir in args.sets:
            cases, hash_file_sha = load_e5_set(set_dir)
            loaded.append((set_dir, cases, hash_file_sha, False))
        all_ids = [e["case_id"] for _d, m, _h, reg in loaded if reg for e in m]
        all_ids += [cid for _d, c, _h, reg in loaded if not reg for cid in c]
        if len(all_ids) != len(set(all_ids)):
            raise Abort("duplicate case_id across case sets")
    except Abort as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2

    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import kapi  # the frozen package
    from eval import harness_v03

    records = []
    for set_dir, content, _hash_file_sha, regression in loaded:
        if regression:
            records.extend(base.run_cases(content, set_dir, kapi.run_gate, True))
        else:
            records.extend(run_e5_cases(content, set_dir, kapi.run_gate))
    rows = [r["table_row"] for r in records]
    criteria = harness_v03.evaluate_table(rows)
    result = {
        "kapi_version": kapi.__version__,
        "spec_version": kapi.SPEC_VERSION,
        "freeze_core_sha256": core_sha,
        "case_sets": {d: {"cases_sha256_file_sha256": h, "n_cases": len(c), "regression": r} for d, c, h, r in loaded},
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cases": records,
        "table": rows,
        "criteria": criteria,
        "bookkeeping": harness_v03.bookkeeping(rows),
    }
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    try:
        with open(args.out, "x", encoding="utf-8", newline="\n") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except FileExistsError:
        print(f"ABORT: output file already exists: {args.out}", file=sys.stderr)
        return 2
    print(harness_v03.format_report(criteria))
    print(f"results written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
