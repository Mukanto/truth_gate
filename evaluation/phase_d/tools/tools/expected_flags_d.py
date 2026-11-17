"""Phase D expected flags per pair and arm (R2-18; TOOLS_SPEC_D_round2 item 8).

PC section 6 (as PB section 6) fixes one list of expected flags for the in-scope classes and enumerates, per case, the
controls and relational pairs the case declares.  In Phase D the world author declares them per arm, so the list is made per
pair and arm, from the assembled faulty study of that arm, at the case freeze:

* the base list (nine flags, identical to Phase C's ``EXPECTED_FLAGS.json["base"]``);
* ``HIGH_RATE:control:<id>`` for each declared control (the stream of a control is ``control:<id>``);
* ``HIGH_RATE:probe:shuffle:<a>,<b>`` for each declared relational pair (the stream is ``probe:shuffle:<a>,<b>``;
  ``truth_gate.probes.shuffle_name`` builds the name).

In that order, controls and pairs in the order the study declares them.

Output ``EXPECTED_FLAGS_D.json``::

    {"note": ..., "base": [...], "cases": {"<id>/<arm>": {"expected": [...]}}}

``<arm>`` is ``reference``, ``W0`` or ``W1`` (the skeleton's name, as ``check_skeletons_d.py`` keys them).  The ``cases`` part
has the format of ``attributable.py``'s ``--expected-file``.

The base list is checked against Phase C's file, ``evaluation/phase_c/EXPECTED_FLAGS.json`` under the package root (or the
file given by ``--phase-c-expected``): a difference stops the tool with exit code 1 and writes nothing.  If that file cannot
be found, the check is reported as not done on stderr and in the output (``"base_checked_against": null``).

Usage:
    py expected_flags_d.py --case DIR [--case DIR ...] --package-root DIR --out EXPECTED_FLAGS_D.json [--phase-c-expected F]
    py expected_flags_d.py --study "<id>/<arm>=FAULTY_STUDY.py" [...] --package-root DIR --out ...
``--case`` assembles ``faulty_body.py`` into ``reference.py`` and into ``skeletons/W0.py`` and ``skeletons/W1.py`` where they
exist.  ``--study`` takes an already assembled faulty study file.  Exit code 0 on success, 1 if the base list differs from
Phase C's, 2 on a usage error.
"""
import argparse
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from assemble import AssembleError, assemble  # noqa: E402
from structure_stat import PackageRootError, import_truth_gate, load_study_module  # noqa: E402

BASE = [
    "K2_HIGH_SIZE",
    "K2_FAILS_UNREACHABLE",
    "K2_NO_SEPARATION",
    "K4_CONTROL_ALSO_HOLDS",
    "K5_HOLDS_ON_NOISE",
    "K5_HOLDS_ON_NULL",
    "K5_HOLDS_ON_SHUFFLE",
    "HIGH_RATE:probe:noise",
    "HIGH_RATE:world:null",
]
SKELETONS = (("reference", "reference.py"), ("W0", os.path.join("skeletons", "W0.py")),
             ("W1", os.path.join("skeletons", "W1.py")))
NOTE = ("PREREG_PHASE_D section 5 (PC section 6, PB section 6): the base list, HIGH_RATE:control:<id> for each control and "
        "HIGH_RATE:probe:shuffle:<a>,<b> for each relational pair that the arm's assembled faulty study declares. "
        "Information flags and capping flags never count.")


class ExpectedFlagsError(Exception):
    """A usage or consistency error."""


def expected_flags(study):
    """The expected list of one study: the base list, its controls, its relational pairs."""
    from truth_gate import probes
    out = list(BASE)
    out += [f"HIGH_RATE:control:{c.id}" for c in study.controls]
    out += [f"HIGH_RATE:probe:{probes.shuffle_name(a, b)}" for a, b in study.relational]
    return out


