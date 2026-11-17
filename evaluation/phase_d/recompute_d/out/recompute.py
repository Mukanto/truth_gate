"""Independent recomputation of the Phase D attributable-detection rule.

Works only from inputs/RULE.md and the certificate JSON files under inputs/.
Standard library only.  Run:  py -I -B out/recompute.py
"""
import json
import math
import os
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INP = os.path.join(ROOT, "inputs")
ALPHA = Fraction(5, 100)  # one-sided Fisher threshold, strict p < 0.05

K2_FLAGS = ("K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE")
FIXED_STREAM_FLAGS = {
    "K5_HOLDS_ON_NOISE": "probe:noise",
    "K5_HOLDS_ON_NULL": "world:null",
}


# ---------------------------------------------------------------- statistics
def fisher_greater(a, n1, b, n2):
    """One-sided (greater) Fisher exact test.

    Table [[a, n1-a], [b, n2-b]]; H1: the first group's success proportion is
    greater.  p = P(X >= a), X hypergeometric (N=n1+n2, K=a+b, draws=n1).
    Returns (exact Fraction, float).
    """
    big_n = n1 + n2
    k = a + b
    total = math.comb(big_n, n1)
    lo = max(0, n1 - (big_n - k))
    hi = min(n1, k)
    num = sum(math.comb(k, x) * math.comb(big_n - k, n1 - x)
              for x in range(max(a, lo), hi + 1))
    p = Fraction(num, total)
    return p, float(p)


# ------------------------------------------------------------- flag handling
def is_rate_flag(flag):
    """Rate flags per the table in RULE.md (K2_NO_SEPARATION alone is not)."""
    if flag in K2_FLAGS or flag in ("K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
                                    "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE"):
        return True
    if flag.startswith("HIGH_RATE:"):
        s = flag[len("HIGH_RATE:"):]
        return (s.startswith("control:") or s == "probe:noise" or s == "world:null"
                or s.startswith("probe:shuffle:"))
    return False


def flag_streams(flag, comp):
    """Streams a rate flag sits on, using the bounds of the study carrying it."""
    if flag in K2_FLAGS:
        return ["world:minus"]
    if flag in FIXED_STREAM_FLAGS:
        return [FIXED_STREAM_FLAGS[flag]]
    if flag.startswith("HIGH_RATE:"):
        return [flag[len("HIGH_RATE:"):]]
    if flag in ("K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_SHUFFLE"):
        prefix = "control:" if flag == "K4_CONTROL_ALSO_HOLDS" else "probe:shuffle:"
        bounds = comp.get("bounds", {})
        plus = bounds.get("world:plus")
        if plus is None:
            return []
        out = []
        for s in sorted(bounds):
            if s.startswith(prefix) and bounds[s]["upper"] >= plus["lower"]:
                out.append(s)
        return out
    return []


def study_view(path):
    cert = json.load(open(path, encoding="utf-8"))
    body = cert.get("body", cert)
    comps = body.get("components") or []
    comp = comps[0] if comps else None
    return {
        "verdict": body.get("verdict"),
        "load_error": body.get("load_error"),
        "comp": comp,
        "flags": list(comp["flags"]) if comp else [],
        "counts": comp["counts"] if comp else {},
    }


# ------------------------------------------------------------------ one pair
def evaluate(pair_id, faulty_path, fixed_path, expected, require_present=True):
    fa, fx = study_view(faulty_path), study_view(fixed_path)
    expected = list(expected)
    exp_set = set(expected)
    res = {
        "faulty_verdict": fa["verdict"], "fixed_verdict": fx["verdict"],
        "faulty_load_error": fa["load_error"], "fixed_load_error": fx["load_error"],
        "expected_flags": expected,
        "faulty_flags": fa["flags"], "fixed_flags": fx["flags"],
    }
    # pb_detected: faulty NOT_FALSIFIABLE and at least one faulty flag is expected
    expected_present = [f for f in fa["flags"] if f in exp_set]
    res["pb_detected"] = fa["verdict"] == "NOT_FALSIFIABLE" and bool(expected_present)

    exclusions = []
    if fa["load_error"]:
        exclusions.append({"kind": "faulty_load_error", "detail": fa["load_error"],
                           "effect": "a faulty load error is not a detection"})
    if fx["load_error"]:
        exclusions.append({"kind": "fixed_load_error", "detail": fx["load_error"],
                           "effect": "no stream qualifies"})

    # streams carrying a rate flag in the fixed study (fixed's own bounds)
    fixed_rate_streams = {}
    if fx["comp"]:
        for f in fx["flags"]:
            if is_rate_flag(f):
                for s in flag_streams(f, fx["comp"]):
                    fixed_rate_streams.setdefault(s, []).append(f)
    res["fixed_rate_flag_streams"] = fixed_rate_streams

    # candidates: faulty rate flags that are expected, on their streams (faulty bounds)
    cands = []
    ignored = []
    faulty_flag_streams = {}
    flag_source = fa["flags"] if require_present else expected
    for f in flag_source:
        if not is_rate_flag(f):
            continue
        streams = flag_streams(f, fa["comp"]) if fa["comp"] else []
        faulty_flag_streams[f] = streams
        if f not in exp_set:
            ignored.append(f)
            continue
        if not streams:
            cands.append((f, None))
        for s in streams:
            cands.append((f, s))
    res["faulty_rate_flag_streams"] = faulty_flag_streams
    res["faulty_rate_flags_not_expected"] = ignored

    qualifying, nonq = [], []
    for f, s in cands:
        if s is None:
            nonq.append({"flag": f, "stream": None, "reasons": ["flag maps to no stream"]})
            continue
        reasons = []
        fc = fa["counts"].get(s)
        xc = fx["counts"].get(s)
        entry = {"flag": f, "stream": s}
        if fx["load_error"]:
            reasons.append("fixed study has a load error")
        elif xc is None:
            reasons.append("stream missing from fixed twin counts")
        elif xc.get("hard_undefined", 0) > 0:
            reasons.append("fixed study has hard UNDEFINED on stream (hard_undefined=%d)"
                           % xc["hard_undefined"])
            exclusions.append({"kind": "fixed_hard_undefined", "stream": s, "flag": f,
                               "hard_undefined": xc["hard_undefined"]})
        if fc is None:
            reasons.append("stream missing from faulty counts")
        if s in fixed_rate_streams:
            reasons.append("fixed study carries rate flag on stream: %s"
                           % ",".join(fixed_rate_streams[s]))
        if fc is not None:
            entry["faulty"] = {"holds": fc["holds"], "n": fc["n"]}
        if xc is not None:
            entry["fixed"] = {"holds": xc["holds"], "n": xc["n"]}
        if fc is not None and xc is not None:
            p, pf = fisher_greater(fc["holds"], fc["n"], xc["holds"], xc["n"])
            entry["fisher_p_one_sided"] = pf
            if not fc["holds"] > xc["holds"]:
                reasons.append("faulty count does not exceed fixed count")
            elif not p < ALPHA:
                reasons.append("one-sided Fisher p >= 0.05")
        if reasons:
            entry["reasons"] = reasons
            nonq.append(entry)
        else:
            qualifying.append(entry)

    res["qualifying"] = qualifying
    res["non_qualifying"] = nonq
    res["exclusions"] = exclusions
    qs = sorted({q["stream"] for q in qualifying})
    res["qualifying_streams"] = qs
    attributable = fa["verdict"] == "NOT_FALSIFIABLE" and bool(qualifying)
    res["attributable"] = attributable
    res["generic"] = attributable and "probe:noise" in qs
    res["declared"] = attributable and any(s != "probe:noise" for s in qs)
    if not attributable and qualifying:
        res["note"] = "stream-level qualifiers exist but faulty verdict is not NOT_FALSIFIABLE"
    return res


