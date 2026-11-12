#!/usr/bin/env python3
"""Criterion A1 smoke check for Truth_Gate 0.4 (spec 0.6, section 14).

Before anything runs, the three folders (``examples/``, ``evaluation/cases/``, ``tests/toy_studies/``) are scanned again
with the rule that wrote ``STUDIES.json`` (``record_baseline_v030.enumerate_studies``) and the found list is compared with
``STUDIES.json``: any difference (a study that is new, missing or changed) fails A1, and so does an empty list (R-34).

For every study in ``evaluation/baseline_v030/STUDIES.json``:

1. check that the study file's SHA-256 is unchanged since the baseline was recorded;
2. run the current package in full mode, as ``python -m kapi check <study at its repo path>``, from the repository
   root (the same path and mode the baseline run used);
3. apply the A1 strip rule to the baseline body and to the new body and compare them.

A1 strip rule (fixed in spec 14 before implementation): remove ``kapi_version``, ``tool``, ``tool_version``,
``spec_version``, ``non_claims`` and ``known_limitations`` wherever they appear, and the fields that are new in
schema 2 (``input_kind``, ``manifest``, ``mutations``, ``k8``, ``m_k8``, ``pattern_stats``, ``suggested_unreviewed``,
``study_notes``) from the body.  Nothing else is removed.  For a study whose baseline body carries
``K6_NONREPRODUCIBLE``, only the verdict and the sets of component and study flags are compared.

Writes ``evaluation/A1_REPORT.json`` (per study: equal or differs, and the first differing JSON path) and prints
a summary.  Exit code 0 when every study is equal, 1 otherwise.

Usage::

    py evaluation/compare_a1.py --scratch DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from record_baseline_v030 import enumerate_studies  # noqa: E402  (the scan that wrote STUDIES.json)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_DIR = os.path.join(ROOT, "evaluation", "baseline_v030")
REPORT = os.path.join(ROOT, "evaluation", "A1_REPORT.json")

STRIP_EVERYWHERE = frozenset({"kapi_version", "tool", "tool_version", "spec_version", "non_claims", "known_limitations"})
STRIP_TOP_LEVEL = frozenset(
    {"input_kind", "manifest", "mutations", "k8", "m_k8", "pattern_stats", "suggested_unreviewed", "study_notes"}
)
NONREPRODUCIBLE = "K6_NONREPRODUCIBLE"


def strip_everywhere(value):
    if isinstance(value, dict):
        return {k: strip_everywhere(v) for k, v in value.items() if k not in STRIP_EVERYWHERE}
    if isinstance(value, list):
        return [strip_everywhere(v) for v in value]
    return value


def strip_body(body: dict) -> dict:
    cleaned = strip_everywhere(body)
    return {k: v for k, v in cleaned.items() if k not in STRIP_TOP_LEVEL}


def first_difference(a, b, path="$"):
    """Path of the first difference in a deterministic walk (sorted keys, list indices), or None if equal."""
    if type(a) is not type(b):
        return path
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                return f"{path}.{key}"
            found = first_difference(a[key], b[key], f"{path}.{key}")
            if found is not None:
                return found
        return None
    if isinstance(a, list):
        for index in range(min(len(a), len(b))):
            found = first_difference(a[index], b[index], f"{path}[{index}]")
            if found is not None:
                return found
        return f"{path}[{min(len(a), len(b))}]" if len(a) != len(b) else None
    return None if a == b else path


def value_at(value, path):
    """Value at a path produced by ``first_difference`` (``<missing>`` when absent)."""
    current = value
    token = ""
    steps = []
    i = 1
    while i < len(path):
        if path[i] == ".":
            j = i + 1
            while j < len(path) and path[j] not in ".[":
                j += 1
            steps.append(path[i + 1:j])
            i = j
        else:
            j = path.index("]", i)
            steps.append(int(path[i + 1:j]))
            i = j + 1
    for step in steps:
        try:
            current = current[step]
        except (KeyError, IndexError, TypeError):
            return "<missing>"
    return current


def flag_view(body: dict) -> dict:
    """Verdict and the sets of component and study flags (the K6_NONREPRODUCIBLE exception)."""
    return {
        "verdict": body.get("verdict"),
        "study_flags": sorted(set(body.get("study_flags", []))),
        "component_flags": {c["id"]: sorted(set(c.get("flags", []))) for c in body.get("components", [])},
    }


def short(value, limit=200):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[:limit] + "..."


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def baseline_name(rel_path: str) -> str:
    return rel_path.replace("/", "__") + ".json"


def run_current(rel: str, out_json: str):
    if os.path.exists(out_json):
        os.remove(out_json)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [sys.executable, "-m", "kapi", "check", rel, "--out", out_json],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    envelope = None
    if os.path.isfile(out_json):
        with open(out_json, "r", encoding="utf-8") as handle:
            envelope = json.load(handle)
    return proc, envelope


def rescan_problems(found: list, studies: list) -> list:
    """Differences between a fresh scan of the three folders and ``STUDIES.json`` (an empty list when they agree)."""
    problems = []
    if not found:
        problems.append("the re-scan of examples/, evaluation/cases/ and tests/toy_studies/ found no study")
    if not studies:
        problems.append("STUDIES.json is empty")
    by_path_found = {e["path"]: e["sha256"] for e in found}
    by_path_base = {e["path"]: e["sha256"] for e in studies}
    for path in sorted(set(by_path_found) - set(by_path_base)):
        problems.append(f"{path}: found by the re-scan, not in STUDIES.json")
    for path in sorted(set(by_path_base) - set(by_path_found)):
        problems.append(f"{path}: in STUDIES.json, not found by the re-scan")
    for path in sorted(set(by_path_found) & set(by_path_base)):
        if by_path_found[path] != by_path_base[path]:
            problems.append(f"{path}: the SHA-256 differs from STUDIES.json")
    if len(by_path_found) != len(found) or len(by_path_base) != len(studies):
        problems.append("a path occurs twice")
    return problems


def compare_one(entry: dict, scratch: str, index: int) -> dict:
    rel = entry["path"]
    record = {"path": rel}
    if sha256_file(os.path.join(ROOT, *rel.split("/"))) != entry["sha256"]:
        record.update(result="differs", first_diff_path="<study file modified since the baseline>")
        return record
    with open(os.path.join(BASELINE_DIR, baseline_name(rel)), "r", encoding="utf-8") as handle:
        old = json.load(handle)
    proc, envelope = run_current(rel, os.path.join(scratch, f"y_{index}.json"))
    if envelope is None:
        record.update(result="differs", first_diff_path="<no certificate written>", exit_code=proc.returncode,
                      stderr_tail=proc.stderr[-500:])
        return record
    new = envelope["body"]
    record["exit_code"] = proc.returncode
    record["new_tool_version"] = new.get("tool_version")
    if NONREPRODUCIBLE in old.get("study_flags", []):
        record["comparison"] = "verdict and flag sets only (baseline carries K6_NONREPRODUCIBLE)"
        a, b = flag_view(old), flag_view(new)
    else:
        record["comparison"] = "full stripped body"
        a, b = strip_body(old), strip_body(new)
    path = first_difference(a, b)
    if path is None:
        record["result"] = "equal"
    else:
        record["result"] = "differs"
        record["first_diff_path"] = path
        record["baseline_value"] = short(value_at(a, path))
        record["new_value"] = short(value_at(b, path))
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", required=True, help="scratch folder for the raw envelopes")
    args = parser.parse_args()
    scratch = os.path.abspath(args.scratch)
    os.makedirs(scratch, exist_ok=True)
    with open(os.path.join(BASELINE_DIR, "STUDIES.json"), "r", encoding="utf-8") as handle:
        studies = json.load(handle)
    problems = rescan_problems(enumerate_studies(), studies)
    if problems:
        print("A1 FAILED: the folders no longer match STUDIES.json (R-34):")
        for problem in problems:
            print(f"   - {problem}")
        return 1
    print(f"A1 re-scan: {len(studies)} studies found, identical to STUDIES.json", flush=True)
    started = time.perf_counter()
    records = []
    for index, entry in enumerate(studies):
        record = compare_one(entry, scratch, index)
        records.append(record)
        if record["result"] != "equal":
            print(f"DIFFERS {record['path']}: {record.get('first_diff_path')}", flush=True)
    total = time.perf_counter() - started
    equal = sum(1 for r in records if r["result"] == "equal")
    report = {
        "criterion": "A1 (spec 0.6, section 14)",
        "studies": len(records),
        "equal": equal,
        "differs": len(records) - equal,
        "wall_seconds": round(total, 1),
        "results": records,
    }
    with open(REPORT, "wb") as handle:
        handle.write((json.dumps(report, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"A1: {len(records)} studies, {equal} equal, {len(records) - equal} differ ({total:.1f} s)")
    return 0 if equal == len(records) else 1


if __name__ == "__main__":
    sys.exit(main())
