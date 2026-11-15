"""Designer's independent recomputation of the Phase C numbers (PREREG_PHASE_C section 7: "the designer recomputes every
number from the certificates with a separate script written without reading the runner").

Written from PREREG_PHASE_C.md sections 6-7, PREREG_PHASE_B.md section 6, REVISIONS-post-freeze.md P-7 and the
certificate format only. The Phase C runner and the Phase B runner were NOT read.

Usage:
  py recompute_designer.py [--run DIR] [--out FILE] [--timeouts LIST] [--repo DIR] [--r1 DIR] [--record DIR]
  py recompute_designer.py --phase-b-abstention-only [--out FILE]
  py recompute_designer.py --selftest

  --run DIR      run folder with certs/<version>/<case>/<twin>.json (version v050 or v041, twin faulty or fixed)
                 default E:\\Claude Projects\\kapi-oss\\evaluation\\phase_c\\run
  --timeouts L   comma list of version:case:twin (for example v050:B1-01:fixed) for checks that ran beyond 3600 s:
                 a miss / failed clean pass in that version's table, "not comparable" in the primary comparison
  --out FILE     also write the text report to FILE (utf-8)

A missing certificate, an unreadable certificate or a certificate with a load error is a miss (faulty) or a failed
clean pass (fixed). Output is plain ASCII text, deterministic (no clocks, no randomness).
"""
import argparse
import json
import math
import os
import sys
import tempfile

EVAL = r"E:\Claude Projects\kapi-oss\evaluation"
DEFAULTS = dict(
    run=os.path.join(EVAL, "phase_c", "run"),
    expected_c=os.path.join(EVAL, "phase_c", "EXPECTED_FLAGS.json"),
    awareness=os.path.join(EVAL, "phase_c", "record", "designer", "AWARENESS_RESULT.json"),
    lines=os.path.join(EVAL, "phase_c", "record", "designer", "DESIGNER_LINES.json"),
    expected_b=os.path.join(EVAL, "phase_b", "EXPECTED_FLAGS.json"),
    r1=os.path.join(EVAL, "r1_v050", "certs"),
)

Z = 1.6448536269514722          # one-sided 95%
SCOPE = ["B-1", "B-2", "B-3", "B-6"]
CLASSES = SCOPE + ["O"]
VERSIONS = [("v050", "0.5.0"), ("v041", "0.4.1")]
TWINS = ["faulty", "fixed"]
NOISE = {"K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"}
K2ONLY = {"K2_NO_SEPARATION", "K2_FAILS_UNREACHABLE"}
INFO_EXACT = {"K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN"}
K1_STREAMS = ["world:plus", "world:minus", "world:null"]
ADDENDUM_SOURCES = {"KRI10", "MOR03", "VAR06", "CUR13", "LAZ18"}
SEVERITY = {"FALSIFIABLE": 0, "WEAK": 1, "UNTESTED": 2, "NOT_FALSIFIABLE": 3, "UNDEFINED": 4}
NOT_COMPARABLE = ("MISSING", "TIMEOUT", "UNREADABLE")
NOT_INFORMATIVE_BELOW = 5

READINGS = [
    "Readings fixed in this script (see the final message of the author of the script):",
    "R1 detection: file ok (certificate present, readable, no load_error, no timeout), STUDY verdict NOT_FALSIFIABLE, and at",
    "   least one component carries a flag of the case's expected list. Information flags and K1_ABSTAINED* are removed",
    "   from the list before use. Labels: generic = a noise flag is among the expected flags found, else declared;",
    "   K2-only = every expected flag found is K2_NO_SEPARATION or K2_FAILS_UNREACHABLE (reported in addition).",
    "R2 clean pass: fixed file ok and STUDY verdict FALSIFIABLE or WEAK.",
    "R3 threshold per in-scope class: n >= 10, one-sided 95% Wilson lower bound of detection >= 0.6 and of clean pass >= 0.6.",
    "   Fewer than 10 pairs: INSUFFICIENT. B-2 subtype rows show the class rule (both bounds >= 0.6 -> HOLDS, else FAILS)",
    "   marked descriptive (P-8 item 5); O and the without-overlap tables carry no threshold (descriptive).",
    "R4 baselines: noise-only / declared-only detection = NOT_FALSIFIABLE plus a noise / a non-noise expected flag;",
    "   clean passes of the baselines equal the gate's; flag-everything = every faulty detected, no fixed passing.",
    "R5 primary comparison unit = the component verdict of the file (single component; study verdict when no component).",
    "   A 0.4.1 UNDEFINED component = certificate ok and component verdict UNDEFINED. Cause (P-7 item 3) from the 0.5.0",
    "   certificate. Comparable = certificate present (no timeout) in both versions; a gain or loss is judged on comparable files.",
    "   Not informative when fewer than 5 of all Phase C files (faulty and fixed, all classes incl. O) are UNDEFINED under 0.4.1.",
    "R6 abstention share (P-7 item 4) = sum(undefined - hard_undefined) / sum(n) over world:plus, world:minus, world:null",
    "   of the components of ok 0.5.0 certificates; files without certificate or component do not enter.",
    "R7 'error too small' (P-7 item 5, P-8 item 4): a miss, file ok with one component, faulty study verdict WEAK or",
    "   FALSIFIABLE, no expected flag found, world:minus holds/n <= 0.05 + 2*sqrt(0.05*0.95/n).",
]


# ------------------------------------------------------------------ small helpers
def wilson_lower(k, n):
    if n == 0:
        return float("nan")
    p = k / n
    den = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return max(0.0, centre - half)


def fnum(x, nd=4):
    return "n/a" if x != x else f"{x:.{nd}f}"


def is_info(flag):
    return flag in INFO_EXACT or flag.startswith("K1_ABSTAINED")


def case_sort_key(cid):
    return cid


def share(num, den):
    return "n/a" if den == 0 else f"{num / den:.4f}"


# ------------------------------------------------------------------ reading certificates
def read_file(run, version, case, twin, timeouts):
    """Returns a dict describing one study file's certificate."""
    fi = dict(version=version, case=case, twin=twin, status="MISSING", body=None, ok=False, study=None,
              comps=[], comp=None, flags=set(), load_error=None)
    if (version, case, twin) in timeouts:
        fi["status"] = "TIMEOUT"
        return fi
    path = os.path.join(run, "certs", version, case, twin + ".json")
    if not os.path.exists(path):
        return fi
    try:
        j = json.load(open(path, encoding="utf-8"))
        body = j["body"] if isinstance(j, dict) and "body" in j else j
        if not isinstance(body, dict):
            raise ValueError("body is not an object")
    except Exception:
        fi["status"] = "UNREADABLE"
        return fi
    fi["body"] = body
    fi["study"] = body.get("verdict")
    fi["comps"] = body.get("components") or []
    fi["load_error"] = body.get("load_error")
    for c in fi["comps"]:
        fi["flags"].update(c.get("flags", []) or [])
    if fi["comps"]:
        vs = [c.get("verdict") for c in fi["comps"]]
        fi["comp"] = max(vs, key=lambda v: SEVERITY.get(v, -1))
    if fi["load_error"]:
        fi["status"] = "LOAD_ERROR"
        return fi
    fi["status"] = "OK"
    fi["ok"] = True
    return fi


def counts_of(fi, stream):
    """Sum (holds, n, undefined, hard_undefined, has_hard_key) of a stream over the components."""
    h = n = u = hu = 0
    found = False
    has_hard = True
    for c in fi["comps"]:
        cc = (c.get("counts") or {}).get(stream)
        if cc is None:
            continue
        found = True
        h += cc.get("holds", 0)
        n += cc.get("n", 0)
        u += cc.get("undefined", 0)
        if "hard_undefined" in cc:
            hu += cc["hard_undefined"]
        else:
            has_hard = False
    return (h, n, u, hu, has_hard) if found else None


