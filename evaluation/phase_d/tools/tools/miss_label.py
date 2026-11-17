"""Phase D miss labels (R2-4, R2-34; TOOLS_SPEC_D_round2 item 7).  Runs only after the run, per pair and arm.

A miss is a pair-in-an-arm that is not an attributable detection (``attributable.classify``).  A detected pair gets no label.
Every miss gets exactly one label, the first of these that applies:

* **(e) attrition or no verdict** - ``--attrition CAUSE`` was given (an invalid skeleton, a part-B "no", a timeout, a load
  error recorded by the runner), or the faulty certificate has a load error or the verdict UNDEFINED or UNTESTED, or (T3-6)
  the fixed twin left no result and the faulty twin is PB-detected (D-R4-5): the fixed certificate has a load error,
  ``--fixed-attrition CAUSE`` names one (a fixed timeout), or the fixed certificate file is absent.  The label is (e) with the
  cause, and the tool does not stop: ``cause`` holds the text and ``cause_twin`` says "faulty", "fixed" or null (the pair as
  a whole).  The faulty twin's causes are tried first.  When the faulty twin is **not** PB-detected (verdict not
  NOT_FALSIFIABLE, or no expected flag), a fixed twin without a result does not make the pair (e): the labels (a), (b) and (d)
  apply as usual and need no fixed certificate, and the fixed twin's cause is recorded in ``fixed_attrition`` (a note;
  ``pb_detected`` says which case applies).
* **(c) flagged, not attributable** - the pair is PB-detected (faulty verdict NOT_FALSIFIABLE and an expected flag) but
  ``attributable.classify`` finds no qualifying stream.  (This includes a fixed twin with a hard UNDEFINED; a fixed twin with
  a load error is (e).)
* **(a) declared worlds lack the structure** - the share of 200 ``minus`` samples of the arm's faulty study at or beyond the
  half-way point (``structure_stat``, stream ``structure:minus``, seed 20261117) is below 0.5.  Not applied when the private
  note's statistic is "set by the brief" or absent (a decoy).  If the statistic cannot be computed on the arm's world the
  label is **structure not computable** instead of (a) (R2-34), and it is the miss's label.
* **(b) the error's minus rate stayed below the gate's flag threshold** (D-R5-5, R3B-6) - the faulty ``world:minus`` holds count of the
  certificate is below ``kstar_arm``, the smallest k of n (the certificate's n, 200) with
  ``wilson_lower(k, n, alpha_family / (2 m)) > size``; ``m`` is the gate's ``count_comparisons`` of the arm's faulty study
  and ``alpha_family`` and ``size`` come from its targets (``validity_check.kstar_of``, the function V1a uses).
* **(d) other: examined as a possible gate finding** - everything else.

Output (JSON): ``{"label": "e" | "c" | "a" | "b" | "d" | "structure_not_computable" | null, "text", "cause", "detected",
"attributable": <classify result>, "structure": {...}, "kstar_arm", "m", "faulty_minus_holds", "n", "reasons": [...]}``.  The
structure, k* and count fields are filled for the labels c, a, b, d and structure_not_computable (for (e) and for a detected
pair there is nothing to compute).

Usage:
    py miss_label.py --faulty F.json --fixed X.json --expected-file EXPECTED_FLAGS_D.json --case "<id>/<arm>"
                     --private PRIVATE.json --study FAULTY_STUDY.py --package-root DIR [--attrition CAUSE]
                     [--fixed-attrition CAUSE] [--out OUT.json]
``--faulty``, ``--fixed`` and ``--study`` may be left out when ``--attrition`` is given (their runs have no result).  ``--fixed``
may also be left out, or name a file that does not exist, when the fixed twin has no certificate: label (e), cause "fixed
certificate absent"; ``--fixed-attrition`` (a fixed timeout) wins over a certificate that is present.  Exit
code 0 on a label (or "detected"), 2 on a usage error.
"""
import argparse
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from attributable import classify  # noqa: E402
from structure_stat import (PackageRootError, StatisticError, import_truth_gate, load_study_module,  # noqa: E402
                            structure_stat)
from validity_check import kstar_of  # noqa: E402

