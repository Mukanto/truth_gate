"""Designer's independent recomputation of the Phase D results.

Written from the rule texts alone (PREREG_PHASE_D sections 5 and 6, PREREG_PHASE_B
section 6, PREREG_PHASE_C section 6).  It does not use or read the official scorer, the
attributable tool, the Phase C runner or any earlier designer script.  Inputs are the
gate certificates, RUNLOG.jsonl, EXPECTED_FLAGS_D.json, ID_MAP_D.json and the part-B
audit files.  Standard library only.

Run:  py -I -B recompute_designer_d.py
Writes RECOMPUTE_D.json and RECOMPUTE_D.md next to this script.

Decisions that the texts do not fix (all recorded in the output under "assumptions"):
  * clean pass without the noise stream: the fixed twin has a clean verdict
    (FALSIFIABLE or WEAK), or its verdict is NOT_FALSIFIABLE and every flag it carries
    is either informational (K5_INCONCLUSIVE:*, K1_ABSTAINED:*, K1_ABSTAINED_MAJORITY:*,
    K2_MINUS_UNREAD, K8_SOME_CHANGES, BAD_RETURN) or a noise-stream flag
    (K5_HOLDS_ON_NOISE, HIGH_RATE:probe:noise).
  * the pair set is every pair that was run (20), classes from ID_MAP_D.json; the
    "reserve" marker is not used to exclude any pair.
"""
import hashlib
import json
import math
import os
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)                       # ...\Kapi\phase_d_work
RUNLOG = os.path.join(WORK, "run", "RUNLOG.jsonl")
CERTS = os.path.join(WORK, "run", "certs")
OSS = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
EXPECTED = os.path.join(OSS, "EXPECTED_FLAGS_D.json")
IDMAP = os.path.join(OSS, "record", "shuffle", "ID_MAP_D.json")
AUDIT_B_DIR = os.path.join(OSS, "record", "sandboxes", "audit_b")

Z = 1.6448536269514722                  # one-sided 95%
ARMS = ["R", "W0", "W1"]
EXP_ARM = {"R": "reference", "W0": "W0", "W1": "W1"}
CLASSES = ["B-2", "B-3", "B-1", "B-6"]
INFO_PREFIXES = ("K1_ABSTAINED", "K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN",
                 "K5_INCONCLUSIVE")
NOISE_FLAGS = ("K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise")
K2_STREAM_FLAGS = ("K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE")
ALPHA = Fraction(5, 100)


# ----------------------------------------------------------------- statistics
def wilson_lower(x, n):
    if n == 0:
        return None
    p = x / n
    z2 = Z * Z
    centre = p + z2 / (2 * n)
    half = Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return (centre - half) / (1 + z2 / n)


def fisher_greater(a, n1, b, n2):
    """One-sided Fisher exact p for [[a, n1-a],[b, n2-b]], H1: first proportion larger."""
    big_n, k = n1 + n2, a + b
    total = math.comb(big_n, n1)
    lo, hi = max(0, n1 - (big_n - k)), min(n1, k)
    num = sum(math.comb(k, x) * math.comb(big_n - k, n1 - x)
              for x in range(max(a, lo), hi + 1))
    return Fraction(num, total)


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return Fraction(1)
    return Fraction(sum(math.comb(n, k) for k in range(b, n + 1)), 2 ** n)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# --------------------------------------------------------------- flag handling
def is_rate_flag(flag):
    if flag in K2_STREAM_FLAGS or flag in ("K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
                                           "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE"):
        return True
    if flag.startswith("HIGH_RATE:"):
        s = flag[len("HIGH_RATE:"):]
        return s.startswith("control:") or s in ("probe:noise", "world:null") \
            or s.startswith("probe:shuffle:")
    return False


