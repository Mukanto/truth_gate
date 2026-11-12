"""Runner for the pre-registered Kapı v0.2 evaluation (spec 0.4, delta 4).  ``run_eval.py`` (v0) is untouched.

Usage (from the project root)::

    py -B evaluation/run_eval_v02.py --regression evaluation/cases/E1E3 evaluation/cases/E2 \\
        --sets evaluation/cases/E4 --out evaluation/results/RESULTS_v0_2.json

``--regression`` lists the v0 sets E1E3 and E2 (unchanged cases, re-run as the regression sets R-E1, R-E2, R-E3);
``--sets`` lists the new independent set E4.

Order of work:

1. Refuse to start if the output file already exists (exit 2).
2. Verify the freeze record ``FREEZE_v0_2.json`` (created by the main session at freeze time; the runner aborts if it is
   missing): every recorded file under ``kapi/``, ``eval/`` and ``spec/`` must have its recorded SHA-256, no unrecorded
   ``.py`` file may exist in ``kapi/`` or ``eval/``, and the recorded core hash must be reproduced (exit 2 otherwise).
3. Verify every case set against its ``CASES_SHA256.json`` and read its ``manifest.json`` (exit 2 otherwise).
4. Only then import the frozen ``kapi`` package and run ``run_gate(file, quick=False)`` twice on the faulty file and
   twice on the fixed file of every case.
5. Build the results table for ``eval/harness_v02.py``, evaluate P1a ... R2, write everything to ``--out`` (created
   exclusively, never overwritten) and print the report.

Manifest entries need ``case_id, set, fault_type, expected_checks, origin, faulty_file, fixed_file``; ``fault_class``
and ``expect_fixed`` are optional.  In a regression set ``set`` must be E1, E2 or E3 (stored as R-E1 ... R-E3 in the
table); in a ``--sets`` directory it must be E4.

Exit codes: 0 done, 2 integrity abort, 4 usage error.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import hash_cases  # noqa: E402  (same directory)

FREEZE_NAME = "FREEZE_v0_2.json"
DEFAULT_FREEZE = os.path.join(ROOT, FREEZE_NAME)
REQUIRED_MANIFEST_KEYS = ("case_id", "set", "fault_type", "expected_checks", "origin", "faulty_file", "fixed_file")
REGRESSION_SETS = ("E1", "E2", "E3")
CORE_PREFIXES = ("kapi/", "eval/", "spec/")


class Abort(Exception):
    """Integrity problem: the run must not start (or continue)."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_freeze(freeze_path: str, root: str) -> str:
    """Check the frozen files against ``FREEZE_v0_2.json``.  Returns the recorded core hash.

    The record has the layout of ``FREEZE_v0.json``: ``{"files": {relative posix path: sha256}, "core_sha256": ...}`` where
    ``core_sha256`` is the SHA-256 of the concatenated hex hashes of the core files (``kapi/``, ``eval/``, ``spec/``)
    in sorted path order.
    """
    if not os.path.isfile(freeze_path):
        raise Abort(f"freeze file is missing: {freeze_path}")
    try:
        with open(freeze_path, "r", encoding="utf-8") as fh:
            freeze = json.load(fh)
        files = freeze["files"]
        core_recorded = freeze["core_sha256"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Abort(f"cannot read freeze file {freeze_path}: {type(exc).__name__}")
    core = sorted(p for p in files if p.startswith(CORE_PREFIXES))
    if not any(p.startswith("kapi/") for p in core) or not any(p.startswith("eval/") for p in core) or not any(
        p.startswith("spec/") for p in core
    ):
        raise Abort("freeze file must list files under kapi/, eval/ and spec/")
    problems = []
    for rel in core:
        path = os.path.join(root, *rel.split("/"))
        try:
            with open(path, "rb") as fh:
                actual = _sha256_bytes(fh.read())
        except OSError:
            problems.append(f"missing: {rel}")
            continue
        if actual != files[rel]:
            problems.append(f"hash mismatch: {rel}")
    for sub in ("kapi", "eval"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, sub)):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in filenames:
                rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
                if name.endswith(".py") and rel not in files:
                    problems.append(f"unrecorded file: {rel}")
    if problems:
        raise Abort("frozen files changed: " + "; ".join(problems))
    core_actual = _sha256_bytes("".join(files[p] for p in core).encode("utf-8"))
    if core_actual != core_recorded:
        raise Abort("core hash recorded in the freeze file is not reproduced from its own file hashes")
    return core_recorded


def load_set(set_dir: str, allowed_sets: tuple) -> tuple:
    """Verify one case set and return ``(manifest, hash_file_sha256)``."""
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
    seen = set()
    for entry in manifest:
        missing = [k for k in REQUIRED_MANIFEST_KEYS if not isinstance(entry, dict) or k not in entry]
        if missing:
            raise Abort(f"manifest entry in {set_dir} lacks {missing}")
        if entry["set"] not in allowed_sets:
            raise Abort(f"manifest entry {entry['case_id']} has set {entry['set']!r}; allowed here: {list(allowed_sets)}")
        if not isinstance(entry["expected_checks"], list) or not entry["expected_checks"]:
            raise Abort(f"manifest entry {entry['case_id']} has no expected_checks")
        if entry["case_id"] in seen:
            raise Abort(f"duplicate case_id {entry['case_id']} in {set_dir}")
        seen.add(entry["case_id"])
        for key in ("faulty_file", "fixed_file"):
            if entry[key] not in recorded:
                raise Abort(f"{entry['case_id']}: {key} {entry[key]!r} is not a hashed file of {set_dir}")
    with open(os.path.join(set_dir, hash_cases.HASH_FILE), "rb") as fh:
        hash_file_sha = _sha256_bytes(fh.read())
    return manifest, hash_file_sha


