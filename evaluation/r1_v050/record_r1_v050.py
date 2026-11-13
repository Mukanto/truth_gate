#!/usr/bin/env python3
"""Record the official R1 run of Truth_Gate 0.5.0 (spec 0.7, section 6, step R1; post-freeze decision R-4).

Runs, in full mode, one check at a time, the gate of tag ``v0.5.0`` on the 267 studies of the frozen 0.4.1 baseline
(the 159 studies of Phase A criterion A1 and the 108 Phase B files): the same paths in the same order as
``evaluation/baseline_v041/STUDIES_V041.json``.  Before anything runs, the script

* checks that the worktree HEAD is the commit of the tag and that the worktree is clean,
* verifies ``evaluation/FREEZE_BASELINE_V041.json`` with ``protocol/tools/freeze.py verify`` (the frozen baseline index,
  baseline certificates, ``compare_r1.py`` and the baseline recorder), and
* checks the SHA-256 of every study file against the baseline index (any difference stops the run).

Every check is ``python -m truth_gate check <repo-relative path> --out <certificate>`` run from the repository root
(the working directory and path convention of ``record_baseline_v041.py``, so module paths in certificates are
comparable with the baseline).  The worktree of the tag is put on ``PYTHONPATH`` and, because ``-m`` puts the working
directory ahead of ``PYTHONPATH``, also first on ``sys.path`` by a small bootstrap that then asserts that
``truth_gate`` was imported from the worktree (the working tree of the repository is not the tag).

The worktree is created by the designer (``git worktree add --detach <DIR> v0.5.0``); this script checks that its HEAD
is the commit of the tag and that it is clean.

Output (never overwritten; the script refuses to run if ``STUDIES_V050.json`` exists), in
``evaluation/r1_v050/``:

* ``certs/<path with / replaced by __>.json``: the certificate envelope exactly as the tool wrote it (the file names
  that ``compare_r1.py`` pairs with the baseline ``certs/``);
* ``STUDIES_V050.json``: per study: set (``A1`` or ``phase_b``), path, study SHA-256, certificate file, certificate
  SHA-256 (of the file), verdict, exit code, wall seconds, worktree HEAD.

Usage (from anywhere)::

    py evaluation/r1_v050/record_r1_v050.py --worktree DIR --scratch DIR [--timeout 3600]

Afterwards, the comparison needs the ``certs`` folder itself as ``NEWDIR`` (``compare_r1.py`` looks for
``<NEWDIR>/<path with / replaced by __>.json``)::

    py evaluation/baseline_v041/compare_r1.py compare evaluation/r1_v050/certs [--report FILE]

Test-only options (never used in the official recording): ``--limit N`` records only the first N studies and writes
``STUDIES_V050_PARTIAL.json``; ``--tag TAG`` replaces ``v0.5.0``.  Both require ``--out-dir DIR``, a folder outside the
repository that receives ``certs/`` and the index instead of ``evaluation/r1_v050/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EVALUATION = os.path.join(ROOT, "evaluation")
CERT_DIR = os.path.join(HERE, "certs")
INDEX_NAME = "STUDIES_V050.json"
INDEX = os.path.join(HERE, INDEX_NAME)
BASELINE_DIR = os.path.join(EVALUATION, "baseline_v041")
BASELINE_INDEX = os.path.join(BASELINE_DIR, "STUDIES_V041.json")
FREEZE_BASELINE = os.path.join(EVALUATION, "FREEZE_BASELINE_V041.json")
FREEZE_TOOL = os.path.join(ROOT, "protocol", "tools", "freeze.py")
DEFAULT_TAG = "v0.5.0"
TAG = DEFAULT_TAG
TOOL_VERSION = "0.5.0"

BOOTSTRAP = r"""
import os, runpy, sys
worktree = os.environ["TRUTH_GATE_WORKTREE"]
cwd = os.getcwd()
sys.path[0] = cwd
sys.path.insert(0, worktree)
import truth_gate
inside = os.path.normcase(os.path.realpath(truth_gate.__file__)).startswith(
    os.path.normcase(os.path.realpath(worktree)) + os.sep)
