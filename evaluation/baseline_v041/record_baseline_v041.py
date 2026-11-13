#!/usr/bin/env python3
"""Record the Truth_Gate 0.4.1 regression baseline (spec 0.7, section 6, step R0).

Runs, in full mode, one check at a time, the gate of tag ``v0.4.1`` on

* the 159 studies of Phase A criterion A1 (the list and the SHA-256 values of
  ``evaluation/baseline_v030/STUDIES.json``; the folders are re-scanned with
  ``record_baseline_v030.enumerate_studies`` and must agree with that file, as ``compare_a1.py`` requires), and
* the 108 Phase B files (``evaluation/phase_b/cases/<case>/faulty.py`` and ``fixed.py``; the case freeze
  ``evaluation/phase_b/FREEZE_CASES.json`` is verified first).

Every check is ``python -m truth_gate check <repo-relative path> --out <certificate>`` run from the repository root
(the working directory and path convention of ``record_baseline_v030.py``, so module paths in certificates are
comparable with later runs).  The worktree of the tag is put on ``PYTHONPATH`` and, because ``-m`` puts the working
directory ahead of ``PYTHONPATH``, also first on ``sys.path`` by a small bootstrap that then asserts that
``truth_gate`` was imported from the worktree (the working tree of the repository will hold 0.5.0 code later).

The worktree is created by the designer (``git worktree add --detach <DIR> v0.4.1``); this script checks that its HEAD
is the commit of the tag and that it is clean.

Output (never overwritten; the script refuses to run if ``STUDIES_V041.json`` exists):

* ``certs/<path with / replaced by __>.json``: the certificate envelope exactly as the tool wrote it;
* ``STUDIES_V041.json``: per study: set (``A1`` or ``phase_b``), path, study SHA-256, certificate file, certificate
  SHA-256 (of the file), verdict, exit code, wall seconds, worktree HEAD.

Usage (from anywhere)::

    py evaluation/baseline_v041/record_baseline_v041.py --worktree DIR --scratch DIR [--timeout 3600]
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
INDEX = os.path.join(HERE, "STUDIES_V041.json")
STUDIES_A1 = os.path.join(EVALUATION, "baseline_v030", "STUDIES.json")
CASES_DIR = os.path.join(EVALUATION, "phase_b", "cases")
FREEZE_CASES = os.path.join(EVALUATION, "phase_b", "FREEZE_CASES.json")
FREEZE_TOOL = os.path.join(ROOT, "protocol", "tools", "freeze.py")
TAG = "v0.4.1"
TOOL_VERSION = "0.4.1"

sys.path.insert(0, EVALUATION)
from record_baseline_v030 import enumerate_studies  # noqa: E402  (the scan that wrote STUDIES.json)

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


def a1_studies() -> list:
    with open(STUDIES_A1, "r", encoding="utf-8") as handle:
        studies = json.load(handle)
    found = {e["path"]: e["sha256"] for e in enumerate_studies()}
    listed = {e["path"]: e["sha256"] for e in studies}
    if found != listed or len(listed) != len(studies) or not studies:
        raise SystemExit("the A1 folders no longer match evaluation/baseline_v030/STUDIES.json")
    for entry in studies:
        if sha256_file(os.path.join(ROOT, *entry["path"].split("/"))) != entry["sha256"]:
            raise SystemExit(f"{entry['path']}: SHA-256 differs from STUDIES.json")
    return [{"set": "A1", "path": e["path"], "sha256": e["sha256"]} for e in studies]


def phase_b_studies() -> list:
    proc = subprocess.run([sys.executable, FREEZE_TOOL, "verify", FREEZE_CASES], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout + proc.stderr)
        raise SystemExit("case freeze verification failed: refusing to run")
    print("case freeze verified (FREEZE_CASES.json)")
    entries = []
    for case in sorted(os.listdir(CASES_DIR)):
        for twin in ("faulty", "fixed"):
            full = os.path.join(CASES_DIR, case, f"{twin}.py")
            if os.path.isfile(full):
                rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
                entries.append({"set": "phase_b", "path": rel, "sha256": sha256_file(full)})
    return entries


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True, help="worktree of tag v0.4.1 (git worktree add --detach DIR v0.4.1)")
    parser.add_argument("--scratch", required=True, help="scratch folder for the raw certificates")
    parser.add_argument("--timeout", type=float, default=3600.0, help="seconds per check (default 3600)")
    args = parser.parse_args()
    if os.path.exists(INDEX):
        raise SystemExit("STUDIES_V041.json exists: the baseline is never overwritten")
    worktree = os.path.abspath(args.worktree)
    scratch = os.path.abspath(args.scratch)
    head = verify_worktree(worktree)
    studies = a1_studies() + phase_b_studies()
    if len({e["path"] for e in studies}) != len(studies):
        raise SystemExit("a path occurs twice")
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
    with open(INDEX, "wb") as handle:
        handle.write((json.dumps(index, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"total wall time {total:.1f} s")
    print("verdict counts:", json.dumps(counts, sort_keys=True))
    failures = [r["path"] for r in records if r["cert"] is None]
    print(f"recording failures (no certificate): {len(failures)}", *failures)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