def check_base(path):
    """``(ok, message)`` of the comparison of ``BASE`` with ``path``'s ``base``."""
    with open(path, encoding="utf-8") as f:
        theirs = json.load(f)["base"]
    if theirs != BASE:
        return False, f"the base list differs from {path}: {BASE} != {theirs}"
    return True, f"the base list equals {path}"


def case_studies(case_dir):
    """``[(key, study_source)]`` for the arms of one case folder (faulty body assembled into each skeleton)."""
    with open(os.path.join(case_dir, "brief.json"), encoding="utf-8") as f:
        case_id = json.load(f)["id"]
    with open(os.path.join(case_dir, "faulty_body.py"), encoding="utf-8") as f:
        body = f.read()
    out = []
    for arm, rel in SKELETONS:
        path = os.path.join(case_dir, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            skeleton = f.read()
        try:
            out.append((f"{case_id}/{arm}", assemble(skeleton, body)))
        except AssembleError as e:
            raise ExpectedFlagsError(f"{case_id}/{arm}: {e}") from e
    if not out:
        raise ExpectedFlagsError(f"{case_dir}: no skeleton found (reference.py, skeletons/W0.py, skeletons/W1.py)")
    return out


def build(studies):
    """``{"<id>/<arm>": {"expected": [...]}}`` from ``[(key, study_source)]``."""
    cases = {}
    for key, src in studies:
        if key in cases:
            raise ExpectedFlagsError(f"duplicate key {key}")
        module = load_study_module(src, f"{key}.py", "faulty")
        study = getattr(module, "STUDY", None)
        if study is None:
            raise ExpectedFlagsError(f"{key}: the file defines no STUDY")
        cases[key] = {"expected": expected_flags(study)}
    return cases


def main(argv=None):
    ap = argparse.ArgumentParser(description="Enumerate the expected flags per pair and arm (Phase D, at the case freeze).")
    ap.add_argument("--case", action="append", default=[], metavar="DIR")
    ap.add_argument("--study", action="append", default=[], metavar="ID/ARM=FILE")
    ap.add_argument("--package-root", required=True, metavar="DIR")
    ap.add_argument("--out", required=True, metavar="EXPECTED_FLAGS_D.json")
    ap.add_argument("--phase-c-expected", metavar="FILE",
                    help="Phase C's EXPECTED_FLAGS.json (default: evaluation/phase_c/EXPECTED_FLAGS.json under the package root)")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    if not a.case and not a.study:
        print("give at least one --case DIR or --study ID/ARM=FILE", file=sys.stderr)
        return 2
    try:
        import_truth_gate(a.package_root)
    except PackageRootError as e:
        print(f"package root check failed: {e}", file=sys.stderr)
        return 2
    pc = a.phase_c_expected or os.path.join(a.package_root, "evaluation", "phase_c", "EXPECTED_FLAGS.json")
    checked = None
    if os.path.isfile(pc):
        try:
            ok, msg = check_base(pc)
        except (OSError, ValueError, KeyError) as e:
            print(f"cannot read {pc}: {type(e).__name__}: {e}", file=sys.stderr)
            return 2
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        checked = pc
        print(msg, file=sys.stderr)
    elif a.phase_c_expected:
        print(f"--phase-c-expected {pc} does not exist", file=sys.stderr)
        return 2
    else:
        print(f"warning: {pc} not found; the base list was not checked", file=sys.stderr)
    try:
        studies = []
        for cd in a.case:
            studies += case_studies(cd)
        for item in a.study:
            key, sep, path = item.partition("=")
            if not sep or "/" not in key:
                raise ExpectedFlagsError(f"--study needs ID/ARM=FILE, got {item!r}")
            with open(path, encoding="utf-8") as f:
                studies.append((key, f.read()))
        cases = build(studies)
    except (OSError, ValueError, KeyError, TypeError, ExpectedFlagsError) as e:
        print(f"expected_flags_d: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # a skeleton that does not load
        print(f"expected_flags_d: a study did not load: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    out = {"note": NOTE, "base": BASE, "base_checked_against": checked, "cases": cases}
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"{len(cases)} case/arm entries written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