# ------------------------------------------------------------------ rows
def build_rows(inp, run, version, timeouts, warnings):
    rows = {}
    for cid in sorted(inp["exp"], key=case_sort_key):
        e = inp["exp"][cid]
        listed = set(e["expected"])
        info_in_list = sorted(f for f in listed if is_info(f))
        if info_in_list:
            warnings.append(f"{cid}: information flags in the expected list were ignored: {','.join(info_in_list)}")
        ex = {f for f in listed if not is_info(f)}
        fb = read_file(run, version, cid, "faulty", timeouts)
        xb = read_file(run, version, cid, "fixed", timeouts)
        present = sorted(fb["flags"] & ex)
        det = fb["ok"] and fb["study"] == "NOT_FALSIFIABLE" and bool(present)
        det_noise = det and bool(set(present) & NOISE)
        det_decl = det and bool(set(present) - NOISE)
        label = ""
        if det:
            label = "generic" if (set(present) & NOISE) else "declared"
        k2only = det and set(present) <= K2ONLY
        clean = xb["ok"] and xb["study"] in ("FALSIFIABLE", "WEAK")
        wid = e.get("world_id")
        aw = inp["aw"].get(wid)
        dl = inp["dl"].get(cid)
        if aw is None:
            warnings.append(f"{cid}: world {wid} has no awareness entry")
        if dl is None:
            warnings.append(f"{cid}: no designer line (overlap unknown, counted as no overlap)")
        ovl = bool(dl and str(dl.get("overlap", "")).startswith("yes"))
        rows[cid] = dict(case=cid, cls=e["class"], sub=e.get("subtype") or "", source=e.get("source", ""), world=wid,
                         aw=(aw or {}).get("resolved", "?"), no_log=bool((aw or {}).get("no_log")),
                         r1=(aw or {}).get("reader1", "?"), r2=(aw or {}).get("reader2", "?"),
                         ovl=ovl, ovl_text=(dl or {}).get("overlap", "?"), f=fb, x=xb, present=present, det=det,
                         det_noise=det_noise, det_decl=det_decl, label=label, k2only=k2only, clean=clean,
                         xflags=sorted(xb["flags"]) if not clean else [])
    return rows


def block_stats(rs):
    n = len(rs)
    d = sum(r["det"] for r in rs)
    c = sum(r["clean"] for r in rs)
    s = dict(n=n, det=d, clean=c,
             gen=sum(r["label"] == "generic" for r in rs), decl=sum(r["label"] == "declared" for r in rs),
             k2=sum(r["k2only"] for r in rs), dn=sum(r["det_noise"] for r in rs), dd=sum(r["det_decl"] for r in rs))
    s["lbd"], s["lbc"] = wilson_lower(d, n), wilson_lower(c, n)
    s["holds"] = n >= 10 and s["lbd"] >= 0.6 and s["lbc"] >= 0.6
    s["rule"] = s["lbd"] >= 0.6 and s["lbc"] >= 0.6
    return s


def fmt_block(name, rs, threshold):
    s = block_stats(rs)
    rule = "HOLDS" if (s["lbd"] >= 0.6 and s["lbc"] >= 0.6) else "FAILS"
    if threshold == "rule":
        verdict = f"class-rule {rule} (descriptive; not a class verdict)"
    elif threshold:
        verdict = "INSUFFICIENT(n<10)" if s["n"] < 10 else ("HOLDS" if s["holds"] else "FAILS")
    else:
        verdict = "descriptive"
    line = (f"{name:16} pairs={s['n']:2} det={s['det']:2} (generic {s['gen']}, declared {s['decl']}, K2-only {s['k2']})"
            f" clean={s['clean']:2} LBdet={fnum(s['lbd'])} LBclean={fnum(s['lbc'])} {verdict}")
    return line, s, verdict


def baseline_lines(rs):
    s = block_stats(rs)
    n = s["n"]
    ok_all = lambda d: n >= 10 and wilson_lower(d, n) >= 0.6 and s["lbc"] >= 0.6
    out = [f"    noise-only      det={s['dn']:2} LBdet={fnum(wilson_lower(s['dn'], n))} clean={s['clean']:2} "
           f"LBclean={fnum(s['lbc'])} would-pass-threshold={'yes' if ok_all(s['dn']) else 'no'}",
           f"    declared-only   det={s['dd']:2} LBdet={fnum(wilson_lower(s['dd'], n))} clean={s['clean']:2} "
           f"LBclean={fnum(s['lbc'])} would-pass-threshold={'yes' if ok_all(s['dd']) else 'no'}",
           f"    flag-everything det={n:2} LBdet={fnum(wilson_lower(n, n))} clean= 0 LBclean={fnum(wilson_lower(0, n))} "
           f"would-pass-threshold=no"]
    return out


def verdict_cell(fi):
    if fi["status"] in ("MISSING", "TIMEOUT", "UNREADABLE", "LOAD_ERROR"):
        return fi["status"]
    return fi["study"] or "?"


# ------------------------------------------------------------------ version section
def version_section(vkey, vname, rows, out, with_too_small):
    out.append("")
    out.append("=" * 100)
    out.append(f"TRUTH_GATE {vname} ({vkey}) - detection, clean pass, thresholds")
    out.append("=" * 100)
    got = sum(r["f"]["status"] != "MISSING" or r["x"]["status"] != "MISSING" for r in rows.values())
    out.append(f"certificates present for {got} of {len(rows)} pairs (a missing certificate is a miss / failed clean pass)")
    out.append("")
    out.append("-- in-scope classes (threshold: both one-sided 95% Wilson lower bounds >= 0.6, n >= 10) --")
    res = {}
    for cls in SCOPE:
        rs = [r for r in rows.values() if r["cls"] == cls]
        line, s, v = fmt_block(cls, rs, True)
        out.append(line)
        res[cls] = (s, v)
        for l in baseline_lines(rs):
            out.append(l)
    out.append("")
    out.append("-- B-2 subtypes (result of the class rule shown, descriptive; the threshold applies to the class) --")
    for sub in sorted({r["sub"] for r in rows.values() if r["cls"] == "B-2"}):
        line, s, v = fmt_block("B-2 " + sub, [r for r in rows.values() if r["cls"] == "B-2" and r["sub"] == sub], "rule")
        out.append(line)
    out.append("")
    out.append("-- out of scope (descriptive, no threshold) --")
    for sub in sorted({r["sub"] for r in rows.values() if r["cls"] == "O"}):
        line, s, v = fmt_block("O " + sub, [r for r in rows.values() if r["cls"] == "O" and r["sub"] == sub], False)
        out.append(line)
    line, s, v = fmt_block("O all", [r for r in rows.values() if r["cls"] == "O"], False)
    out.append(line)
    out.append("")
    out.append("-- without the pairs that overlap Phase B (descriptive) --")
    for cls in SCOPE + ["O"]:
        rs = [r for r in rows.values() if r["cls"] == cls and not r["ovl"]]
        line, s, v = fmt_block(cls + " no-overlap", rs, False)
        out.append(line)
    out.append("")
    out.append("-- per pair --")
    for r in rows.values():
        out.append(f"{r['case']:6} {r['cls']:4} {r['sub']:5} {r['source']:6} faulty={verdict_cell(r['f']):16}"
                   f" det={'Y' if r['det'] else 'n'} {r['label']:8}{' K2only' if r['k2only'] else ''}"
                   f" [{','.join(r['present'])}] | fixed={verdict_cell(r['x']):16} clean={'Y' if r['clean'] else 'n'}"
                   f" [{','.join(r['xflags'])}]")
    return res