def _flags_of(body: dict) -> list:
    flags = set()
    for comp in body.get("components", []):
        flags.update(comp.get("flags", []))
    for flag in body.get("study_flags", []):
        flags.add(flag if isinstance(flag, str) else json.dumps(flag, sort_keys=True))
    return sorted(flags)


def _run_once(run_gate, path: str) -> dict:
    """One run; a runner error is recorded (verdict UNDEFINED, flag RUNNER_ERROR, no hash), not hidden."""
    start = time.perf_counter()
    try:
        env = run_gate(path, quick=False)
        body = env["body"]
        return {"verdict": body["verdict"], "flags": _flags_of(body), "body_sha256": env["body_sha256"],
                "seconds": round(time.perf_counter() - start, 3)}
    except Exception as exc:
        return {"verdict": "UNDEFINED", "flags": ["RUNNER_ERROR"], "body_sha256": None,
                "seconds": round(time.perf_counter() - start, 3), "runner_error": type(exc).__name__}


def _side(run_gate, path: str, rel: str) -> dict:
    with open(path, "rb") as fh:
        file_sha = _sha256_bytes(fh.read())
    return {"file": rel, "file_sha256": file_sha, "runs": [_run_once(run_gate, path), _run_once(run_gate, path)]}


def _harness_runs(side: dict) -> list:
    return [{"verdict": r["verdict"], "flags": list(r["flags"]), "body_sha256": r["body_sha256"]} for r in side["runs"]]


def run_cases(manifest: list, set_dir: str, run_gate, regression: bool) -> list:
    """Run both files of every case twice and build the harness rows."""
    records = []
    for entry in manifest:
        faulty = _side(run_gate, os.path.join(set_dir, entry["faulty_file"]), entry["faulty_file"])
        fixed = _side(run_gate, os.path.join(set_dir, entry["fixed_file"]), entry["fixed_file"])
        table_set = f"R-{entry['set']}" if regression else entry["set"]
        row = {
            "case_id": entry["case_id"],
            "set": table_set,
            "fault_type": entry["fault_type"],
            "expected_checks": list(entry["expected_checks"]),
            "faulty_verdict": faulty["runs"][0]["verdict"],
            "faulty_flags": list(faulty["runs"][0]["flags"]),
            "fixed_verdict": fixed["runs"][0]["verdict"],
            "fixed_flags": list(fixed["runs"][0]["flags"]),
            "faulty_hash_runs": [r["body_sha256"] for r in faulty["runs"]],
            "fixed_hash_runs": [r["body_sha256"] for r in fixed["runs"]],
            "faulty_runs": _harness_runs(faulty),
            "fixed_runs": _harness_runs(fixed),
        }
        for key in ("fault_class", "expect_fixed"):
            if entry.get(key) is not None:
                row[key] = entry[key]
        records.append({"case_id": entry["case_id"], "set": table_set, "fault_type": entry["fault_type"],
                        "origin": entry["origin"], "expected_checks": list(entry["expected_checks"]),
                        "faulty": faulty, "fixed": fixed, "table_row": row})
    return records


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="run_eval_v02", description="Run the pre-registered Kapı v0.2 evaluation.")
    parser.add_argument("--regression", nargs="+", required=True, help="regression case sets (the v0 sets E1E3 and E2)")
    parser.add_argument("--sets", nargs="+", required=True, help="new case sets (E4)")
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
        loaded = []
        for set_dir in args.regression:
            manifest, hash_file_sha = load_set(set_dir, REGRESSION_SETS)
            loaded.append((set_dir, manifest, hash_file_sha, True))
        for set_dir in args.sets:
            manifest, hash_file_sha = load_set(set_dir, ("E4",))
            loaded.append((set_dir, manifest, hash_file_sha, False))
        all_ids = [e["case_id"] for _d, m, _h, _r in loaded for e in m]
        if len(all_ids) != len(set(all_ids)):
            raise Abort("duplicate case_id across case sets")
    except Abort as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2

    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import kapi  # the frozen package
    from eval import harness_v02

    records = []
    for set_dir, manifest, _hash_file_sha, regression in loaded:
        records.extend(run_cases(manifest, set_dir, kapi.run_gate, regression))
    rows = [r["table_row"] for r in records]
    criteria = harness_v02.evaluate_table(rows)
    result = {
        "kapi_version": kapi.__version__,
        "spec_version": kapi.SPEC_VERSION,
        "freeze_core_sha256": core_sha,
        "case_sets": {d: {"cases_sha256_file_sha256": h, "n_cases": len(m), "regression": r} for d, m, h, r in loaded},
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cases": records,
        "table": rows,
        "criteria": criteria,
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
    print(harness_v02.format_report(criteria))
    print(f"results written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
