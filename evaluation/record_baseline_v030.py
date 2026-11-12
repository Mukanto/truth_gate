#!/usr/bin/env python3
"""Record the Kapi 0.3.0 baseline for criterion A1 (spec 0.6, section 14, "Baseline").

Steps (nothing here imports the package under test; every study is run in a child process):

1. Enumerate the A1 studies: every ``.py`` file under ``examples/``, ``evaluation/cases/`` and
   ``tests/toy_studies/`` (recursive) with a module-level assignment to ``STUDY``.
   Write ``evaluation/baseline_v030/STUDIES.json`` (path, sha256).
2. Run each study with the 0.3.0 package (exported with ``git archive v0.3.0 kapi``), in full mode, from the
   repository root, and store the certificate body as canonical JSON in
   ``evaluation/baseline_v030/<path with / replaced by __>.json``.
3. Write ``evaluation/baseline_v030/RUNLOG.json`` (exit code, python and numpy versions, wall time).

Usage::

    py evaluation/record_baseline_v030.py --export DIR --scratch DIR [--jobs N]

``DIR`` for ``--export`` is the folder that contains the exported ``kapi`` package.
The child process puts the export folder before the working directory on ``sys.path`` and asserts that
``kapi.__file__`` lies inside it, then runs ``kapi``'s ``__main__`` exactly as ``-m kapi`` would.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH_DIRS = ("examples", "evaluation/cases", "tests/toy_studies")
OUT_DIR = os.path.join(ROOT, "evaluation", "baseline_v030")

# Child bootstrap: equivalent to ``python -m kapi ARGS`` with the export folder ahead of the working directory.
BOOTSTRAP = r"""
import os, runpy, sys
export = os.environ.get("KAPI_EXPORT_DIR")
cwd = os.getcwd()
sys.path[0] = cwd
if export:
    sys.path.insert(0, export)
    import kapi
    inside = os.path.normcase(os.path.realpath(kapi.__file__)).startswith(
        os.path.normcase(os.path.realpath(export)) + os.sep)
    assert inside, "kapi imported from " + kapi.__file__ + ", not from the export folder"
sys.argv = ["kapi"] + sys.argv[1:]
runpy.run_module("kapi", run_name="__main__", alter_sys=True)
"""


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def assigns_study(path: str) -> bool:
    """True if the module assigns ``STUDY`` at module level (plain, annotated or augmented assignment)."""
    with open(path, "rb") as handle:
        source = handle.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        for target in targets:
            for sub in ast.walk(target):
                if isinstance(sub, ast.Name) and sub.id == "STUDY":
                    return True
    return False


def enumerate_studies() -> list:
    found = []
    for rel_dir in SEARCH_DIRS:
        base = os.path.join(ROOT, *rel_dir.split("/"))
        for folder, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in names:
                if name.endswith(".py"):
                    full = os.path.join(folder, name)
                    if assigns_study(full):
                        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
                        found.append({"path": rel, "sha256": sha256_file(full)})
    found.sort(key=lambda e: e["path"])
    return found


def baseline_name(rel_path: str) -> str:
    return rel_path.replace("/", "__") + ".json"


def canonical_bytes(obj) -> bytes:
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return (text + "\n").encode("utf-8")


def run_one(entry: dict, export: str, scratch: str, index: int) -> dict:
    rel = entry["path"]
    out_json = os.path.join(scratch, f"x_{index}.json")
    if os.path.exists(out_json):
        os.remove(out_json)
    env = dict(os.environ)
    env["KAPI_EXPORT_DIR"] = export
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPATH", None)
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-c", BOOTSTRAP, "check", rel, "--out", out_json],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    wall = time.perf_counter() - start
    record = {"path": rel, "exit_code": proc.returncode, "wall_seconds": round(wall, 3)}
    if os.path.isfile(out_json):
        with open(out_json, "r", encoding="utf-8") as handle:
            envelope = json.load(handle)
        body = envelope["body"]
        with open(os.path.join(OUT_DIR, baseline_name(rel)), "wb") as handle:
            handle.write(canonical_bytes(body))
        record["verdict"] = body.get("verdict")
        record["python_version"] = body.get("python_version")
        record["numpy_version"] = body.get("numpy_version")
        record["kapi_version"] = body.get("kapi_version")
        record["study_flags"] = body.get("study_flags")
    else:
        record["verdict"] = None
        record["stderr_tail"] = proc.stderr[-500:]
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, help="folder that contains the exported 0.3.0 kapi package")
    parser.add_argument("--scratch", required=True, help="scratch folder for the raw envelopes")
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    export = os.path.abspath(args.export)
    scratch = os.path.abspath(args.scratch)
    os.makedirs(scratch, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    studies = enumerate_studies()
    print(f"{len(studies)} A1 studies")
    with open(os.path.join(OUT_DIR, "STUDIES.json"), "wb") as handle:
        handle.write((json.dumps(studies, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))

    import numpy
    started = time.perf_counter()
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(run_one, e, export, scratch, i) for i, e in enumerate(studies)]
        for fut in futures:
            rec = fut.result()
            records.append(rec)
            print(f"{rec['path']}: exit {rec['exit_code']} {rec['verdict']} {rec['wall_seconds']}s", flush=True)
    total = time.perf_counter() - started

    runlog = {
        "tool_under_test": "kapi 0.3.0 (git tag v0.3.0)",
        "mode": "full",
        "runner_python_version": sys.version.split()[0],
        "runner_numpy_version": numpy.__version__,
        "jobs": args.jobs,
        "total_wall_seconds": round(total, 1),
        "runs": records,
    }
    with open(os.path.join(OUT_DIR, "RUNLOG.json"), "wb") as handle:
        handle.write((json.dumps(runlog, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    counts: dict = {}
    for rec in records:
        counts[rec["verdict"]] = counts.get(rec["verdict"], 0) + 1
    print(f"total wall time {total:.1f} s")
    print("verdict counts:", json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
