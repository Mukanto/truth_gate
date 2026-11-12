#!/usr/bin/env python3
"""Criterion A2 runner (spec 0.6, section 14): manifests reproduce hand-written studies.

For each pair (an A2 manifest under ``evaluation/phase_a/a2/<name>/`` and its Python original) the gate is run on both,
in full mode, from the repository root, and the following are compared and printed side by side:

* the study verdict and the verdict of every component,
* the flags of every component and the study-level flags,
* the tolerance declarations of every criterion.

Before the runs, the **coverage of the manifests** is checked mechanically (R-34) and the run fails if it is not met:

* every Python original of examples 01-03 (both twins) and of ``convergence_criteria`` has a pair;
* the criteria of the ``03_unit_epsilon_bug_*`` manifests are patterns, and so is criterion C3 of
  ``convergence_criteria``;
* every control and premise of the manifests of examples 01-03 is a mutation (a ``mutations`` list, no Python
  reference);
* no manifest declares ``rows_exchangeable`` or ``invariances``.

The result is reported as it comes out; nothing here is tuned.  Exit code 0 when the coverage holds and every pair is
equal, 1 otherwise.

Usage::

    py evaluation/phase_a/run_a2.py
"""

from __future__ import annotations

import glob
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from truth_gate.certificate import run_gate  # noqa: E402

A2 = os.path.join(ROOT, "evaluation", "phase_a", "a2")
PAIRS = (  # (manifest folder, Python original)
    ("01_tautology_faulty", "examples/01_tautology/faulty.py"),
    ("01_tautology_fixed", "examples/01_tautology/fixed.py"),
    ("02_inert_minus_world_faulty", "examples/02_inert_minus_world/faulty.py"),
    ("02_inert_minus_world_fixed", "examples/02_inert_minus_world/fixed.py"),
    ("03_unit_epsilon_bug_faulty", "examples/03_unit_epsilon_bug/faulty.py"),
    ("03_unit_epsilon_bug_fixed", "examples/03_unit_epsilon_bug/fixed.py"),
    ("convergence_criteria", "examples/convergence_criteria/study.py"),
)
NUMBERED_EXAMPLES = ("01_", "02_", "03_")


def load_manifest(folder: str) -> dict:
    with open(os.path.join(A2, folder, "truthgate.toml"), "rb") as handle:
        return tomllib.load(handle)


def coverage_problems() -> list:
    """What the A2 inputs lack of the required coverage (R-34); an empty list means the coverage is met."""
    problems = []
    originals = {original for _folder, original in PAIRS}
    required = sorted(
        os.path.relpath(path, ROOT).replace(os.sep, "/")
        for example in sorted(glob.glob(os.path.join(ROOT, "examples", "0*_*")))
        for path in glob.glob(os.path.join(example, "*.py"))
        if os.path.basename(path) in ("faulty.py", "fixed.py")
    ) + ["examples/convergence_criteria/study.py"]
    if not any(r.startswith("examples/0") for r in required):
        problems.append("no faulty/fixed original of examples 01-03 was found")
    for path in required:
        if path not in originals:
            problems.append(f"no A2 pair for {path}")
    for folder, _original in PAIRS:
        if not os.path.isfile(os.path.join(A2, folder, "truthgate.toml")):
            problems.append(f"{folder}: no truthgate.toml")
    if problems:
        return problems
    for folder, _original in PAIRS:
        manifest = load_manifest(folder)
        numbered = folder.startswith(NUMBERED_EXAMPLES)
        criteria = manifest.get("criteria") or []
        if not criteria:
            problems.append(f"{folder}: no criteria")
        if folder.startswith("03_"):
            problems += [f"{folder}: criterion {c.get('id')!r} is not a pattern" for c in criteria if "pattern" not in c]
        if folder == "convergence_criteria":
            c3 = [c for c in criteria if str(c.get("id", "")).startswith("C3")]
            if not c3:
                problems.append(f"{folder}: no criterion C3")
            problems += [f"{folder}: criterion {c.get('id')!r} is not a pattern" for c in c3 if "pattern" not in c]
        if numbered:
            for kind in ("controls", "premises"):
                for item in manifest.get(kind) or []:
                    if not item.get("mutations") or "python" in item:
                        problems.append(f"{folder}: {kind[:-1]} {item.get('id')!r} is not a mutation")
        if (manifest.get("data") or {}).get("rows_exchangeable"):
            problems.append(f"{folder}: declares rows_exchangeable")
        if manifest.get("invariances"):
            problems.append(f"{folder}: declares invariances")
    return problems


def summary(body: dict) -> dict:
    return {
        "verdict": body["verdict"],
        "components": {c["id"]: {"verdict": c["verdict"], "flags": sorted(c["flags"])} for c in body["components"]},
        "study_flags": sorted(body["study_flags"]),
        "tolerances": {c["id"]: c["tolerances"] for c in body["study"]["criteria"]} if body.get("study") else {},
    }


def fmt_flags(flags: list) -> str:
    return ", ".join(flags) or "-"


def main() -> int:
    os.chdir(ROOT)
    problems = coverage_problems()
    if problems:
        print("A2 FAILED: the required coverage of the manifests is not met (R-34):")
        for problem in problems:
            print(f"   - {problem}")
        return 1
    print(f"A2 coverage: {len(PAIRS)} pairs; the 03 criteria and convergence C3 are patterns; every control and premise "
          "of examples 01-03 is a mutation; no rows_exchangeable, no invariances\n")
    equal_pairs = 0
    for folder, original in PAIRS:
        manifest = os.path.join(A2, folder, "truthgate.toml")
        a = summary(run_gate(manifest)["body"])
        b = summary(run_gate(os.path.join(ROOT, *original.split("/")))["body"])
        print(f"== {folder}   (manifest)  vs  {original}  (Python original)")
        print(f"   verdict            manifest: {a['verdict']:<16} original: {b['verdict']}")
        for cid in sorted(set(a["components"]) | set(b["components"])):
            ca, cb = a["components"].get(cid), b["components"].get(cid)
            print(f"   {cid}")
            print(f"     verdict          manifest: {ca['verdict'] if ca else '(missing)':<16} "
                  f"original: {cb['verdict'] if cb else '(missing)'}")
            print(f"     flags            manifest: {fmt_flags(ca['flags']) if ca else '(missing)'}")
            print(f"                      original: {fmt_flags(cb['flags']) if cb else '(missing)'}")
            ta, tb = a["tolerances"].get(cid), b["tolerances"].get(cid)
            print(f"     tolerances       manifest: {ta}   original: {tb}")
        print(f"   study flags        manifest: {fmt_flags(a['study_flags'])}   original: {fmt_flags(b['study_flags'])}")
        same = a == b
        equal_pairs += same
        print(f"   -> {'equal' if same else 'differs'}\n")
    print(f"A2: {equal_pairs}/{len(PAIRS)} pairs equal")
    return 0 if equal_pairs == len(PAIRS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