SEED = 20261117
STRUCTURE_SAMPLES = 200
TEXTS = {
    "e": "attrition or no verdict",
    "c": "flagged, not attributable",
    "a": "declared worlds lack the structure",
    "b": "the error's minus rate stayed below the gate's flag threshold",  # D-R5-5
    "d": "other: examined as a possible gate finding",
    "structure_not_computable": "structure not computable",
}


NO_FIXED_RESULT = {"verdict": "UNDEFINED", "components": [], "load_error": {"type": "no fixed result"}}  # D-R4-5


class LabelError(Exception):
    """The inputs cannot be labelled (a usage error)."""


def has_statistic(private):
    """True if the private note carries a structure statistic that is not "set by the brief"."""
    spec = private.get("structure_statistic")
    return bool(spec) and not spec.get("set_by_brief")


def label_miss(faulty_body, fixed_body, expected, private, study_module, package_root, attrition=None, fixed_attrition=None):
    """Label one pair in one arm (see the module docstring).  ``faulty_body`` and ``fixed_body`` are certificate bodies,
    ``study_module`` the loaded faulty study of the arm.  ``faulty_body``, ``expected``, ``private`` and ``study_module`` may
    be ``None`` only with ``attrition``.  ``fixed_body`` may be ``None`` (the fixed certificate is absent: label (e)), and
    ``fixed_attrition`` names a cause of the fixed twin that left no result, such as a timeout (label (e))."""
    import_truth_gate(package_root)
    res = {"label": None, "text": None, "cause": None, "cause_twin": None, "detected": False, "attributable": None,
           "structure": None, "kstar_arm": None, "m": None, "faulty_minus_holds": None, "n": None, "reasons": [],
           "pb_detected": None, "fixed_attrition": None}  # D-R4-5

    def done(label, why):
        res["label"], res["text"] = label, TEXTS[label]
        res["reasons"].append(why)
        return res

    if attrition:
        res["cause"] = attrition
        return done("e", f"attrition: {attrition}")
    if faulty_body is None or study_module is None:
        raise LabelError("the faulty certificate and the faulty study file are required unless --attrition is given")

    # --- (e) from the faulty certificate
    comps = faulty_body.get("components") or []
    if faulty_body.get("load_error") or not comps:
        res["cause"], res["cause_twin"] = "faulty load error", "faulty"
        return done("e", "no verdict: faulty load error")
    if faulty_body["verdict"] in ("UNDEFINED", "UNTESTED"):
        res["cause"], res["cause_twin"] = f"faulty verdict {faulty_body['verdict']}", "faulty"
        return done("e", f"no verdict: {res['cause']}")

    # --- (e) from the fixed twin (T3-6, D-R4-5): only when the faulty twin is PB-detected, so that the fixed twin decides
    pb = faulty_body["verdict"] == "NOT_FALSIFIABLE" and any(f in set(expected) for f in comps[0]["flags"])  # D-R4-5
    res["pb_detected"] = pb  # D-R4-5
    fixed_problem = None  # D-R4-5
    if fixed_attrition:  # D-R4-5
        fixed_problem = fixed_attrition  # D-R4-5
    elif fixed_body is None:  # D-R4-5
        fixed_problem = "fixed certificate absent"  # D-R4-5
    elif fixed_body.get("load_error") or not (fixed_body.get("components") or []):  # D-R4-5
        fixed_problem = "fixed load error"  # D-R4-5
    if fixed_problem and pb:  # D-R4-5
        res["cause"], res["cause_twin"] = fixed_problem, "fixed"
        return done("e", f"fixed twin: {fixed_problem}")
    if fixed_problem:  # D-R4-5: the faulty twin is not PB-detected: the structure labels need no fixed certificate
        res["fixed_attrition"] = fixed_problem  # D-R4-5
        res["reasons"].append(f"note: the fixed twin has no result ({fixed_problem}); the faulty twin is not PB-detected, "
                              "so the labels (a), (b) and (d) apply")  # D-R4-5
        fixed_body = NO_FIXED_RESULT  # D-R4-5: a stand-in, only so that classify can say why nothing is attributable

    # --- detected: no label
    att = classify(faulty_body, fixed_body, expected)
    res["attributable"] = att
    if att["attributable"]:
        res["detected"] = True
        res["reasons"].append("attributable detection: no label")
        return res

    # --- the facts of (a) and (b)
    study = study_module.STUDY
    from truth_gate.checks import count_comparisons
    counts_minus = comps[0]["counts"]["world:minus"]
    res["faulty_minus_holds"], res["n"] = counts_minus["holds"], counts_minus["n"]
    res["m"] = count_comparisons(study)
    res["kstar_arm"] = kstar_of(study.targets.alpha_family, res["m"], study.targets.size, n=counts_minus["n"])
    below_kstar = res["kstar_arm"] is None or counts_minus["holds"] < res["kstar_arm"]
    res["structure"] = structure_of(private, study_module, package_root, res["reasons"])

    # --- (c)
    if att["pb_detected"]:
        res["reasons"].append("PB-detected, no attributable stream: " + "; ".join(att["reasons"]))
        return done("c", "flagged, not attributable")

    # --- (a)
    st = res["structure"]
    if st is not None:
        if st.get("error"):
            return done("structure_not_computable", "structure not computable: " + st["error"])
        if st["share_beyond_half"] < 0.5:
            return done("a", f"share beyond the half-way point {st['share_beyond_half']:.3f} < 0.5")
    # --- (b)
    if below_kstar:
        return done("b", f"faulty minus count {res['faulty_minus_holds']} < k* {res['kstar_arm']}")
    return done("d", f"faulty minus count {res['faulty_minus_holds']} >= k* {res['kstar_arm']}, structure present or not "
                     "applicable, no attributable detection")