# ------------------------------------------------------------------ overlap, sources
def overlap_section(rows, out):
    out.append("")
    out.append("=" * 100)
    out.append("OVERLAP WITH PHASE B AND NEW SOURCES (descriptive; PREREG section 1, P-7 items 6 and 7)")
    out.append("=" * 100)
    res = {}
    for cls in SCOPE:
        rs = [r for r in rows.values() if r["cls"] == cls]
        k = sum(r["ovl"] for r in rs)
        add = sum(r["source"] in ADDENDUM_SOURCES for r in rs)
        wording = 2 * k > len(rs)
        res[cls] = dict(n=len(rs), overlap=k, addendum=add, wording=wording)
        out.append(f"{cls}: pairs={len(rs)} overlapping Phase B={k} addendum-source pairs={add} "
                   f"new-source minimum (>=4) {'met' if add >= 4 else 'not met'}"
                   + (" | MORE THAN HALF OVERLAP: this class's Phase C result \"largely repeats Phase B settings with a new"
                      " world author\" and is not presented as separate evidence" if wording else ""))
    return res


# ------------------------------------------------------------------ primary comparison
def cause_of(f50):
    """P-7 item 3, from the 0.5.0 certificate of the same file."""
    if f50["status"] in ("MISSING", "TIMEOUT", "UNREADABLE"):
        return "unknown"
    if not f50["comps"]:
        return "unknown"
    for st in K1_STREAMS:
        c = counts_of(f50, st)
        if c is not None and c[3] > 0:
            return "hard"
    c = counts_of(f50, "world:plus")
    if c is not None and 2 * c[2] > c[1]:
        return "plus majority"
    return "soft only"


def comp_verdict_str(fi):
    if fi["status"] in NOT_COMPARABLE:
        return fi["status"]
    if fi["status"] == "LOAD_ERROR":
        return "LOAD_ERROR"
    return fi["comp"] if fi["comp"] else "NO_COMPONENT"


def comparison_section(r50, r41, out):
    out.append("")
    out.append("=" * 100)
    out.append("PRIMARY COMPARISON 0.5.0 vs 0.4.1 (PREREG section 6, P-7 item 3; unit: the component of each file)")
    out.append("=" * 100)
    files = []
    for cid in r50:
        for twin in TWINS:
            f50 = r50[cid]["f" if twin == "faulty" else "x"]
            f41 = r41[cid]["f" if twin == "faulty" else "x"]
            files.append((cid, twin, r50[cid]["cls"], f41, f50))
    undef = []
    for cid, twin, cls, f41, f50 in files:
        if f41["ok"] and f41["comp"] == "UNDEFINED":
            undef.append((cid, twin, cls, cause_of(f50)))
    informative = len(undef) >= NOT_INFORMATIVE_BELOW
    res = dict(n_files=len(files), n_undef=len(undef), informative=informative, undef=undef)
    out.append(f"files with a 0.4.1 component verdict UNDEFINED: {len(undef)} of {len(files)} "
               f"(threshold for an informative comparison: at least {NOT_INFORMATIVE_BELOW})")
    out.append("list (case:twin class cause):")
    for cid, twin, cls, cause in undef:
        out.append(f"   {cid}:{twin} {cls} cause={cause}")
    if not undef:
        out.append("   (none)")
    # not comparable
    nc = [f"{cid}:{twin}({f41['status'] if f41['status'] in NOT_COMPARABLE else f50['status']})"
          for cid, twin, cls, f41, f50 in files if f41["status"] in NOT_COMPARABLE or f50["status"] in NOT_COMPARABLE]
    res["not_comparable"] = nc
    out.append(f"not comparable (certificate missing or timeout in a version), {len(nc)}: " + (" ".join(nc) or "none"))

    # pair-level gains and losses (needed in both cases: a loss is always reported)
    gains_det, gains_clean, loss_det, loss_clean = [], [], [], []
    for cid in r50:
        a, b = r50[cid], r41[cid]
        if a["f"]["status"] not in NOT_COMPARABLE and b["f"]["status"] not in NOT_COMPARABLE:
            if a["det"] and not b["det"]:
                gains_det.append(cid)
            if b["det"] and not a["det"]:
                loss_det.append(cid)
        if a["x"]["status"] not in NOT_COMPARABLE and b["x"]["status"] not in NOT_COMPARABLE:
            if a["clean"] and not b["clean"]:
                gains_clean.append(cid)
            if b["clean"] and not a["clean"]:
                loss_clean.append(cid)
    res.update(gains_det=gains_det, gains_clean=gains_clean, loss_det=loss_det, loss_clean=loss_clean)

    # verdict moves of components
    moved = [(cid, twin, cls, comp_verdict_str(f41), comp_verdict_str(f50))
             for cid, twin, cls, f41, f50 in files
             if f41["status"] not in NOT_COMPARABLE and f50["status"] not in NOT_COMPARABLE
             and comp_verdict_str(f41) != comp_verdict_str(f50)]
    anomalies = [m for m in moved if m[3] != "UNDEFINED"]
    res["moved"] = moved
    res["anomalies"] = anomalies
    res["hidden_misses"] = [(c, t) for c, t, k, a, b in moved if t == "faulty" and a == "UNDEFINED" and b in ("FALSIFIABLE", "WEAK")]
    res["hidden_alarms"] = [(c, t) for c, t, k, a, b in moved if t == "fixed" and a == "UNDEFINED" and b == "NOT_FALSIFIABLE"]

    out.append("")
    out.append("LOSSES (by spec 0.7 section 4 none can occur; a loss counts against 0.5.0, whatever a later release does):")
    out.append("   detections lost : " + (" ".join(loss_det) or "none"))
    out.append("   clean passes lost: " + (" ".join(loss_clean) or "none"))
    out.append("anomalies (component verdict changed although 0.4.1 was not UNDEFINED; 0.5.0 should change only UNDEFINED):")
    for cid, twin, cls, a, b in anomalies:
        out.append(f"   {cid}:{twin} {cls} {a} -> {b}")
    if not anomalies:
        out.append("   none")

    if not informative:
        out.append("")
        out.append(f"RESULT: NOT INFORMATIVE (fewer than {NOT_INFORMATIVE_BELOW} files have a 0.4.1 UNDEFINED component); "
                   "the list above is the report, no per-class statement is made.")
        return res

    out.append("")
    out.append("per class (informative comparison):")
    any_change = bool(undef or gains_det or gains_clean or loss_det or loss_clean or moved)
    for cls in CLASSES:
        cu = [u for u in undef if u[2] == cls]
        causes = {}
        for u in cu:
            causes[u[3]] = causes.get(u[3], 0) + 1
        cmaj = sorted(f"{cid}:{twin}" for cid, twin, c, f41, f50 in files
                      if c == cls and any(fl.startswith("K1_ABSTAINED_MAJORITY") for fl in f50["flags"]))
        gd = [c for c in gains_det if r50[c]["cls"] == cls]
        gc = [c for c in gains_clean if r50[c]["cls"] == cls]
        ld = [c for c in loss_det if r50[c]["cls"] == cls]
        lc = [c for c in loss_clean if r50[c]["cls"] == cls]
        hm = [f"{c}" for c, t in res["hidden_misses"] if r50[c]["cls"] == cls]
        ha = [f"{c}" for c, t in res["hidden_alarms"] if r50[c]["cls"] == cls]
        out.append(f"{cls}: undefined under 0.4.1={len(cu)} causes={dict(sorted(causes.items()))}")
        out.append(f"    detections gained : {' '.join(gd) or 'none'}")
        out.append(f"    clean passes gained: {' '.join(gc) or 'none'}")
        out.append(f"    faulty UNDEFINED->FALSIFIABLE/WEAK (misses 0.4.1 hid): {' '.join(hm) or 'none'}")
        out.append(f"    fixed UNDEFINED->NOT_FALSIFIABLE (false alarms 0.4.1 hid): {' '.join(ha) or 'none'}")
        out.append(f"    losses: detections {' '.join(ld) or 'none'}; clean passes {' '.join(lc) or 'none'}")
        out.append(f"    components with K1_ABSTAINED_MAJORITY (0.5.0): {' '.join(cmaj) or 'none'}")
    out.append("")
    out.append("all component verdict moves 0.4.1 -> 0.5.0 (comparable files):")
    for cid, twin, cls, a, b in moved:
        out.append(f"   {cid}:{twin} {cls} {a} -> {b}")
    if not moved:
        out.append("   none")
    if not any_change:
        out.append("RESULT: NO CHANGE")
    return res


