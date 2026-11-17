"""Phase D attributable detection (PREREG_PHASE_D section 5; TOOLS_SPEC_D section 4).

``classify(faulty_cert, fixed_cert, expected)`` applies the rule to the ``body`` of two gate certificates (one criterion
``C`` without components, so one component record each) and the list of expected flags of the pair.

Rate flags and the stream each maps to (the counts and bounds of the certificate decide which streams exist):
  K2_HIGH_SIZE, K2_FAILS_UNREACHABLE            -> world:minus
  K5_HOLDS_ON_NOISE, HIGH_RATE:probe:noise      -> probe:noise
  K5_HOLDS_ON_NULL, HIGH_RATE:world:null        -> world:null
  K5_HOLDS_ON_SHUFFLE                           -> the probe:shuffle:* streams s of that certificate with
                                                   bounds[s]["upper"] >= bounds["world:plus"]["lower"]
  K4_CONTROL_ALSO_HOLDS                         -> the control:* streams s of that certificate with
                                                   bounds[s]["upper"] >= bounds["world:plus"]["lower"]
  HIGH_RATE:<stream>                            -> <stream>
Anything else (K2_NO_SEPARATION, K5_INCONCLUSIVE:..., ...) is not a rate flag.
The bounds condition is the gate's own: truth_gate/checks.py check_k4 (lines 263-265) and check_k5 (lines 287-289) raise the
flag once per stream whose ``not sl(st, plus, ctx)``; ``sl`` (checks.py 155-159) is ``sl_stochastic`` (stats.py 55-57),
``wilson_upper(stream) < wilson_lower(plus)`` at the per-bound level; the certificate's ``bounds`` (checks.py 784-787) are
those Wilson bounds, so "not SL" is ``upper(stream) >= lower(plus)``.  (The certificate rounds the bounds to 12 decimals.)
A certificate without bounds (deterministic mode) maps K4 and shuffle flags to no stream; the reason says so.

Rule.  The pair is PB-detected if the faulty verdict is NOT_FALSIFIABLE and a faulty flag is in ``expected``.  It is
attributable if, in addition, some expected rate flag of the faulty twin on a stream s has both (a) no rate flag of the
fixed twin mapping to s and (b) faulty holds on s greater than fixed holds with a one-sided Fisher exact p < 0.05 (from
the counts' ``holds`` and ``n``).  Load errors and hard UNDEFINED (R2-2, R2-23):
  * a faulty body without a component or with ``load_error``: pb_detected is False, reason "faulty load error"; no exception;
  * a fixed body without a component or with ``load_error``: no stream qualifies, reason "fixed load error";
  * the fixed counts on s with ``hard_undefined`` > 0: s does not qualify, reason "fixed hard UNDEFINED on s";
  * the fixed twin has no counts for s: s does not qualify, the reason is listed.
``generic``: ``probe:noise`` qualifies.  ``declared``: a qualifying stream other than ``probe:noise`` exists.
``draft1_rule``: the draft-1 rule, kept as a secondary scoring: PB-detected, and some expected rate flag of the faulty
twin on s with a holds rate at least 0.10 above the fixed twin's (20 of 200) and Fisher p < 0.05 (no condition (a); it
needs fixed counts for s, so a fixed load error gives False; it ignores ``hard_undefined``, which the draft-1 rule never had).

Returns {"pb_detected", "attributable", "generic", "declared", "draft1_rule", "qualifying": [...], "reasons": [...]}.
Each ``qualifying`` entry is {"flag", "stream", "faulty_holds", "faulty_n", "fixed_holds", "fixed_n", "p"}.

Usage:  py attributable.py --faulty F.json --fixed X.json --expected-file EXPECTED.json --case ID [--package-root DIR]
F.json and X.json are certificate files (the ``body`` is used; a bare body is accepted); EXPECTED.json is PC's
EXPECTED_FLAGS.json (``{"cases": {ID: {"expected": [...]}}}``).  Prints the result as JSON.  Exit code 0, or 2 on a usage
error.  ``--package-root`` is accepted for uniformity and only verified (the rule needs no gate).
"""
import argparse
import json
import os
import sys
from math import comb

P_LIMIT = 0.05
DRAFT1_MARGIN = 0.10  # 20 holds of 200


def fisher_greater(a, n1, b, n2):
    """One-sided p of Fisher's exact test that the first proportion (a of n1) exceeds the second (b of n2).

    Exact, by the hypergeometric tail: P(X >= a) with X the number of the k = a + b successes that fall in group 1.
    """
    if not (0 <= a <= n1 and 0 <= b <= n2):
        raise ValueError("require 0 <= a <= n1 and 0 <= b <= n2")
    k, n = a + b, n1 + n2
    total = comb(n, k)
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(k, n1) + 1)) / total


PLUS = "world:plus"


def not_sl_streams(counts, bounds, prefix):
    """Streams s of ``counts`` starting with ``prefix`` whose gate SL against plus fails: bounds[s]["upper"] >= bounds[plus]["lower"].

    This is the condition under which ``check_k4`` / ``check_k5`` raise their flag for the stream (see the module
    docstring).  Returns ``[]`` when the certificate has no bounds for plus (deterministic mode) or for s.
    """
    if not bounds or PLUS not in bounds:
        return []
    plus_lower = bounds[PLUS]["lower"]
    return [s for s in counts if s.startswith(prefix) and s in bounds and bounds[s]["upper"] >= plus_lower]


