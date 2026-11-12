#!/usr/bin/env python3
"""Criterion A3 runner (spec 0.6, section 14): any language gives the same answer.

For each pair (the A2 manifest under ``evaluation/phase_a/a2/<name>/`` and the A3 manifest under
``evaluation/phase_a/a3/<name>/``, whose criterion is a Node program) the gate is run on both, in full mode, from the
repository root, and the following are compared:

* the study verdict and the verdict of every component,
* the flags of every component, **excluding** ``K2_MINUS_UNREAD`` (a command criterion always reads every key), and the
  study-level flags,
* the HOLDS and UNDEFINED counts of every component on every stream.

For a pair that differs, the first differing component and stream is printed.  Before the runs, the **structure of every pair** is checked
mechanically (R-34) and the run fails if it is not met: each A3 criterion is a ``command``, and the worlds, controls,
premises and tolerances of the A3 manifest equal those of the A2 manifest.  A missing ``node`` is a failure of A3,
not a skip (exit code 1).  Nothing here is tuned: the result is reported as it comes out.  Exit code 0 when every pair
is equal, 1 otherwise.

Usage::

    py evaluation/phase_a/run_a3.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from truth_gate.certificate import run_gate  # noqa: E402

A2 = os.path.join(ROOT, "evaluation", "phase_a", "a2")
A3 = os.path.join(ROOT, "evaluation", "phase_a", "a3")
PAIRS = (
    "01_tautology_faulty",
    "01_tautology_fixed",
    "02_inert_minus_world_faulty",
    "02_inert_minus_world_fixed",
    "03_unit_epsilon_bug_faulty",
    "03_unit_epsilon_bug_fixed",
)
IGNORED_FLAGS = {"K2_MINUS_UNREAD"}


def load_manifest(root: str, name: str) -> dict:
    with open(os.path.join(root, name, "truthgate.toml"), "rb") as handle:
        return tomllib.load(handle)


def structure_problems() -> list:
    """What differs between an A3 manifest and its A2 manifest beyond the criteria's language (R-34)."""
    problems = []
    for name in PAIRS:
        for root, label in ((A2, "A2"), (A3, "A3")):
            if not os.path.isfile(os.path.join(root, name, "truthgate.toml")):
                problems.append(f"{name}: no {label} truthgate.toml")
        if problems and problems[-1].startswith(name):
            continue
        a2, a3 = load_manifest(A2, name), load_manifest(A3, name)
        criteria3 = a3.get("criteria") or []
        if not criteria3:
            problems.append(f"{name}: the A3 manifest has no criteria")
        problems += [f"{name}: A3 criterion {c.get('id')!r} is not a `command`" for c in criteria3 if "command" not in c]
        ids2 = [c.get("id") for c in a2.get("criteria") or []]
        if ids2 != [c.get("id") for c in criteria3]:
            problems.append(f"{name}: the criterion ids differ (A2 {ids2}, A3 {[c.get('id') for c in criteria3]})")
        else:
            for c2, c3 in zip(a2["criteria"], criteria3):
                if c2.get("tolerances") != c3.get("tolerances"):
                    problems.append(f"{name}: tolerances of {c2.get('id')!r} differ")
        for key in ("worlds", "controls", "premises"):
            if a2.get(key) != a3.get(key):
                problems.append(f"{name}: {key} differ between the A2 and the A3 manifest")
        files = []
        for root in (A2, A3):
            path = os.path.join(root, name, "world.py")
            files.append(open(path, "rb").read() if os.path.isfile(path) else None)
        if files[0] != files[1]:  # the worlds are Python references into world.py: the two copies must be the same
            problems.append(f"{name}: world.py differs between the A2 and the A3 folder")
    return problems


def summary(body: dict) -> dict:
    return {
        "verdict": body["verdict"],
        "study_flags": sorted(body["study_flags"]),
        "components": {
            c["id"]: {
                "verdict": c["verdict"],
                "flags": sorted(set(c["flags"]) - IGNORED_FLAGS),
                "counts": {s: {"holds": v["holds"], "undefined": v["undefined"], "n": v["n"]}
                           for s, v in sorted(c["counts"].items())},
            }
            for c in body["components"]
        },
    }


def first_difference(a: dict, b: dict) -> str:
    """Describe the first difference between two summaries ('' when equal)."""
    if a["verdict"] != b["verdict"]:
        return f"study verdict: A2 {a['verdict']} vs A3 {b['verdict']}"
    if a["study_flags"] != b["study_flags"]:
        return f"study flags: A2 {a['study_flags']} vs A3 {b['study_flags']}"
    for cid in sorted(set(a["components"]) | set(b["components"])):
        ca, cb = a["components"].get(cid), b["components"].get(cid)
        if ca is None or cb is None:
            return f"component {cid}: present only in {'A2' if cb is None else 'A3'}"
        if ca["verdict"] != cb["verdict"]:
            return f"component {cid} verdict: A2 {ca['verdict']} vs A3 {cb['verdict']}"
        if ca["flags"] != cb["flags"]:
            return f"component {cid} flags: A2 {ca['flags']} vs A3 {cb['flags']}"
        for stream in sorted(set(ca["counts"]) | set(cb["counts"])):
            sa, sb = ca["counts"].get(stream), cb["counts"].get(stream)
            if sa != sb:
                return f"component {cid}, stream {stream}: A2 {sa} vs A3 {sb}"
    return ""


def fmt_flags(flags: list) -> str:
    return ", ".join(flags) or "-"


def main() -> int:
    os.chdir(ROOT)
    if shutil.which("node") is None:
        print("A3 FAILED: `node` is not on PATH (a missing node is a failure of A3, not a skip)")
        return 1
    problems = structure_problems()
    if problems:
        print("A3 FAILED: the structure of the A3 manifests does not match their A2 manifests (R-34):")
        for problem in problems:
            print(f"   - {problem}")
        return 1
    print(f"A3 structure: {len(PAIRS)} pairs; every A3 criterion is a command; worlds, controls, premises and tolerances "
          "equal the A2 manifest\n")
    rows = []
    equal_pairs = 0
    for name in PAIRS:
        a = summary(run_gate(os.path.join(A2, name, "truthgate.toml"))["body"])
        b = summary(run_gate(os.path.join(A3, name, "truthgate.toml"))["body"])
        diff = first_difference(a, b)
        equal_pairs += not diff
        print(f"== {name}")
        print(f"   verdict   A2: {a['verdict']:<16} A3: {b['verdict']}")
        for cid in sorted(set(a["components"]) | set(b["components"])):
            ca, cb = a["components"].get(cid), b["components"].get(cid)
            print(f"   {cid}")
            print(f"     flags   A2: {fmt_flags(ca['flags']) if ca else '(missing)'}")
            print(f"             A3: {fmt_flags(cb['flags']) if cb else '(missing)'}")
            if ca and cb:
                streams = sorted(set(ca["counts"]) | set(cb["counts"]))
                same = sum(ca["counts"].get(s) == cb["counts"].get(s) for s in streams)
                print(f"     counts  {same}/{len(streams)} streams equal (HOLDS, UNDEFINED, n)")
        print(f"   -> {'equal' if not diff else 'DIFFERS, first difference: ' + diff}\n")
        rows.append((name, a["verdict"], b["verdict"], "equal" if not diff else "DIFFERS"))
    print("pair                           A2 verdict        A3 verdict        result")
    for name, va, vb, res in rows:
        print(f"{name:<30} {va:<17} {vb:<17} {res}")
    print(f"A3: {equal_pairs}/{len(PAIRS)} pairs equal")
    return 0 if equal_pairs == len(PAIRS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