# ------------------------------------------------------------------ abstention
def k1_abstention(fi, acc, warnings=None):
    """Adds soft undefined and n of the K1 streams of one ok file to acc = [num, den, files]."""
    if not fi["ok"] or not fi["comps"]:
        return
    acc[2] += 1
    for st in K1_STREAMS:
        c = counts_of(fi, st)
        if c is None:
            continue
        h, n, u, hu, has_hard = c
        acc[0] += u - hu
        acc[1] += n
        if not has_hard and warnings is not None:
            warnings.append(f"{fi['case']}:{fi['twin']} {st}: no hard_undefined in counts (treated as 0)")


def abstention_c(r50, warnings):
    res = {}
    for cls in CLASSES:
        for twin in TWINS:
            acc = [0, 0, 0]
            for r in r50.values():
                if r["cls"] == cls:
                    k1_abstention(r["f" if twin == "faulty" else "x"], acc, warnings)
            res[(cls, twin)] = tuple(acc)
    return res


def phase_b_abstention(r1_dir, pb_cases, warnings=None):
    res = {}
    missing = {}
    for cls in CLASSES:
        for twin in TWINS:
            acc = [0, 0, 0]
            miss = 0
            for cid in sorted(pb_cases):
                if pb_cases[cid]["class"] != cls:
                    continue
                path = os.path.join(r1_dir, f"evaluation__phase_b__cases__{cid}__{twin}.py.json")
                if not os.path.exists(path):
                    miss += 1
                    continue
                try:
                    j = json.load(open(path, encoding="utf-8"))
                    body = j["body"] if "body" in j else j
                except Exception:
                    miss += 1
                    continue
                fi = dict(case=cid, twin=twin, ok=not body.get("load_error"), comps=body.get("components") or [])
                k1_abstention(fi, acc, warnings)
            res[(cls, twin)] = tuple(acc)
            missing[(cls, twin)] = miss
    return res, missing


def abstention_text(c_res, b_res, b_missing, out, title):
    out.append("")
    out.append("=" * 100)
    out.append(title)
    out.append("=" * 100)
    out.append("share = sum(undefined - hard_undefined) / sum(n) over world:plus, world:minus, world:null of 0.5.0 certificates")
    out.append("class  twin     Phase C share (num/den, files)         Phase B share (num/den, files, missing)")
    for cls in CLASSES:
        for twin in TWINS:
            cn, cd, cf = c_res[(cls, twin)] if c_res is not None else (0, 0, 0)
            bn, bd, bf = b_res[(cls, twin)]
            cpart = "-" if c_res is None else f"{share(cn, cd)} ({cn}/{cd}, {cf} files)"
            out.append(f"{cls:5}  {twin:7}  {cpart:38} {share(bn, bd)} ({bn}/{bd}, {bf} files, {b_missing[(cls, twin)]} missing)")


# ------------------------------------------------------------------ awareness
def awareness_section(r50, out):
    out.append("")
    out.append("=" * 100)
    out.append("AWARENESS (resolved reading; 'no log' counted in P and shown on its own) - declared worlds that may contain"
               " what the error exploits")
    out.append("=" * 100)
    res = {}
    for cls in CLASSES:
        rs = [r for r in r50.values() if r["cls"] == cls]
        n = len(rs)
        cnt = {lv: sum(r["aw"] == lv for r in rs) for lv in "PCN"}
        unk = sum(r["aw"] not in ("P", "C", "N") for r in rs)
        nolog = sum(r["no_log"] for r in rs)
        res[cls] = dict(n=n, P=cnt["P"], C=cnt["C"], N=cnt["N"], no_log=nolog, unknown=unk)
        out.append(f"{cls:4} n={n:2} P={cnt['P']} ({share(cnt['P'], n)}) C={cnt['C']} ({share(cnt['C'], n)}) "
                   f"N={cnt['N']} ({share(cnt['N'], n)}) of which no-log (in P)={nolog} unknown={unk}")
        r1c = {lv: sum(r["r1"] == lv for r in rs) for lv in ("P", "C", "N", "no log")}
        r2c = {lv: sum(r["r2"] == lv for r in rs) for lv in ("P", "C", "N", "no log")}
        out.append(f"       reader1 {r1c}  reader2 {r2c}")
    out.append("")
    out.append("0.5.0 detections and clean passes by resolved level (descriptive):")
    for lv in "PCN":
        for cls in CLASSES:
            rs = [r for r in r50.values() if r["aw"] == lv and r["cls"] == cls]
            if rs:
                out.append(f"   {lv} {cls:4} n={len(rs):2} det={sum(r['det'] for r in rs):2} "
                           f"(generic {sum(r['label'] == 'generic' for r in rs)}, declared {sum(r['label'] == 'declared' for r in rs)},"
                           f" K2-only {sum(r['k2only'] for r in rs)}) clean={sum(r['clean'] for r in rs):2}")
    return res


# ------------------------------------------------------------------ error too small
def too_small_section(r50, out):
    out.append("")
    out.append("=" * 100)
    out.append("'ERROR TOO SMALL IN THE DECLARED WORLDS AT THIS SIZE' (0.5.0 misses; P-7 item 5)")
    out.append("=" * 100)
    labelled = []
    for r in r50.values():
        f = r["f"]
        if r["det"]:
            continue
        line = f"{r['case']:6} {r['cls']:4} miss: faulty={verdict_cell(f)}"
        if not f["ok"] or r["present"] or f["study"] not in ("WEAK", "FALSIFIABLE") or len(f["comps"]) != 1:
            if not f["ok"]:
                reason = "no certificate/load error"
            elif r["present"]:
                reason = f"has expected flag(s) {','.join(r['present'])}"
            elif len(f["comps"]) != 1:
                reason = f"{len(f['comps'])} components"
            else:
                reason = f"study verdict {f['study']} is not WEAK or FALSIFIABLE (P-8 item 4)"
            out.append(line + f" -> no label ({reason})")
            continue
        c = counts_of(f, "world:minus")
        if c is None or c[1] == 0:
            out.append(line + " -> no label (no world:minus counts)")
            continue
        h, n = c[0], c[1]
        thr = 0.05 + 2 * math.sqrt(0.05 * 0.95 / n)
        rate = h / n
        lab = rate <= thr
        if lab:
            labelled.append(r["case"])
        out.append(line + f" minus holds/n={h}/{n}={rate:.4f} bound={thr:.4f} -> "
                   + ("LABEL: error too small in the declared worlds at this size" if lab else "no label (minus rate above bound)"))
    out.append(f"labelled pairs ({len(labelled)}): " + (" ".join(labelled) or "none"))
    return labelled


# ------------------------------------------------------------------ whole report
def load_inputs(a):
    exp = json.load(open(a["expected_c"], encoding="utf-8"))["cases"]
    aw = json.load(open(a["awareness"], encoding="utf-8"))["ids"]
    dl = json.load(open(a["lines"], encoding="utf-8"))
    pb = json.load(open(a["expected_b"], encoding="utf-8"))["cases"]
    return dict(exp=exp, aw=aw, dl=dl, pb=pb, r1=a["r1"])