def flag_streams(flag, comp):
    """Streams of a rate flag; K4/K5-shuffle use the bounds of the certificate carrying it."""
    if flag in K2_STREAM_FLAGS:
        return ["world:minus"]
    if flag == "K5_HOLDS_ON_NOISE":
        return ["probe:noise"]
    if flag == "K5_HOLDS_ON_NULL":
        return ["world:null"]
    if flag.startswith("HIGH_RATE:"):
        return [flag[len("HIGH_RATE:"):]]
    if flag in ("K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_SHUFFLE"):
        prefix = "control:" if flag == "K4_CONTROL_ALSO_HOLDS" else "probe:shuffle:"
        bounds = comp.get("bounds", {})
        plus = bounds.get("world:plus")
        if plus is None:
            return []
        return [s for s in sorted(bounds)
                if s.startswith(prefix) and bounds[s]["upper"] >= plus["lower"]]
    return []


def is_info_flag(flag):
    return flag.startswith(INFO_PREFIXES)


# ----------------------------------------------------------------------- load
def load_runlog():
    last = {}
    with open(RUNLOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("event") == "result":
                last[(r["case"], r["arm"], r["twin"])] = r      # later rows replace earlier
    return last


def load_twin(case, arm, twin, runrow):
    """Return a dict describing one study: status, verdict, flags, counts, bounds."""
    out = {"status": None, "verdict": None, "flags": [], "counts": {}, "comp": None,
           "load_error": None, "cert_file": None, "runlog_verdict": None}
    path = os.path.join(CERTS, arm, "%s_%s.json" % (case, twin))
    if runrow is not None:
        out["runlog_verdict"] = runrow.get("verdict")
    if runrow is not None and runrow.get("timed_out"):
        out["status"] = "timeout"
        return out
    if not os.path.exists(path) or (runrow is not None and not runrow.get("has_certificate")):
        out["status"] = "no certificate"
        return out
    out["cert_file"] = path
    out["cert_file_sha256"] = sha256_file(path)
    out["cert_sha_matches_runlog"] = (runrow is not None
                                      and runrow.get("cert_sha256") == out["cert_file_sha256"])
    cert = json.load(open(path, encoding="utf-8"))
    body = cert.get("body", cert)
    if body.get("load_error"):
        out["status"] = "load error"
        out["load_error"] = body["load_error"]
        out["verdict"] = body.get("verdict")
        return out
    comps = body.get("components") or []
    comp = comps[0] if comps else None
    out["status"] = "ok"
    out["verdict"] = body.get("verdict")
    out["comp"] = comp
    out["flags"] = list(comp["flags"]) if comp else []
    out["counts"] = comp.get("counts", {}) if comp else {}
    return out


# -------------------------------------------------------------- per-pair rules
def attributable(faulty, fixed, expected):
    exp = set(expected)
    res = {"attributable": False, "generic": False, "declared": False,
           "qualifying": [], "non_qualifying": [], "listed_cases": []}
    # streams carrying a rate flag in the fixed study (fixed bounds; every rate flag counts)
    fixed_rate = {}
    if fixed["status"] == "ok" and fixed["comp"]:
        for f in fixed["flags"]:
            if is_rate_flag(f):
                for s in flag_streams(f, fixed["comp"]):
                    fixed_rate.setdefault(s, []).append(f)
    res["fixed_rate_flag_streams"] = fixed_rate
    if faulty["status"] == "load error":
        res["listed_cases"].append("faulty load error: not a detection")
    if fixed["status"] == "load error":
        res["listed_cases"].append("fixed load error: no stream qualifies")
    if faulty["status"] != "ok" or faulty["verdict"] != "NOT_FALSIFIABLE":
        return res
    for f in faulty["flags"]:
        if f not in exp or not is_rate_flag(f):
            continue
        for s in flag_streams(f, faulty["comp"]):
            entry = {"flag": f, "stream": s}
            reasons = []
            fc = faulty["counts"].get(s)
            xc = fixed["counts"].get(s) if fixed["status"] == "ok" else None
            if fixed["status"] != "ok":
                reasons.append("fixed twin has no usable study (%s)" % fixed["status"])
            elif xc is None:
                reasons.append("fixed study has no count on the stream")
            elif xc.get("hard_undefined", 0) > 0:
                reasons.append("fixed study has hard UNDEFINED on the stream")
                res["listed_cases"].append("hard UNDEFINED on %s" % s)
            if fc is None:
                reasons.append("faulty study has no count on the stream")
            if s in fixed_rate:
                reasons.append("fixed study carries a rate flag on the stream: "
                               + ",".join(fixed_rate[s]))
            if fc is not None:
                entry["faulty"] = [fc["holds"], fc["n"]]
            if xc is not None:
                entry["fixed"] = [xc["holds"], xc["n"]]
            if fc is not None and xc is not None:
                p = fisher_greater(fc["holds"], fc["n"], xc["holds"], xc["n"])
                entry["fisher_p"] = float(p)
                if not fc["holds"] > xc["holds"]:
                    reasons.append("faulty count does not exceed fixed count")
                elif not p < ALPHA:
                    reasons.append("Fisher p >= 0.05")
            if reasons:
                entry["reasons"] = reasons
                res["non_qualifying"].append(entry)
            else:
                res["qualifying"].append(entry)
    qs = sorted({q["stream"] for q in res["qualifying"]})
    res["qualifying_streams"] = qs
    res["attributable"] = bool(res["qualifying"])
    res["generic"] = res["attributable"] and "probe:noise" in qs
    res["declared"] = res["attributable"] and any(s != "probe:noise" for s in qs)
    return res


def evaluate_pair(case, arm, runlog, expected_all):
    exp = expected_all["%s/%s" % (case, EXP_ARM[arm])]["expected"]
    fa = load_twin(case, arm, "faulty", runlog.get((case, arm, "faulty")))
    fx = load_twin(case, arm, "fixed", runlog.get((case, arm, "fixed")))
    r = {"id": case, "arm": arm,
         "faulty_status": fa["status"], "fixed_status": fx["status"],
         "faulty_verdict": fa["verdict"] if fa["status"] == "ok" else None,
         "fixed_verdict": fx["verdict"] if fx["status"] == "ok" else None,
         "faulty_flags": fa["flags"], "fixed_flags": fx["flags"],
         "runlog_verdict_faulty": fa["runlog_verdict"], "runlog_verdict_fixed": fx["runlog_verdict"],
         "cert_sha_matches_runlog": [fa.get("cert_sha_matches_runlog"), fx.get("cert_sha_matches_runlog")],
         "expected_flags": exp}
    causes = []
    for tw, nm in ((fa, "faulty"), (fx, "fixed")):
        if tw["status"] != "ok":
            causes.append("%s twin: %s" % (nm, tw["status"]))
    r["attrition_causes"] = causes
    r["attrition"] = bool(causes)
    # PB-style detection
    exp_present = [f for f in fa["flags"] if f in set(exp)] if fa["status"] == "ok" else []
    r["pb_detected"] = fa["status"] == "ok" and fa["verdict"] == "NOT_FALSIFIABLE" and bool(exp_present)
    r["expected_flags_present"] = exp_present
    r["noise_only"] = r["pb_detected"] and any(f in NOISE_FLAGS for f in exp_present)
    r["declared_only_baseline"] = r["pb_detected"] and any(f not in NOISE_FLAGS for f in exp_present)
    # clean pass
    r["clean_pass"] = fx["status"] == "ok" and fx["verdict"] in ("FALSIFIABLE", "WEAK")
    blocking = [f for f in fx["flags"] if not is_info_flag(f) and f not in NOISE_FLAGS]
    r["fixed_blocking_non_noise_flags"] = blocking if fx["status"] == "ok" else None
    r["clean_pass_no_noise"] = r["clean_pass"] or (
        fx["status"] == "ok" and fx["verdict"] == "NOT_FALSIFIABLE" and not blocking)
    r["flag_everything_detected"] = True
    r["flag_everything_clean"] = False
    # attributable
    a = attributable(fa, fx, exp)
    r.update({"attributable": a["attributable"], "generic": a["generic"], "declared": a["declared"],
              "qualifying_streams": a["qualifying_streams"] if "qualifying_streams" in a else [],
              "qualifying": a["qualifying"], "non_qualifying": a["non_qualifying"],
              "listed_cases": a["listed_cases"], "fixed_rate_flag_streams": a["fixed_rate_flag_streams"]})
    return r


# ----------------------------------------------------------------------- tables
MEASURES = [
    ("pb_detected", "pb_detection"), ("attributable", "attributable"),
    ("generic", "generic"), ("declared", "declared"),
    ("clean_pass", "clean_pass"), ("clean_pass_no_noise", "clean_pass_no_noise"),
    ("noise_only", "noise_only"), ("declared_only_baseline", "declared_only"),
    ("flag_everything_detected", "flag_everything_detection"),
    ("flag_everything_clean", "flag_everything_clean"),
]


def table_for(rows):
    n = len(rows)
    t = {"n": n}
    for key, name in MEASURES:
        x = sum(1 for r in rows if r[key])
        t[name] = {"count": x, "wilson_lower": wilson_lower(x, n)}
    t["generic_only"] = sum(1 for r in rows if r["generic"] and not r["declared"])
    t["declared_only_attributable"] = sum(1 for r in rows if r["declared"] and not r["generic"])
    t["generic_and_declared"] = sum(1 for r in rows if r["generic"] and r["declared"])
    t["attrition_pairs"] = sum(1 for r in rows if r["attrition"])
    return t


def main():
    runlog = load_runlog()
    expected_all = json.load(open(EXPECTED, encoding="utf-8"))["cases"]
    idmap = {x["id"]: x for x in json.load(open(IDMAP, encoding="utf-8"))}
    cases = sorted({k[0] for k in runlog})
    cls = {c: idmap[c]["class"] for c in cases}

    # part B (every audited pair must be yes/yes; none else counts)
    partb = {}
    for sub in sorted(os.listdir(AUDIT_B_DIR)):
        p = os.path.join(AUDIT_B_DIR, sub, "AUDIT_B.json")
        if os.path.exists(p):
            for e in json.load(open(p, encoding="utf-8")):
                partb[e["case"]] = {"X": e["X"], "Y": e["Y"]}
    partb_no = sorted(c for c, v in partb.items() if "yes" not in (v["X"], v["Y"]) or v["X"] != "yes" or v["Y"] != "yes")

    pairs = {a: {} for a in ARMS}
    for a in ARMS:
        for c in cases:
            r = evaluate_pair(c, a, runlog, expected_all)
            r["class"] = cls[c]
            r["part_b"] = partb.get(c)
            if c not in partb:
                r["attrition_causes"].append("no part-B record")
                r["attrition"] = True
            elif c in partb_no:
                r["attrition_causes"].append("part B: no")
                r["attrition"] = True
                r["pb_detected"] = r["attributable"] = r["generic"] = r["declared"] = False
                r["noise_only"] = r["declared_only_baseline"] = False
                r["clean_pass"] = r["clean_pass_no_noise"] = False
            pairs[a][c] = r
    # an attributable miss when the fixed twin has no result (attribution needs the fixed counts)
    for a in ARMS:
        for r in pairs[a].values():
            if r["fixed_status"] != "ok":
                r["attributable"] = r["generic"] = r["declared"] = False

    tables = {}
    for a in ARMS:
        tables[a] = {}
        for k in CLASSES:
            tables[a][k] = table_for([r for r in pairs[a].values() if r["class"] == k])
        tables[a]["decoys(B-1+B-6)"] = table_for(
            [r for r in pairs[a].values() if r["class"] in ("B-1", "B-6")])
        tables[a]["B-2+B-3"] = table_for(
            [r for r in pairs[a].values() if r["class"] in ("B-2", "B-3")])

    # H-D1 / H-D2 (arm W1)
    hd12 = {}
    for h, k in (("H-D1", "B-2"), ("H-D2", "B-3")):
        t = tables["W1"][k]
        n = t["n"]
        att, cl = t["attributable"], t["clean_pass"]
        e = {"class": k, "n": n,
             "attributable": att, "clean_pass": cl,
             "criterion": "one-sided 95% Wilson lower bound >= 0.6 on both; n < 16 is insufficient"}
        if n < 16:
            e["verdict"] = "insufficient cases"
        else:
            ok = (att["wilson_lower"] >= 0.6) and (cl["wilson_lower"] >= 0.6)
            e["verdict"] = "HOLDS" if ok else "FAILS"
        hd12[h] = e

    # H-D3
    pool = [c for c in cases if cls[c] in ("B-2", "B-3")]
    per = []
    for c in pool:
        w1, w0 = pairs["W1"][c], pairs["W0"][c]
        per.append({"id": c, "class": cls[c], "W1_declared": w1["declared"], "W0_declared": w0["declared"],
                    "W1_attrition": w1["attrition_causes"], "W0_attrition": w0["attrition_causes"],
                    "comparable": not (w1["attrition"] or w0["attrition"])})
    comp = [p for p in per if p["comparable"]]
    excl = [p for p in per if not p["comparable"]]

    def discord(items, a_key, b_key):
        b = sum(1 for p in items if p[a_key] and not p[b_key])
        c_ = sum(1 for p in items if p[b_key] and not p[a_key])
        both = sum(1 for p in items if p[a_key] and p[b_key])
        neither = sum(1 for p in items if not p[a_key] and not p[b_key])
        return b, c_, both, neither

    b, c_, both, neither = discord(comp, "W1_declared", "W0_declared")
    p = mcnemar_one_sided(b, c_)
    per_class = {}
    for k in ("B-2", "B-3"):
        items = [x for x in comp if x["class"] == k]
        bb, cc, bo, ne = discord(items, "W1_declared", "W0_declared")
        per_class[k] = {"n_comparable": len(items), "b_W1_only": bb, "c_W0_only": cc,
                        "both": bo, "neither": ne}
    sens_items = []
    for x in per:
        sens_items.append({"id": x["id"], "class": x["class"],
                           "W1": x["W1_declared"] and not x["W1_attrition"],
                           "W0": x["W0_declared"] and not x["W0_attrition"]})
    sb, sc, sboth, sneither = discord(sens_items, "W1", "W0")
    sp = mcnemar_one_sided(sb, sc)
    hd3 = {"pairs_in_pool": len(per), "n_comparable": len(comp),
           "exclusions": [{"id": x["id"], "class": x["class"],
                           "W1": x["W1_attrition"], "W0": x["W0_attrition"]} for x in excl],
           "b_W1_only": b, "c_W0_only": c_, "both": both, "neither": neither,
           "p_exact_one_sided": float(p), "p_fraction": "%d/%d" % (p.numerator, p.denominator),
           "label": "HOLDS" if p < ALPHA else "not demonstrated",
           "per_class": per_class,
           "sensitivity": {"b_W1_only": sb, "c_W0_only": sc, "both": sboth, "neither": sneither,
                           "n": len(sens_items), "p_exact_one_sided": float(sp),
                           "label": "HOLDS" if sp < ALPHA else "not demonstrated"},
           "per_pair": per}

    # clean-pass guard: W0 better than W1 on the pairs entering H-D3, decoys excluded
    gitems = [{"id": x["id"], "class": x["class"],
               "W1": pairs["W1"][x["id"]]["clean_pass"], "W0": pairs["W0"][x["id"]]["clean_pass"]}
              for x in comp]
    gb = sum(1 for g in gitems if g["W0"] and not g["W1"])    # W0 better
    gc = sum(1 for g in gitems if g["W1"] and not g["W0"])    # W1 better
    gp = mcnemar_one_sided(gb, gc)
    dec_diff = {a: sum(1 for r in pairs[a].values() if r["class"] in ("B-1", "B-6") and r["clean_pass"])
                for a in ("W0", "W1")}
    guard = {"n": len(gitems), "b_W0_clean_W1_not": gb, "c_W1_clean_W0_not": gc,
             "both_clean": sum(1 for g in gitems if g["W0"] and g["W1"]),
             "neither_clean": sum(1 for g in gitems if not g["W0"] and not g["W1"]),
             "p_exact_one_sided": float(gp), "p_fraction": "%d/%d" % (gp.numerator, gp.denominator),
             "significant_at_0.05": bool(gp < ALPHA),
             "pooled_W1_minus_W0_clean_pass": sum(g["W1"] for g in gitems) - sum(g["W0"] for g in gitems),
             "decoy_clean_pass_W0": dec_diff["W0"], "decoy_clean_pass_W1": dec_diff["W1"],
             "per_pair": gitems}

    # arm R consistency list (I-D4)
    r_list = [{"id": c, "class": cls[c], "attributable": pairs["R"][c]["attributable"],
               "clean_pass": pairs["R"][c]["clean_pass"]}
              for c in cases if not (pairs["R"][c]["attributable"] and pairs["R"][c]["clean_pass"])]

    # integrity
    integ = {"runlog_verdict_mismatch": [], "cert_sha_mismatch": []}
    for a in ARMS:
        for r in pairs[a].values():
            if r["faulty_verdict"] != r["runlog_verdict_faulty"]:
                integ["runlog_verdict_mismatch"].append([r["id"], a, "faulty"])
            if r["fixed_verdict"] != r["runlog_verdict_fixed"]:
                integ["runlog_verdict_mismatch"].append([r["id"], a, "fixed"])
            for tw, ok in zip(("faulty", "fixed"), r["cert_sha_matches_runlog"]):
                if ok is not True:
                    integ["cert_sha_mismatch"].append([r["id"], a, tw])

    out = {
        "script": os.path.abspath(__file__),
        "script_sha256": sha256_file(os.path.abspath(__file__)),
        "inputs": {"RUNLOG.jsonl": sha256_file(RUNLOG), "EXPECTED_FLAGS_D.json": sha256_file(EXPECTED),
                   "ID_MAP_D.json": sha256_file(IDMAP)},
        "assumptions": [
            "pair set = the 20 cases in RUNLOG (reserve flag not used); classes from ID_MAP_D.json",
            "clean pass without the noise stream: clean verdict, or NOT_FALSIFIABLE whose every flag is informational "
            "(K5_INCONCLUSIVE:*, K1_ABSTAINED*, K2_MINUS_UNREAD, K8_SOME_CHANGES, BAD_RETURN) or a noise flag "
            "(K5_HOLDS_ON_NOISE, HIGH_RATE:probe:noise)",
            "noise-only / declared-only baselines: faulty NOT_FALSIFIABLE and an expected flag that is (is not) a noise flag; "
            "their clean pass equals the PB-style clean pass; flag-everything: all faulty detected, no fixed passes",
            "attrition: twin without certificate / timeout / load error; part B all yes; no invalid skeletons",
        ],
        "cases": cases, "classes": cls,
        "part_b_no": partb_no, "integrity": integ,
        "pairs": pairs, "tables": tables,
        "H-D1_H-D2": hd12, "H-D3": hd3, "clean_pass_guard": guard,
        "arm_R_not_attributable_or_not_clean": r_list,
    }
    with open(os.path.join(HERE, "RECOMPUTE_D.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    # ------------------------------------------------------------------ markdown
    def fmt(m):
        lb = m["wilson_lower"]
        return "%d (%s)" % (m["count"], "-" if lb is None else "%.3f" % lb)

    def yn(b):
        return "Y" if b else "-"
    L = ["# RECOMPUTE_D (designer, independent)", "",
         "Script sha256: `%s`" % out["script_sha256"], "",
         "Counts with one-sided 95% Wilson lower bound in brackets. n = pairs.", ""]
    for a in ARMS:
        L += ["## Arm %s" % a, "",
              "| group | n | pb-det | attributable | generic | declared | clean | clean w/o noise | noise-only | declared-only | flag-everything det |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, t in tables[a].items():
            L.append("| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                k, t["n"], fmt(t["pb_detection"]), fmt(t["attributable"]), fmt(t["generic"]),
                fmt(t["declared"]), fmt(t["clean_pass"]), fmt(t["clean_pass_no_noise"]),
                fmt(t["noise_only"]), fmt(t["declared_only"]), fmt(t["flag_everything_detection"])))
        L.append("")
    L += ["## H-D1 / H-D2 (arm W1)", ""]
    for h, e in hd12.items():
        L.append("- %s (%s): n=%d, attributable %s, clean %s -> **%s**" % (
            h, e["class"], e["n"], fmt(e["attributable"]), fmt(e["clean_pass"]), e["verdict"]))
    L += ["", "## H-D3 (B-2+B-3, declared attributable, W1 vs W0)", "",
          "- pool %d, comparable %d; b (W1 only) = %d, c (W0 only) = %d, both = %d, neither = %d; p = %.6f (%s) -> **%s**" % (
              hd3["pairs_in_pool"], hd3["n_comparable"], b, c_, both, neither, hd3["p_exact_one_sided"],
              hd3["p_fraction"], hd3["label"]),
          "- per class: " + "; ".join("%s b=%d c=%d (n=%d)" % (k, v["b_W1_only"], v["c_W0_only"], v["n_comparable"])
                                      for k, v in per_class.items()),
          "- exclusions: %s" % (hd3["exclusions"] or "none"),
          "- sensitivity: b=%d c=%d p=%.6f -> %s" % (sb, sc, sp, hd3["sensitivity"]["label"]),
          "", "## Clean-pass guard (W0 better than W1; decoys excluded)", "",
          "- n=%d; b (W0 clean, W1 not) = %d; c (W1 clean, W0 not) = %d; p = %.6f (%s); significant: %s" % (
              guard["n"], gb, gc, guard["p_exact_one_sided"], guard["p_fraction"], guard["significant_at_0.05"]),
          "- pooled W1 minus W0 clean pass: %d; decoys clean pass W0 %d, W1 %d" % (
              guard["pooled_W1_minus_W0_clean_pass"], dec_diff["W0"], dec_diff["W1"]),
          "", "## Per pair", "",
          "| id | class | arm | faulty | fixed | pb-det | attrib | generic | declared | clean | clean w/o noise | qualifying streams | attrition |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cases:
        for a in ARMS:
            r = pairs[a][c]
            qs = "; ".join("%s (%d/%d vs %d/%d, p=%.3g)" % (
                q["stream"], q["faulty"][0], q["faulty"][1], q["fixed"][0], q["fixed"][1], q["fisher_p"])
                for q in r["qualifying"]) or "-"
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                c, cls[c], a, r["faulty_verdict"], r["fixed_verdict"], yn(r["pb_detected"]),
                yn(r["attributable"]), yn(r["generic"]), yn(r["declared"]), yn(r["clean_pass"]),
                yn(r["clean_pass_no_noise"]), qs, "; ".join(r["attrition_causes"]) or "-"))
    L += ["", "Integrity: runlog verdict mismatches %d; certificate sha mismatches %d; part-B no: %s" % (
        len(integ["runlog_verdict_mismatch"]), len(integ["cert_sha_mismatch"]), partb_no or "none"), ""]
    with open(os.path.join(HERE, "RECOMPUTE_D.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[:3]))
    print("H-D1/H-D2:", {h: e["verdict"] for h, e in hd12.items()})
    print("H-D3: b=%d c=%d p=%.6f %s" % (b, c_, hd3["p_exact_one_sided"], hd3["label"]))
    print("guard: b=%d c=%d p=%.6f" % (gb, gc, guard["p_exact_one_sided"]))
    print("integrity:", {k: len(v) for k, v in integ.items()})


if __name__ == "__main__":
    main()