def _sens(r):
    return {k: r[k] for k in ("attributable", "generic", "declared", "qualifying_streams")}


def main():
    results = {}
    acc = os.path.join(INP, "acceptance")
    for pid in sorted(os.listdir(acc)):
        d = os.path.join(acc, pid)
        if not os.path.isdir(d):
            continue
        exp = json.load(open(os.path.join(d, "expected_flags.json"), encoding="utf-8"))
        r = evaluate(pid, os.path.join(d, "faulty.json"), os.path.join(d, "fixed.json"),
                     exp["cases"][pid]["expected"])
        r["set"] = "acceptance"
        r["sensitivity_expected_flag_need_not_be_present"] = _sens(
            evaluate(pid, os.path.join(d, "faulty.json"), os.path.join(d, "fixed.json"),
                     exp["cases"][pid]["expected"], require_present=False))
        results[pid] = r
    pcd = os.path.join(INP, "pc")
    pcexp = json.load(open(os.path.join(pcd, "EXPECTED_FLAGS.json"), encoding="utf-8"))["cases"]
    for cid in sorted(os.listdir(pcd)):
        d = os.path.join(pcd, cid)
        if not os.path.isdir(d):
            continue
        r = evaluate(cid, os.path.join(d, "faulty.json"), os.path.join(d, "fixed.json"),
                     pcexp[cid]["expected"])
        r["set"] = "pc"
        r["sensitivity_expected_flag_need_not_be_present"] = _sens(
            evaluate(cid, os.path.join(d, "faulty.json"), os.path.join(d, "fixed.json"),
                     pcexp[cid]["expected"], require_present=False))
        results[cid] = r

    with open(os.path.join(HERE, "RESULTS.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)

    def yn(b):
        return "Y" if b else "-"

    lines = ["# RESULTS", "",
             "| id | set | faulty | fixed | pb_det | attrib | generic | declared | qualifying streams | exclusions |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in results.items():
        qs = "; ".join("%s (%s, %d/%d vs %d/%d, p=%.4g)" % (
            q["stream"], q["flag"], q["faulty"]["holds"], q["faulty"]["n"],
            q["fixed"]["holds"], q["fixed"]["n"], q["fisher_p_one_sided"])
            for q in r["qualifying"]) or "-"
        ex = "; ".join(e["kind"] + (":" + e["stream"] if "stream" in e else "")
                       for e in r["exclusions"]) or "-"
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            k, r["set"], r["faulty_verdict"], r["fixed_verdict"], yn(r["pb_detected"]),
            yn(r["attributable"]), yn(r["generic"]), yn(r["declared"]), qs, ex))
    lines.append("")
    for s in ("acceptance", "pc"):
        alt = [r["sensitivity_expected_flag_need_not_be_present"] for r in results.values()
               if r["set"] == s]
        lines.append("(sensitivity, expected flag need not be present in faulty) %s: "
                     "attributable=%d generic=%d declared=%d" % (
                         s, sum(a["attributable"] for a in alt), sum(a["generic"] for a in alt),
                         sum(a["declared"] for a in alt)))
    lines.append("")
    for s in ("acceptance", "pc"):
        rs = [r for r in results.values() if r["set"] == s]
        lines.append("%s: n=%d pb_detected=%d attributable=%d generic=%d declared=%d" % (
            s, len(rs), sum(r["pb_detected"] for r in rs), sum(r["attributable"] for r in rs),
            sum(r["generic"] for r in rs), sum(r["declared"] for r in rs)))
    with open(os.path.join(HERE, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-2:]))


if __name__ == "__main__":
    main()