def build_report(inp, run, timeouts):
    out, warnings = [], []
    out.append("PHASE C - designer's recomputation (independent of the runner)")
    out.append(f"run folder: {run}")
    out.append(f"pairs in EXPECTED_FLAGS.json: {len(inp['exp'])}; timeouts given: {sorted(':'.join(t) for t in timeouts) or 'none'}")
    out.append("")
    out.extend(READINGS)
    R = {}
    rows = {}
    for vkey, vname in VERSIONS:
        rows[vkey] = build_rows(inp, run, vkey, timeouts, warnings)
    R["rows"] = rows
    R["v050"] = version_section("v050", "0.5.0 (pre-registered primary table)", rows["v050"], out, True)
    too = too_small_section(rows["v050"], out)
    R["too_small"] = too
    R["overlap"] = overlap_section(rows["v050"], out)
    R["v041"] = version_section("v041", "0.4.1 (secondary table)", rows["v041"], out, False)
    R["cmp"] = comparison_section(rows["v050"], rows["v041"], out)
    c_abs = abstention_c(rows["v050"], warnings)
    b_abs, b_miss = phase_b_abstention(inp["r1"], inp["pb"], warnings)
    R["abst_c"], R["abst_b"] = c_abs, b_abs
    abstention_text(c_abs, b_abs, b_miss, out, "ABSTENTION SHARES, 0.5.0 (P-7 item 4; Phase B from evaluation/r1_v050/certs)")
    R["aw"] = awareness_section(rows["v050"], out)
    out.append("")
    out.append("=" * 100)
    out.append(f"WARNINGS ({len(warnings)})")
    out.append("=" * 100)
    seen = set()
    for w in warnings:
        if w not in seen:
            seen.add(w)
            out.append("  " + w)
    if not warnings:
        out.append("  none")
    return "\n".join(out) + "\n", R


def phase_b_only_report(inp):
    out, warnings = [], []
    b_abs, b_miss = phase_b_abstention(inp["r1"], inp["pb"], warnings)
    abstention_text(None, b_abs, b_miss, out, "PHASE B ABSTENTION SHARES, 0.5.0 (P-7 item 4; evaluation/r1_v050/certs)")
    for w in sorted(set(warnings)):
        out.append("  warning: " + w)
    return "\n".join(out) + "\n", b_abs


# ------------------------------------------------------------------ selftest
def _cert(version, verdict, flags=(), streams=None, load_error=None, comps=True, comp_verdict=None):
    """Synthetic certificate envelope. streams: stream -> (holds, n, undefined, hard)."""
    if streams is None:
        streams = {}
    st = {"world:plus": (200, 200, 0, 0), "world:minus": (0, 200, 0, 0), "control:x": (0, 200, 200, 200),
          "probe:noise": (0, 200, 200, 0)}
    st.update(streams)
    counts = {}
    for k, (h, n, u, hu) in st.items():
        d = {"holds": h, "n": n, "undefined": u}
        if version == "v050":
            d["hard_undefined"] = hu
        counts[k] = d
    comp = {"id": "C", "verdict": comp_verdict or verdict, "flags": sorted(flags), "counts": counts}
    body = {"tool_version": "0.5.0" if version == "v050" else "0.4.1", "verdict": verdict, "load_error": load_error,
            "components": [comp] if comps else []}
    return {"body": body, "body_sha256": "x", "created_utc": "-"}