assert inside, "truth_gate imported from " + truth_gate.__file__ + ", not from the worktree"
sys.argv = ["truth_gate"] + sys.argv[1:]
runpy.run_module("truth_gate", run_name="__main__", alter_sys=True)
"""


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def cert_name(rel_path: str) -> str:
    return rel_path.replace("/", "__") + ".json"


def git(*args: str, cwd: str = ROOT) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def verify_worktree(worktree: str) -> str:
    tag_commit = git("rev-parse", f"{TAG}^{{commit}}")
    head = git("-C", worktree, "rev-parse", "HEAD")
    if head != tag_commit:
        raise SystemExit(f"worktree {worktree} is at {head}, but {TAG} is {tag_commit}: refusing to run")
    if git("-C", worktree, "status", "--porcelain"):
        raise SystemExit(f"worktree {worktree} is not clean: refusing to run")
    print(f"worktree ok: {worktree} is at {TAG} ({head[:12]})")
    return head


def baseline_studies() -> list:
    proc = subprocess.run([sys.executable, FREEZE_TOOL, "verify", FREEZE_BASELINE], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout + proc.stderr)
        raise SystemExit("baseline freeze verification failed: refusing to run")
    print("baseline freeze verified (FREEZE_BASELINE_V041.json)")
    with open(BASELINE_INDEX, "r", encoding="utf-8") as handle:
        studies = json.load(handle)["studies"]
    if not studies:
        raise SystemExit("the baseline index lists no studies")
    for entry in studies:
        full = os.path.join(ROOT, *entry["path"].split("/"))
        if not os.path.isfile(full):
            raise SystemExit(f"{entry['path']}: study file missing")
        if sha256_file(full) != entry["study_sha256"]:
            raise SystemExit(f"{entry['path']}: SHA-256 differs from STUDIES_V041.json")
    return [{"set": e["set"], "path": e["path"], "sha256": e["study_sha256"]} for e in studies]


def run_one(entry: dict, worktree: str, head: str, scratch: str, timeout: float) -> dict:
    rel = entry["path"]
    raw = os.path.join(scratch, cert_name(rel))
    if os.path.exists(raw):
        os.remove(raw)
    env = dict(os.environ)
    env["PYTHONPATH"] = worktree
    env["TRUTH_GATE_WORKTREE"] = worktree
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    record = {"set": entry["set"], "path": rel, "study_sha256": entry["sha256"], "worktree_head": head}
    start = time.perf_counter()
    timed_out = False
    try:
        proc = subprocess.run([sys.executable, "-c", BOOTSTRAP, "check", rel, "--out", raw], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        exit_code, tail = proc.returncode, (proc.stdout + proc.stderr)[-500:]
    except subprocess.TimeoutExpired:
        timed_out, exit_code, tail = True, None, "timeout"
    record["exit_code"] = exit_code
    record["seconds"] = round(time.perf_counter() - start, 3)
    if timed_out:
        record["timeout"] = True
    if os.path.isfile(raw):
        with open(raw, "r", encoding="utf-8") as handle:
            body = json.load(handle)["body"]
        if body.get("tool_version") != TOOL_VERSION:
            raise SystemExit(f"{rel}: certificate says tool_version {body.get('tool_version')!r}, not {TOOL_VERSION}")
        dest = os.path.join(CERT_DIR, cert_name(rel))
        shutil.copyfile(raw, dest)
        record["cert"] = "certs/" + cert_name(rel)
        record["cert_sha256"] = sha256_file(dest)
        record["verdict"] = body.get("verdict")
    else:
        record.update(cert=None, cert_sha256=None, verdict=None, failure=tail)
    return record


def main() -> int:
    global TAG, TOOL_VERSION, CERT_DIR, INDEX
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True, help="worktree of tag v0.5.0 (git worktree add --detach DIR v0.5.0)")
    parser.add_argument("--scratch", required=True, help="scratch folder for the raw certificates")
    parser.add_argument("--timeout", type=float, default=3600.0, help="seconds per check (default 3600)")
    parser.add_argument("--limit", type=int, default=None, help="TEST ONLY: record only the first N studies (needs --out-dir)")
    parser.add_argument("--tag", default=DEFAULT_TAG, help="TEST ONLY: tag of the worktree instead of v0.5.0 (needs --out-dir)")
    parser.add_argument("--out-dir", default=None, help="TEST ONLY: output folder outside the repository (certs/ and the index)")
    args = parser.parse_args()
    test_mode = args.limit is not None or args.tag != DEFAULT_TAG
    if test_mode != (args.out_dir is not None):
        raise SystemExit("--out-dir goes with --limit / --tag (test only), and they need it: the official recording "
                         "writes into evaluation/r1_v050/")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if test_mode:
        out_dir = os.path.realpath(os.path.abspath(args.out_dir))
        root_real = os.path.realpath(ROOT)
        if out_dir == root_real or out_dir.startswith(root_real + os.sep):
            raise SystemExit("--out-dir must be outside the repository")
        TAG = args.tag
        TOOL_VERSION = TAG[1:] if TAG.startswith("v") else TAG
        CERT_DIR = os.path.join(out_dir, "certs")
        INDEX = os.path.join(out_dir, "STUDIES_V050_PARTIAL.json" if args.limit is not None else INDEX_NAME)
    if os.path.exists(INDEX):
        raise SystemExit(f"{os.path.basename(INDEX)} exists: the recording is never overwritten")
    worktree = os.path.abspath(args.worktree)
    scratch = os.path.abspath(args.scratch)
    head = verify_worktree(worktree)
    studies = baseline_studies()
    if len({e["path"] for e in studies}) != len(studies):
        raise SystemExit("a path occurs twice")
    if args.limit is not None:
        studies = studies[:args.limit]
    print(f"{len(studies)} studies: {sum(e['set'] == 'A1' for e in studies)} A1, "
          f"{sum(e['set'] == 'phase_b' for e in studies)} Phase B", flush=True)
    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(scratch, exist_ok=True)

    import numpy
    started = time.perf_counter()
    records = []
    for entry in studies:
        rec = run_one(entry, worktree, head, scratch, args.timeout)
        records.append(rec)
        print(f"{rec['path']}: exit {rec['exit_code']} {rec['verdict']} {rec['seconds']}s", flush=True)
    total = time.perf_counter() - started

    counts: dict = {}
    for rec in records:
        counts[rec["verdict"]] = counts.get(rec["verdict"], 0) + 1
    index = {
        "tool_under_test": f"truth-gate {TOOL_VERSION} (git tag {TAG})",
        "tag_commit": head,
        "mode": "full",
        "runner_python_version": sys.version.split()[0],
        "runner_numpy_version": numpy.__version__,
        "total_wall_seconds": round(total, 1),
        "verdict_counts": counts,
        "studies": records,
    }
    if args.limit is not None:
        index["partial_limit"] = args.limit
    with open(INDEX, "wb") as handle:
        handle.write((json.dumps(index, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"total wall time {total:.1f} s")
    print("verdict counts:", json.dumps(counts, sort_keys=True))
    failures = [r["path"] for r in records if r["cert"] is None]
    print(f"recording failures (no certificate): {len(failures)}", *failures)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