def structure_of(private, study_module, package_root, reasons):
    """The statistic on 200 minus samples of the arm's study (stream ``structure:minus``, seed 20261117), ``{"error": text}``
    if it cannot be computed, or ``None`` when the label does not apply (set by the brief, or no statistic)."""
    if not has_statistic(private):
        why = "set by the brief" if (private.get("structure_statistic") or {}).get("set_by_brief") else "no structure statistic"
        reasons.append(f"structure label not applied: {why}")
        return None
    try:
        return structure_stat(study_module, private, "minus", STRUCTURE_SAMPLES, SEED, package_root)
    except StatisticError as e:
        return {"error": str(e)}


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Label a miss of one pair in one arm (Phase D, after the run).")
    ap.add_argument("--faulty", metavar="F.json")
    ap.add_argument("--fixed", metavar="X.json")
    ap.add_argument("--expected-file", metavar="EXPECTED_FLAGS_D.json")
    ap.add_argument("--case", metavar="ID/ARM", help='the key in the expected file, "<id>/<arm>"')
    ap.add_argument("--private", metavar="PRIVATE.json")
    ap.add_argument("--study", metavar="FILE", help="the arm's faulty study file (as it was run)")
    ap.add_argument("--package-root", required=True, metavar="DIR")
    ap.add_argument("--attrition", metavar="CAUSE")
    ap.add_argument("--fixed-attrition", metavar="CAUSE", help="the fixed twin left no result (a timeout): label (e)")
    ap.add_argument("--out", metavar="OUT.json")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    try:
        import_truth_gate(a.package_root)
    except PackageRootError as e:
        print(f"package root check failed: {e}", file=sys.stderr)
        return 2
    try:
        if a.attrition:
            res = label_miss(None, None, None, None, None, a.package_root, attrition=a.attrition)
        else:
            for name in ("faulty", "expected_file", "case", "private", "study"):
                if getattr(a, name) is None:
                    raise LabelError(f"--{name.replace('_', '-')} is required unless --attrition is given")
            fc = _read_json(a.faulty)
            xc = _read_json(a.fixed) if (a.fixed and not a.fixed_attrition and os.path.isfile(a.fixed)) else None
            expected = _read_json(a.expected_file)["cases"][a.case]["expected"]
            private = _read_json(a.private)
            with open(a.study, encoding="utf-8") as f:
                module = load_study_module(f.read(), a.study, "faulty")
            res = label_miss(fc.get("body", fc), None if xc is None else xc.get("body", xc), expected, private, module,
                             a.package_root, fixed_attrition=a.fixed_attrition)
    except (OSError, ValueError, KeyError, TypeError, LabelError) as e:
        print(f"miss_label: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