def selftest():
    fails = []

    def check(name, cond, info=""):
        if not cond:
            fails.append(f"{name} {info}")

    # --- Wilson
    check("wilson 10/10", abs(wilson_lower(10, 10) - 10 / (10 + Z * Z)) < 1e-12, wilson_lower(10, 10))
    check("wilson 9/10 >= .6", wilson_lower(9, 10) >= 0.6, wilson_lower(9, 10))
    check("wilson 8/10 < .6", wilson_lower(8, 10) < 0.6, wilson_lower(8, 10))
    check("wilson 0/10", abs(wilson_lower(0, 10)) < 1e-12 or wilson_lower(0, 10) < 1e-9)
    check("wilson 0/0 nan", wilson_lower(0, 0) != wilson_lower(0, 0))
    check("wilson 5/12 value", abs(wilson_lower(5, 12) - 0.2199) < 0.002, wilson_lower(5, 12))

    with tempfile.TemporaryDirectory() as tmp:
        run = os.path.join(tmp, "run")
        r1 = os.path.join(tmp, "r1")
        os.makedirs(r1)
        EXP = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
               "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "HIGH_RATE:probe:noise", "HIGH_RATE:world:null",
               "HIGH_RATE:probe:shuffle:a,b"]
        exp, aw, dl = {}, {}, {}
        specs = {}  # (version, case, twin) -> cert dict or None

        def add_case(cid, cls, sub, src, level, ovl, no_log=False):
            wid = "C" + cid
            exp[cid] = dict(case_id=cid, world_id=wid, **{"class": cls}, subtype=sub, source=src, in_scope=cls != "O",
                            expected=list(EXP) + ["K1_ABSTAINED:world:plus"] * (cid == "T08"))
            aw[wid] = dict(reader1="no log" if no_log else level, reader2="no log" if no_log else level, resolved=level,
                           no_log=no_log, log_words=0 if no_log else 100)
            dl[cid] = dict(overlap=("yes, Phase B case X" if ovl else ("no (addendum source)" if src in ADDENDUM_SOURCES else "no")))

        def put(v, cid, twin, cert):
            specs[(v, cid, twin)] = cert

        # ---- B-1: T01..T10 (T01-T04 addendum MOR03; T05-T10 overlap -> 6 of 10 overlap > half)
        for i in range(1, 11):
            cid = f"T{i:02d}"
            add_case(cid, "B-1", "", "MOR03" if i <= 4 else "KRI09", "P" if i != 9 else "N", i >= 5)
        # T01 faulty: 0.4.1 UNDEFINED (soft) -> 0.5.0 detected generic with soft abstention 10 on plus
        put("v041", "T01", "faulty", _cert("v041", "UNDEFINED"))
        put("v050", "T01", "faulty", _cert("v050", "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE", "K1_ABSTAINED:world:plus"],
                                           {"world:plus": (190, 200, 10, 0)}))
        put("v041", "T01", "fixed", _cert("v041", "FALSIFIABLE"))
        put("v050", "T01", "fixed", _cert("v050", "FALSIFIABLE"))
        # T02 faulty: UNDEFINED -> FALSIFIABLE with no expected flag, minus 16/200=0.08 -> error too small
        put("v041", "T02", "faulty", _cert("v041", "UNDEFINED"))
        put("v050", "T02", "faulty", _cert("v050", "FALSIFIABLE", [], {"world:minus": (16, 200, 0, 0)}))
        # T02 fixed: UNDEFINED -> NOT_FALSIFIABLE (false alarm hidden)
        put("v041", "T02", "fixed", _cert("v041", "UNDEFINED"))
        put("v050", "T02", "fixed", _cert("v050", "NOT_FALSIFIABLE", ["K2_HIGH_SIZE"]))
        # T03 faulty: K2-only detection (declared label), both versions; fixed WEAK in 0.5.0, UNDEFINED(hard) in 0.4.1
        put("v041", "T03", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["K2_NO_SEPARATION"]))
        put("v050", "T03", "faulty", _cert("v050", "NOT_FALSIFIABLE", ["K2_NO_SEPARATION", "K2_FAILS_UNREACHABLE"]))
        put("v041", "T03", "fixed", _cert("v041", "UNDEFINED"))
        put("v050", "T03", "fixed", _cert("v050", "UNDEFINED", [], {"world:minus": (0, 200, 3, 3)}))
        # T04 faulty: 0.4.1 detection with HIGH_RATE:world:null; 0.5.0 NOT_FALSIFIABLE with only information flags
        # (loss of a detection), minus 10/200 (no flag, <= bound -> labelled too small) and majority flag
        put("v041", "T04", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["HIGH_RATE:world:null"]))
        put("v050", "T04", "faulty", _cert("v050", "NOT_FALSIFIABLE",
                                           ["K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus", "BAD_RETURN"],
                                           {"world:minus": (10, 200, 60, 0)}))
        put("v041", "T04", "fixed", _cert("v041", "UNTESTED"))
        put("v050", "T04", "fixed", _cert("v050", "UNTESTED"))
        # T05 faulty and fixed 0.5.0 missing; 0.4.1 present (fixed UNDEFINED -> cause unknown)
        put("v041", "T05", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"]))
        put("v041", "T05", "fixed", _cert("v041", "UNDEFINED"))
        # T06 faulty load error (no components) in 0.5.0; fixed ok
        put("v041", "T06", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"]))
        put("v050", "T06", "faulty", _cert("v050", "UNDEFINED", load_error="boom", comps=False))
        put("v041", "T06", "fixed", _cert("v041", "FALSIFIABLE"))
        put("v050", "T06", "fixed", _cert("v050", "FALSIFIABLE"))
        # T07 faulty WEAK with expected flag -> miss, has flag (no too-small label); fixed FALSIFIABLE
        put("v041", "T07", "faulty", _cert("v041", "WEAK", ["K4_CONTROL_ALSO_HOLDS"]))
        put("v050", "T07", "faulty", _cert("v050", "WEAK", ["K4_CONTROL_ALSO_HOLDS"]))
        put("v041", "T07", "fixed", _cert("v041", "FALSIFIABLE"))
        put("v050", "T07", "fixed", _cert("v050", "FALSIFIABLE"))
        # T08 faulty NOT_FALSIFIABLE with only information flags (K1_ABSTAINED listed in expected but ignored), minus 50/200
        put("v041", "T08", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["K2_MINUS_UNREAD"], {"world:minus": (50, 200, 0, 0)}))
        put("v050", "T08", "faulty", _cert("v050", "NOT_FALSIFIABLE", ["K1_ABSTAINED:world:plus", "K8_SOME_CHANGES"],
                                           {"world:minus": (50, 200, 0, 0)}))
        put("v041", "T08", "fixed", _cert("v041", "FALSIFIABLE"))
        put("v050", "T08", "fixed", _cert("v050", "FALSIFIABLE"))
        # T09 faulty declared (shuffle) detection; fixed timeout in 0.5.0 (certificate exists but is ignored)
        put("v041", "T09", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["HIGH_RATE:probe:shuffle:a,b"]))
        put("v050", "T09", "faulty", _cert("v050", "NOT_FALSIFIABLE", ["HIGH_RATE:probe:shuffle:a,b"]))
        put("v041", "T09", "fixed", _cert("v041", "FALSIFIABLE"))
        put("v050", "T09", "fixed", _cert("v050", "FALSIFIABLE", [], {"world:plus": (100, 200, 100, 0)}))
        # T10 faulty generic + K2 flag (not K2-only); fixed: UNDEFINED(0.4.1) -> UNDEFINED plus majority (soft 120)
        put("v041", "T10", "faulty", _cert("v041", "NOT_FALSIFIABLE", ["HIGH_RATE:probe:noise", "K2_FAILS_UNREACHABLE"]))
        put("v050", "T10", "faulty", _cert("v050", "NOT_FALSIFIABLE", ["HIGH_RATE:probe:noise", "K2_FAILS_UNREACHABLE"]))
        put("v041", "T10", "fixed", _cert("v041", "UNDEFINED"))
        put("v050", "T10", "fixed", _cert("v050", "UNDEFINED", ["K1_UNDEFINED"], {"world:plus": (80, 200, 120, 0)}))

        # ---- B-2: U01..U10 (5 L1.3, 5 L1.4), 8 detections, all clean, no overlap, source KAP23
        for i in range(1, 11):
            cid = f"U{i:02d}"
            add_case(cid, "B-2", "L1.3" if i <= 5 else "L1.4", "KAP23", "C", False)
            for v in ("v041", "v050"):
                if i <= 8:
                    put(v, cid, "faulty", _cert(v, "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NULL"]))
                else:
                    put(v, cid, "faulty", _cert(v, "FALSIFIABLE", []))
                put(v, cid, "fixed", _cert(v, "FALSIFIABLE"))
        # ---- B-3: V01..V03 (n<10); V01 addendum
        for i in range(1, 4):
            cid = f"V{i:02d}"
            add_case(cid, "B-3", "", "CUR13" if i == 1 else "PEA97", "P", False, no_log=(i == 3))
            for v in ("v041", "v050"):
                put(v, cid, "faulty", _cert(v, "NOT_FALSIFIABLE", ["K4_CONTROL_ALSO_HOLDS"]))
                put(v, cid, "fixed", _cert(v, "WEAK"))
        # ---- B-6: 10 pairs all detected and clean -> HOLDS; no overlap
        for i in range(1, 11):
            cid = f"W{i:02d}"
            add_case(cid, "B-6", "", "NIE11" if i > 2 else "LAZ18", "P", False)
            for v in ("v041", "v050"):
                put(v, cid, "faulty", _cert(v, "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"]))
                put(v, cid, "fixed", _cert(v, "FALSIFIABLE"))
        # ---- O
        add_case("X01", "O", "O-1", "KAP23", "P", False)
        add_case("X02", "O", "O-2", "SIM11", "C", False)
        for v in ("v041", "v050"):
            put(v, "X01", "faulty", _cert(v, "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"]))
            put(v, "X01", "fixed", _cert(v, "FALSIFIABLE"))
            put(v, "X02", "faulty", _cert(v, "FALSIFIABLE"))
            put(v, "X02", "fixed", _cert(v, "FALSIFIABLE"))

        # P-8 item 4: UNDEFINED miss and two-component miss get no "error too small" label (minus holds 0/200 in both)
        add_case("X03", "O", "O-3", "BAG09", "P", False)
        add_case("X04", "O", "O-3", "HER14", "P", False)
        two = _cert("v050", "FALSIFIABLE")
        two["body"]["components"].append(dict(two["body"]["components"][0], id="D"))
        for v in ("v041", "v050"):
            put(v, "X03", "faulty", _cert(v, "UNDEFINED"))
            put(v, "X03", "fixed", _cert(v, "FALSIFIABLE"))
            put(v, "X04", "faulty", two if v == "v050" else _cert(v, "FALSIFIABLE"))
            put(v, "X04", "fixed", _cert(v, "FALSIFIABLE"))

        def write_all(drop_undefined=()):
            for (v, cid, twin), cert in specs.items():
                if cert is None:
                    continue
                if v == "v041" and (cid, twin) in drop_undefined:
                    cert = _cert("v041", "FALSIFIABLE")
                d = os.path.join(run, "certs", v, cid)
                os.makedirs(d, exist_ok=True)
                json.dump(cert, open(os.path.join(d, twin + ".json"), "w", encoding="utf-8"))

        write_all()
        # unreadable certificate (T06-like): add a case Y01 with broken JSON in 0.5.0
        add_case("Y01", "B-3", "", "ARC81", "P", False)
        for v in ("v041", "v050"):
            d = os.path.join(run, "certs", v, "Y01")
            os.makedirs(d, exist_ok=True)
            json.dump(_cert(v, "FALSIFIABLE"), open(os.path.join(d, "fixed.json"), "w", encoding="utf-8"))
            if v == "v041":
                json.dump(_cert(v, "NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"]), open(os.path.join(d, "faulty.json"), "w"))
            else:
                open(os.path.join(d, "faulty.json"), "w").write("{broken")

        # phase B certificates for the abstention test
        pb = {"P01": dict(**{"class": "B-1"}), "P02": dict(**{"class": "B-1"}), "P03": dict(**{"class": "B-2"}),
              "P04": dict(**{"class": "O"})}

        def pbw(cid, twin, c):
            if c is None:
                return
            json.dump(c, open(os.path.join(r1, f"evaluation__phase_b__cases__{cid}__{twin}.py.json"), "w"))
        pbw("P01", "faulty", _cert("v050", "NOT_FALSIFIABLE", [], {"world:plus": (150, 200, 50, 10), "world:null": (0, 100, 30, 0)}))
        pbw("P02", "faulty", _cert("v050", "FALSIFIABLE"))
        pbw("P01", "fixed", _cert("v050", "FALSIFIABLE", [], {"world:minus": (0, 200, 20, 20)}))
        # P02 fixed missing; P03 faulty load error (excluded); P03 fixed ok with 5 soft on minus
        pbw("P03", "faulty", _cert("v050", "UNDEFINED", load_error="x", comps=False))
        pbw("P03", "fixed", _cert("v050", "FALSIFIABLE", [], {"world:minus": (0, 200, 5, 0)}))
        pbw("P04", "faulty", _cert("v050", "FALSIFIABLE"))
        pbw("P04", "fixed", _cert("v050", "FALSIFIABLE"))

        inp = dict(exp=exp, aw=aw, dl=dl, pb=pb, r1=r1)
        to = {("v050", "T09", "fixed")}
        text, R = build_report(inp, run, to)
        r50, r41 = R["rows"]["v050"], R["rows"]["v041"]

        # detection rules
        check("T01 det generic", r50["T01"]["det"] and r50["T01"]["label"] == "generic" and not r50["T01"]["k2only"])
        check("T02 not det (no flag)", not r50["T02"]["det"])
        check("T03 det declared K2-only", r50["T03"]["det"] and r50["T03"]["label"] == "declared" and r50["T03"]["k2only"])
        check("T04 info flags only is a miss in 0.5.0, det in 0.4.1", not r50["T04"]["det"] and r41["T04"]["det"])
        check("T05 missing = miss/failed clean", not r50["T05"]["det"] and not r50["T05"]["clean"] and r50["T05"]["f"]["status"] == "MISSING")
        check("T06 load error = miss", not r50["T06"]["det"] and r50["T06"]["f"]["status"] == "LOAD_ERROR")
        check("T07 WEAK with flag is a miss", not r50["T07"]["det"])
        check("T08 information flags never count (even if listed)", not r50["T08"]["det"] and not r41["T08"]["det"])
        check("T09 faulty declared", r50["T09"]["det"] and r50["T09"]["label"] == "declared" and not r50["T09"]["k2only"])
        check("T09 timeout fixed = failed clean", not r50["T09"]["clean"] and r50["T09"]["x"]["status"] == "TIMEOUT" and r41["T09"]["clean"])
        check("T10 generic, not K2-only", r50["T10"]["det"] and r50["T10"]["label"] == "generic" and not r50["T10"]["k2only"])
        check("clean: WEAK passes, UNTESTED fails, NOT_FALSIFIABLE fails", r50["V01"]["clean"] and not r50["T04"]["clean"] and not r50["T02"]["clean"])
        check("unreadable cert = miss", r50["Y01"]["f"]["status"] == "UNREADABLE" and not r50["Y01"]["det"] and r50["Y01"]["clean"])
        # class tables
        s = R["v050"]["B-1"][0]
        check("B-1 0.5.0 det count", s["det"] == 4 and s["n"] == 10, s)      # T01 T03 T09 T10
        check("B-1 clean count", s["clean"] == 4, s)                         # T01 T06 T07 T08
        check("B-1 verdict FAILS", R["v050"]["B-1"][1] == "FAILS")
        check("B-1 generic/declared/k2", (s["gen"], s["decl"], s["k2"]) == (2, 2, 1), (s["gen"], s["decl"], s["k2"]))
        check("B-2 verdict FAILS (8/10)", R["v050"]["B-2"][1] == "FAILS" and R["v050"]["B-2"][0]["det"] == 8)
        check("B-3 INSUFFICIENT (n<10)", R["v050"]["B-3"][1] == "INSUFFICIENT(n<10)" and R["v050"]["B-3"][0]["n"] == 4)
        check("B-6 HOLDS", R["v050"]["B-6"][1] == "HOLDS" and R["v050"]["B-6"][0]["det"] == 10)
        check("v041 B-1 det", R["v041"]["B-1"][0]["det"] == 6, R["v041"]["B-1"][0])  # T03 T04 T05 T06 T09 T10
        # baselines
        sb = block_stats([r for r in r50.values() if r["cls"] == "B-6"])
        check("baseline noise-only B-6", sb["dn"] == 10 and sb["dd"] == 0)
        bl = baseline_lines([r for r in r50.values() if r["cls"] == "B-6"])
        check("flag-everything line", "LBdet=0.7871" in bl[2] and "LBclean=0.0000" in bl[2], bl[2])
        check("declared-only B-6 fails", "would-pass-threshold=no" in bl[1] and "would-pass-threshold=yes" in bl[0])
        # overlap
        ov = R["overlap"]
        check("overlap wording B-1 (6 of 10)", ov["B-1"]["overlap"] == 6 and ov["B-1"]["wording"] is True)
        check("no wording B-2 / addendum", ov["B-2"]["wording"] is False and ov["B-1"]["addendum"] == 4
              and ov["B-1"]["n"] == 10 and ov["B-3"]["addendum"] == 1)
        check("overlap excluded table in text", "B-1 no-overlap" in text and "pairs= 4" in text.split("B-1 no-overlap")[1].splitlines()[0])
        # primary comparison
        c = R["cmp"]
        und = {(a, b): d for a, b, _, d in c["undef"]}
        check("undefined list", set(und) == {("T01", "faulty"), ("T02", "faulty"), ("T02", "fixed"), ("T03", "fixed"),
                                             ("T05", "fixed"), ("T10", "fixed"), ("X03", "faulty")}, sorted(und))
        check("cause soft", und[("T01", "faulty")] == "soft only" and und[("T02", "faulty")] == "soft only")
        check("cause hard", und[("T03", "fixed")] == "hard")
        check("cause unknown", und[("T05", "fixed")] == "unknown")
        check("cause plus majority", und[("T10", "fixed")] == "plus majority")
        check("informative (7 >= 5)", c["informative"] is True and c["n_undef"] == 7)
        check("gains det", c["gains_det"] == ["T01"], c["gains_det"])
        check("loss det (T06: 0.5.0 load error is a loss, T05 not comparable)", c["loss_det"] == ["T04", "T06"] and c["loss_clean"] == [], (c["loss_det"], c["loss_clean"]))
        check("hidden misses / alarms", c["hidden_misses"] == [("T02", "faulty")] and c["hidden_alarms"] == [("T02", "fixed")],
              (c["hidden_misses"], c["hidden_alarms"]))
        check("T01 faulty UNDEFINED->NF is a gain not a hidden miss", ("T01", "faulty") not in c["hidden_misses"])
        check("gains clean none (timeout excluded)", c["gains_clean"] == [], c["gains_clean"])
        check("not comparable lists", any(x.startswith("T05:faulty") for x in c["not_comparable"])
              and any(x.startswith("T09:fixed(TIMEOUT)") for x in c["not_comparable"])
              and any(x.startswith("Y01:faulty(UNREADABLE)") for x in c["not_comparable"]), c["not_comparable"])
        check("no gain/loss for T05/T06 (not comparable)", "T05" not in c["loss_det"] + c["gains_det"])
        check("anomalies: only T06 faulty (load error)", c["anomalies"] == [("T06", "faulty", "B-1", "NOT_FALSIFIABLE", "LOAD_ERROR")], c["anomalies"])
        check("majority flag listed", "T04:faulty" in text.split("K1_ABSTAINED_MAJORITY (0.5.0): ")[1].split("\n")[0])
        # not informative variant
        import shutil
        shutil.rmtree(run)
        write_all(drop_undefined={("T10", "fixed"), ("T05", "fixed"), ("T01", "faulty")})
        for v in ("v041", "v050"):                      # re-create the Y01 files removed with the folder
            d = os.path.join(run, "certs", v, "Y01")
            os.makedirs(d, exist_ok=True)
            json.dump(_cert(v, "FALSIFIABLE"), open(os.path.join(d, "fixed.json"), "w"))
        text2, R2 = build_report(inp, run, to)
        check("not informative (4 < 5)", R2["cmp"]["informative"] is False and R2["cmp"]["n_undef"] == 4, R2["cmp"]["n_undef"])
        check("not informative text and no per-class text", "NOT INFORMATIVE" in text2 and "per class (informative comparison)" not in text2)
        check("loss still reported when not informative", "detections lost : T04 T06" in text2)
        check("T01 faulty no longer gained (0.4.1 now FALSIFIABLE, miss)", R2["cmp"]["gains_det"] == ["T01"])
        # abstention
        ac = R["abst_c"]
        # B-1 faulty (0.5.0, ok certs with components): T01..T04, T07..T10 -> 8 files x (200+200) = 3200 ; num = 10 (T01 plus) + 60 (T04 minus)
        check("abstention C B-1 faulty", ac[("B-1", "faulty")] == (70, 3200, 8), ac[("B-1", "faulty")])
        # B-1 fixed: T01 T02 T03 T04 T06 T07 T08 T10 (T05 missing, T09 timeout) -> 3200 ; num = 120 (T10 plus) ; T03 hard 3 excluded
        check("abstention C B-1 fixed", ac[("B-1", "fixed")] == (120, 3200, 8), ac[("B-1", "fixed")])
        check("abstention excludes control/probe streams", ac[("B-6", "faulty")][0] == 0)
        # note the first build_report call used "run" before the variant; R is the informative variant
        # Phase B abstention
        ab = R["abst_b"]
        # B-1 faulty: P01 (plus 50-10=40 n200, minus 0/200, null 30/100) + P02 (400) -> num 70, den 200+200+100+400=900, 2 files
        check("phase B abstention B-1 faulty", ab[("B-1", "faulty")] == (70, 900, 2), ab[("B-1", "faulty")])
        # B-1 fixed: P01 only: minus soft 0 (20-20) -> 0/400 ; P02 missing
        check("phase B abstention B-1 fixed", ab[("B-1", "fixed")] == (0, 400, 1), ab[("B-1", "fixed")])
        check("phase B abstention B-2 faulty excludes load error", ab[("B-2", "faulty")] == (0, 0, 0))
        check("phase B abstention B-2 fixed", ab[("B-2", "fixed")] == (5, 400, 1))
        sep = phase_b_only_report(inp)[1]
        check("phase-b-only equals combined", sep == ab)
        # error too small
        tl = R["too_small"]
        check("too small labels", "T02" in tl and "U09" in tl and "T04" not in tl and "T08" not in tl and "T07" not in tl and "T06" not in tl
              and "T05" not in tl, tl)
        check("P-8 item 4: UNDEFINED and NOT_FALSIFIABLE-without-flag misses get no label",
              "X03" not in tl and "T04" not in tl and "T08" not in tl and "T01" not in tl, tl)
        check("P-8 item 4: two components get no label", "X04" not in tl and "2 components" in text, tl)
        check("P-8 item 4: text states the verdict reason", "is not WEAK or FALSIFIABLE" in text)
        check("P-8 item 5: B-2 subtype rows carry the class rule",
              "B-2 L1.3" in text and text.count("class-rule") >= 2 and "class-rule FAILS (descriptive" in text
              and "class-rule HOLDS (descriptive" in text)
        sub_l13 = block_stats([r for r in r50.values() if r["cls"] == "B-2" and r["sub"] == "L1.3"])
        check("P-8 item 5: L1.3 5/5 5/5 -> bounds 0.65 -> HOLDS (descriptive)", sub_l13["rule"] is True and sub_l13["n"] == 5)
        sub_l14 = block_stats([r for r in r50.values() if r["cls"] == "B-2" and r["sub"] == "L1.4"])
        check("P-8 item 5: L1.4 rule", sub_l14["det"] == 3 and sub_l14["rule"] is False, sub_l14)
        check("bound exactly 0.081 at n=200", abs((0.05 + 2 * math.sqrt(0.05 * 0.95 / 200)) - 0.0808) < 0.0002)
        # boundary: 17/200 = 0.085 is above the bound
        n = 200
        check("17/200 above bound, 16/200 below", 17 / n > 0.05 + 2 * math.sqrt(0.05 * 0.95 / n) >= 16 / n)
        # awareness
        aw_r = R["aw"]
        check("awareness B-1", aw_r["B-1"]["P"] == 9 and aw_r["B-1"]["N"] == 1 and aw_r["B-1"]["C"] == 0, aw_r["B-1"])
        check("awareness no-log counted in P and shown", aw_r["B-3"]["no_log"] == 1 and aw_r["B-3"]["P"] == 4, aw_r["B-3"])
        check("report deterministic", text2 == build_report(inp, run, to)[0])
        check("ascii only", all(ord(ch) < 128 for ch in text))
    # missing run folder does not crash (everything missing)
    with tempfile.TemporaryDirectory() as tmp:
        inp2 = dict(exp={"A1": dict(case_id="A1", world_id="C01", **{"class": "B-1"}, subtype="", source="S", expected=EXP_MIN())},
                    aw={"C01": dict(reader1="P", reader2="P", resolved="P", no_log=False)}, dl={}, pb={}, r1=tmp)
        t, R3 = build_report(inp2, os.path.join(tmp, "none"), set())
        check("empty run: all misses", R3["v050"]["B-1"][0]["det"] == 0 and R3["v050"]["B-1"][0]["clean"] == 0)
        check("empty run: not informative", R3["cmp"]["informative"] is False)
    if fails:
        print("SELFTEST FAILED:")
        for f in fails:
            print("  " + f)
        return 1
    print("SELFTEST PASSED")
    return 0


def EXP_MIN():
    return ["K5_HOLDS_ON_NOISE"]


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=DEFAULTS["run"])
    ap.add_argument("--out")
    ap.add_argument("--timeouts", default="")
    ap.add_argument("--r1", default=DEFAULTS["r1"])
    ap.add_argument("--expected-c", default=DEFAULTS["expected_c"])
    ap.add_argument("--expected-b", default=DEFAULTS["expected_b"])
    ap.add_argument("--awareness", default=DEFAULTS["awareness"])
    ap.add_argument("--lines", default=DEFAULTS["lines"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--phase-b-abstention-only", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.selftest:
        return selftest()
    inp = load_inputs(dict(expected_c=a.expected_c, awareness=a.awareness, lines=a.lines, expected_b=a.expected_b, r1=a.r1))
    if a.phase_b_abstention_only:
        text, _ = phase_b_only_report(inp)
    else:
        to = set()
        for t in a.timeouts.split(","):
            t = t.strip()
            if t:
                v, c, w = t.split(":")
                to.add((v, c, w))
        text, _ = build_report(inp, a.run, to)
    sys.stdout.write(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
