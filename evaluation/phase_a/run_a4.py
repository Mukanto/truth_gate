#!/usr/bin/env python3
"""Criterion A4 runner (spec 0.6, section 14 and 14.1): K8 catches order dependence and changes the verdict.

Runs the planted pair under ``evaluation/phase_a/a4/`` in full mode from the repository root and checks the
pre-registered outcome:

* faulty twin: the verdict is NOT_FALSIFIABLE and ``K8_NOT_INVARIANT`` is its only mandatory flag;
* fixed twin: the verdict is FALSIFIABLE and no component carries a K8 flag.

It prints the K8 table (pairs, defined pairs, changes, UNDEFINED pairs, Wilson lower bound and level, per invariance,
component and world) and the plus and minus HOLDS rates.  The result is reported as it comes out; nothing here is
tuned.  Exit code 0 when A4 holds, 1 otherwise.

Usage::

    py evaluation/phase_a/run_a4.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from truth_gate.certificate import run_gate  # noqa: E402
from truth_gate.checks import is_mandatory  # noqa: E402

A4 = os.path.join(ROOT, "evaluation", "phase_a", "a4")


def helper_copies_agree() -> bool:
    """``a4_worlds.py`` sits next to each manifest (the manifests say ``python = "a4_worlds.py:..."``); the three
    copies must be the same bytes."""
    blobs = []
    for folder in ("", "faulty", "fixed"):
        with open(os.path.join(A4, folder, "a4_worlds.py"), "rb") as handle:
            blobs.append(handle.read())
    return blobs[0] == blobs[1] == blobs[2]


def report(name: str, body: dict) -> dict:
    print(f"== {name}: verdict {body['verdict']}   study flags: {', '.join(body['study_flags']) or '-'}")
    print(f"   m_k8 = {body['m_k8']}   {body.get('k8_statement', '(K8 did not run)')}")
    mandatory, k8_flags = [], []
    for comp in body["components"]:
        counts = comp["counts"]
        print(f"   component {comp['id']}: {comp['verdict']}   flags: {', '.join(comp['flags']) or '-'}")
        for stream in ("world:plus", "world:minus"):
            c = counts[stream]
            print(f"     {stream:<12} HOLDS {c['holds']}/{c['n']} = {c['holds'] / c['n']:.4f}   UNDEFINED {c['undefined']}")
        mandatory += [f for f in comp["flags"] if is_mandatory(f)]
        k8_flags += [f for f in comp["flags"] if f.startswith("K8_")]
    print("   K8 table   (invariance / component / world: pairs, defined, changes, undefined, wilson_lower, level)")
    for inv, comps in sorted(body["k8"].items()):
        for cid, worlds in sorted(comps.items()):
            for world in ("plus", "minus"):
                r = worlds[world]
                rate = r["changes"] / r["defined"] if r["defined"] else float("nan")
                print(f"     {inv} / {cid} / {world}: pairs {r['pairs']}, defined {r['defined']}, changes {r['changes']} "
                      f"(rate {rate:.4f}), undefined {r['undefined']}, wilson_lower {r['wilson_lower']:.6f}, "
                      f"level {r['level']}")
    return {"mandatory": sorted(set(mandatory)), "k8_flags": sorted(set(k8_flags))}


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")  # the K8 statement contains a middle dot
    except (AttributeError, ValueError):
        pass
    os.chdir(ROOT)
    ok = helper_copies_agree()
    print(f"helper a4_worlds.py identical in a4/, a4/faulty/ and a4/fixed/: {ok}\n")
    faulty = run_gate(os.path.join(A4, "faulty", "truthgate.toml"))["body"]
    f = report("faulty", faulty)
    print()
    fixed = run_gate(os.path.join(A4, "fixed", "truthgate.toml"))["body"]
    g = report("fixed", fixed)
    print()
    faulty_ok = faulty["verdict"] == "NOT_FALSIFIABLE" and f["mandatory"] == ["K8_NOT_INVARIANT"] \
        and not faulty["study_flags"]
    fixed_ok = fixed["verdict"] == "FALSIFIABLE" and not g["k8_flags"]
    print(f"faulty: NOT_FALSIFIABLE with K8_NOT_INVARIANT as its only mandatory flag: {faulty_ok}")
    print(f"fixed:  FALSIFIABLE with no K8 flag: {fixed_ok}")
    holds = ok and faulty_ok and fixed_ok
    print(f"A4: {'HOLDS' if holds else 'FAILS'}")
    return 0 if holds else 1


if __name__ == "__main__":
    raise SystemExit(main())
