"""Designer's independent recomputation of the Phase B metrics (PREREG §7: 'The designer recomputes every number from
the certificates with a separate script'). Written without reading run_phase_b.py.

Usage: py phase_b_recompute.py <run_dir> <version>     (version: v040 or v030)
Reads <run_dir>/certs/<version>/<case>/{faulty,fixed}.json, evaluation/phase_b/EXPECTED_FLAGS.json and
record/world/AWARENESS.md. A missing certificate or a load error counts as a miss / failed clean pass. Timeouts are
taken from the runner's log separately (pass --timeouts case:twin,... if any).
"""
import json, math, os, re, sys

REPO = r"E:\Claude Projects\kapi-oss\evaluation\phase_b"
Z = 1.6448536269514722
SCOPE = ["B-1", "B-2", "B-3", "B-6"]
NOISE = {"K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"}
K2ONLY = {"K2_NO_SEPARATION", "K2_FAILS_UNREACHABLE"}


def wilson_lower(k, n):
    if n == 0:
        return float("nan")
    p = k / n
    den = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return centre - half


def load(path):
    if not os.path.exists(path):
        return None
    body = json.load(open(path, encoding="utf-8"))["body"]
    return body


def flags_of(body):
    fl = set()
    for c in body.get("components", []) or []:
        fl.update(c.get("flags", []))
    return fl


def awareness():
    txt = open(os.path.join(REPO, "record", "world", "AWARENESS.md"), encoding="utf-8").read()
    lev = {}
    for line in txt.splitlines():
        m = re.match(r"\|\s*([PCN])\s*\|(.*)\|\s*\d+\s*\|", line)
        if m:
            for w in re.findall(r"W\d\d", m.group(2)):
                lev[w] = m.group(1)
    return lev


def main(run_dir, version, timeouts=()):
    exp = json.load(open(os.path.join(REPO, "EXPECTED_FLAGS.json"), encoding="utf-8"))["cases"]
    lev = awareness()
    assert len(lev) == 54, len(lev)
    rows = []
    for cid in sorted(exp):
        e = exp[cid]
        fb = load(os.path.join(run_dir, "certs", version, cid, "faulty.json"))
        xb = load(os.path.join(run_dir, "certs", version, cid, "fixed.json"))
        f_ok = fb is not None and not fb.get("load_error") and f"{cid}:faulty" not in timeouts
        x_ok = xb is not None and not xb.get("load_error") and f"{cid}:fixed" not in timeouts
        ff = flags_of(fb) if fb else set()
        present = sorted(ff & set(e["expected"]))
        fverd = fb["verdict"] if fb else "MISSING"
        det = f_ok and fverd == "NOT_FALSIFIABLE" and bool(present)
        det_noise = f_ok and fverd == "NOT_FALSIFIABLE" and bool(set(present) & NOISE)
        det_decl = f_ok and fverd == "NOT_FALSIFIABLE" and bool(set(present) - NOISE)
        label = ("generic" if (ff & NOISE) else "declared") if det else ""
        k2only = det and set(present) <= K2ONLY
        xverd = xb["verdict"] if xb else "MISSING"
        clean = x_ok and xverd in ("FALSIFIABLE", "WEAK")
        rows.append(dict(case=cid, cls=e["class"], sub=e["subtype"], world=e["world_id"], aw=lev[e["world_id"]],
                         fverd=fverd, det=det, label=label, k2only=k2only, present=present, xverd=xverd,
                         clean=clean, xflags=sorted(flags_of(xb)) if (xb and not clean) else [],
                         det_noise=det_noise, det_decl=det_decl))
    out = []
    def block(name, rs):
        n = len(rs); d = sum(r["det"] for r in rs); c = sum(r["clean"] for r in rs)
        g = sum(r["label"] == "generic" for r in rs); dc = sum(r["label"] == "declared" for r in rs)
        k2 = sum(r["k2only"] for r in rs)
        dn = sum(r["det_noise"] for r in rs); dd = sum(r["det_decl"] for r in rs)
        ld, lc = wilson_lower(d, n), wilson_lower(c, n)
        verdict = "HOLDS" if (n >= 10 and ld >= 0.6 and lc >= 0.6) else "FAILS"
        out.append(f"{name:14} n={n:2} det={d:2} (gen {g}, decl {dc}, K2-only {k2}) clean={c:2} "
                   f"LBdet={ld:.4f} LBclean={lc:.4f} {verdict} | noise-only det={dn} LB={wilson_lower(dn, n):.4f}"
                   f" | declared-only det={dd} LB={wilson_lower(dd, n):.4f} | flag-all LBclean={wilson_lower(0, n):.4f}")
    for cls in SCOPE:
        block(cls, [r for r in rows if r["cls"] == cls])
    for sub in sorted({r["sub"] for r in rows if r["cls"] == "B-2"}):
        block("  B-2 " + sub, [r for r in rows if r["cls"] == "B-2" and r["sub"] == sub])
    block("out of scope", [r for r in rows if r["cls"] == "O"])
    out.append("")
    for lv in "PCN":
        for cls in SCOPE + ["O"]:
            rs = [r for r in rows if r["aw"] == lv and r["cls"] == cls]
            if rs:
                out.append(f"awareness {lv} {cls:4} n={len(rs):2} det={sum(r['det'] for r in rs):2} "
                           f"(gen {sum(r['label']=='generic' for r in rs)}, decl {sum(r['label']=='declared' for r in rs)}, "
                           f"K2-only {sum(r['k2only'] for r in rs)}) clean={sum(r['clean'] for r in rs):2}")
    out.append("")
    for r in rows:
        out.append(f"{r['case']:6} {r['cls']:4} {r['sub']:5} {r['world']} {r['aw']} faulty={r['fverd']:16} "
                   f"det={'Y' if r['det'] else 'n'} {r['label']:8}{' K2only' if r['k2only'] else ''} {','.join(r['present'])}"
                   f" | fixed={r['xverd']:16} clean={'Y' if r['clean'] else 'n'} {','.join(r['xflags'])}")
    print("\n".join(out))
    return rows


if __name__ == "__main__":
    to = set()
    if len(sys.argv) > 3 and sys.argv[3].startswith("--timeouts="):
        to = set(x for x in sys.argv[3].split("=", 1)[1].split(",") if x)
    main(sys.argv[1], sys.argv[2], to)