def streams_of(flag, counts, bounds=None):
    """Streams a rate flag maps to (``[]`` for a flag that is not a rate flag).  ``bounds`` is the component's ``bounds``."""
    if flag in ("K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE"):
        return ["world:minus"]
    if flag in ("K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"):
        return ["probe:noise"]
    if flag in ("K5_HOLDS_ON_NULL", "HIGH_RATE:world:null"):
        return ["world:null"]
    if flag == "K5_HOLDS_ON_SHUFFLE":
        return not_sl_streams(counts, bounds, "probe:shuffle:")
    if flag == "K4_CONTROL_ALSO_HOLDS":
        return not_sl_streams(counts, bounds, "control:")
    if flag.startswith("HIGH_RATE:"):
        return [flag[len("HIGH_RATE:"):]]
    return []


def _no_component(body):
    """True if a certificate body carries no usable component: a load error, or ``components`` empty."""
    return bool(body.get("load_error")) or len(body.get("components") or []) == 0


def _component(body, which):
    comps = body["components"]
    if len(comps) != 1:
        raise ValueError(f"{which}: expected one component, found {len(comps)}")
    return comps[0]


def classify(faulty_cert: dict, fixed_cert: dict, expected: list) -> dict:
    """Classify one pair (see the module docstring).  The certificates are the ``body`` of gate certificates."""
    expected = set(expected)
    out = {"pb_detected": False, "attributable": False, "generic": False, "declared": False, "draft1_rule": False,
           "qualifying": [], "reasons": []}
    if _no_component(faulty_cert):
        out["reasons"].append("faulty load error")
        return out
    cf = _component(faulty_cert, "faulty")
    flags_f = list(cf["flags"])
    counts_f, bounds_f = cf["counts"], cf.get("bounds") or {}
    hits = [f for f in flags_f if f in expected]
    pb = faulty_cert["verdict"] == "NOT_FALSIFIABLE" and bool(hits)
    out["pb_detected"] = pb
    if not pb:
        if faulty_cert["verdict"] != "NOT_FALSIFIABLE":
            out["reasons"].append(f"faulty verdict is {faulty_cert['verdict']}, not NOT_FALSIFIABLE")
        else:
            out["reasons"].append("no faulty flag is in the expected list")
        return out
    if _no_component(fixed_cert):
        out["reasons"].append("fixed load error")
        return out
    cx = _component(fixed_cert, "fixed")
    flags_x = list(cx["flags"])
    counts_x, bounds_x = cx["counts"], cx.get("bounds") or {}
    fixed_streams = {s for f in flags_x for s in streams_of(f, counts_x, bounds_x)}
    for f in hits:
        streams = streams_of(f, counts_f, bounds_f)
        if not streams and f in ("K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_SHUFFLE"):
            out["reasons"].append(f"{f}: no stream meets the bounds condition in the faulty certificate")
        for s in streams:
            if s not in counts_x:
                out["reasons"].append(f"{f}@{s}: fixed has no counts")
                continue
            a, n1 = counts_f[s]["holds"], counts_f[s]["n"]
            b, n2 = counts_x[s]["holds"], counts_x[s]["n"]
            p = fisher_greater(a, n1, b, n2)
            if (a / n1 - b / n2) >= DRAFT1_MARGIN - 1e-12 and p < P_LIMIT:
                out["draft1_rule"] = True
            if counts_x[s].get("hard_undefined", 0) > 0:
                out["reasons"].append(f"{f}@{s}: fixed hard UNDEFINED on {s}")
                continue
            flagged = s in fixed_streams
            ok = (not flagged) and a > b and p < P_LIMIT
            note = f"{f}@{s} {a} vs {b} p={p:.3g}" + (" fixed-flagged" if flagged else "") + (" OK" if ok else "")
            out["reasons"].append(note)
            if ok:
                out["qualifying"].append({"flag": f, "stream": s, "faulty_holds": a, "faulty_n": n1,
                                          "fixed_holds": b, "fixed_n": n2, "p": p})
    qs = {q["stream"] for q in out["qualifying"]}
    out["attributable"] = bool(qs)
    out["generic"] = "probe:noise" in qs
    out["declared"] = any(s != "probe:noise" for s in qs)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Attributable detection of a pair of gate certificates (Phase D).")
    ap.add_argument("--faulty", required=True)
    ap.add_argument("--fixed", required=True)
    ap.add_argument("--expected-file", required=True)
    ap.add_argument("--case", required=True)
    ap.add_argument("--package-root", default=None, help="optional; verified only (no gate is needed)")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    if a.package_root is not None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from structure_stat import import_truth_gate, PackageRootError
        try:
            import_truth_gate(a.package_root)
        except PackageRootError as e:
            print(f"package root check failed: {e}", file=sys.stderr)
            return 2
    try:
        with open(a.faulty, encoding="utf-8") as f:
            cert_f = json.load(f)
        with open(a.fixed, encoding="utf-8") as f:
            cert_x = json.load(f)
        with open(a.expected_file, encoding="utf-8") as f:
            expected = json.load(f)["cases"][a.case]["expected"]
        result = classify(cert_f.get("body", cert_f), cert_x.get("body", cert_x), expected)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"attributable: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
