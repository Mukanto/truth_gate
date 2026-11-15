"""Phase C step 2 (designer): mechanical checks of the briefs and private notes (PREREG_PHASE_C sections 1, 2, 4 item 2).

Usage: py step2_check.py AUTHORS_DIR REPO_DIR [--out REPORT.json]
Checks per class folder: BRIEFS/PRIVATE match; term check (frozen tools/term_check.py); required note fields; tag and
family in the closed vocabularies; B-2 subtype; source allowed for the class; per-source caps; counts; addendum
minimum; B-2 subtype minima; independent read sources; dtypes; numbers in sizes above the 1000 cap; overlap marks
against PHASE_B_TABLE.json. The "what a brief may state" text and the estimand are read by the designer, not here.
"""
import json, os, re, subprocess, sys
from collections import Counter

authors, repo = sys.argv[1], sys.argv[2]
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
pc = os.path.join(repo, "evaluation", "phase_c")
table = json.load(open(os.path.join(pc, "PHASE_B_TABLE.json"), encoding="utf-8"))
voc = table["vocabulary"]
CLASS = {"B1": "B-1", "B2": "B-2", "B3": "B-3", "B6": "B-6", "O": "O"}
PB_SOURCES = {"B-1": {"KRI09", "VUL09", "MAK19", "BAR05"}, "B-2": {"KAP23", "AMB02", "SIM03"},
              "B-3": {"PEA97", "ARC81", "KRO93"}, "B-6": {"NIE11", "HUR84", "LAZ10", "MAK19", "GEL06"},
              "O": {"KAP23", "SIM11", "BAG09", "HER14"}}
ADD = {"B-1": {"KRI10", "MOR03"}, "B-2": {"VAR06"}, "B-3": {"CUR13"}, "B-6": {"LAZ18"}, "O": set()}
NOT_INDEPENDENT = {"KRI10", "LAZ18", "GEL06"}
REQ = ["local_id", "source", "passage", "faulty", "fixed", "estimand", "mechanism_tag", "statistic_family",
       "guard_minimum", "sizes_note"]
report = {}
for folder, cls in CLASS.items():
    d = os.path.join(authors, folder)
    r = {"issues": [], "pairs": {}}
    report[folder] = r
    try:
        briefs = json.load(open(os.path.join(d, "BRIEFS.json"), encoding="utf-8"))
        notes = json.load(open(os.path.join(d, "PRIVATE.json"), encoding="utf-8"))
    except Exception as e:
        r["issues"].append(f"cannot read: {type(e).__name__}: {e}")
        continue
    bid = [b.get("local_id") for b in briefs]
    nid = [n.get("local_id") for n in notes]
    if sorted(bid) != sorted(nid) or len(set(bid)) != len(bid):
        r["issues"].append(f"local ids differ or repeat: briefs {bid} notes {nid}")
    for b in briefs:
        extra = set(b) - {"local_id", "claim", "data_keys", "sizes"}
        if extra:
            r["issues"].append(f"{b.get('local_id')}: extra brief fields {sorted(extra)}")
    tc = subprocess.run([sys.executable, os.path.join(pc, "tools", "term_check.py"), os.path.join(d, "BRIEFS.json")],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    r["term_check_exit"] = tc.returncode
    if tc.returncode != 0:
        r["issues"].append("term check: " + (tc.stdout + tc.stderr).strip()[:2000])
    nb = {n.get("local_id"): n for n in notes}
    src_count, sub_count = Counter(), Counter()
    for b in briefs:
        lid = b.get("local_id")
        n = nb.get(lid, {})
        p = {"source": n.get("source"), "tag": n.get("mechanism_tag"), "family": n.get("statistic_family")}
        miss = [k for k in REQ if not str(n.get(k, "")).strip()]
        if cls == "B-2" and not str(n.get("subtype", "")).strip():
            miss.append("subtype")
        if miss:
            r["issues"].append(f"{lid}: missing note fields {miss}")
        tags = voc["mechanism_tag"]["O" if cls == "O" else cls]
        if p["tag"] not in tags:
            r["issues"].append(f"{lid}: tag {p['tag']!r} not in {tags}")
        if p["family"] not in voc["statistic_family"]:
            r["issues"].append(f"{lid}: family {p['family']!r} not in vocabulary")
        if cls == "B-2" and n.get("subtype") != p["tag"]:
            r["issues"].append(f"{lid}: subtype {n.get('subtype')!r} != tag {p['tag']!r}")
        if cls == "B-2" and p["source"] == "VAR06" and p["tag"] != "L1.3":
            r["issues"].append(f"{lid}: VAR06 pair not L1.3")
        if p["source"] not in PB_SOURCES[cls] | ADD[cls]:
            r["issues"].append(f"{lid}: source {p['source']!r} not allowed for {cls}")
        src_count[p["source"]] += 1
        sub_count[p["tag"]] += 1
        for k in b.get("data_keys", []):
            if str(k.get("dtype", "")).lower() not in ("float", "bool"):
                r["issues"].append(f"{lid}: key {k.get('key')} dtype {k.get('dtype')!r}")
        nums = [int(x) for x in re.findall(r"\d[\d,]*", str(b.get("sizes", "")).replace(",", ""))]
        if any(x > 1000 for x in nums):
            r["issues"].append(f"{lid}: a number above 1000 in sizes ({[x for x in nums if x > 1000]}); check the cap")
        overlap = None
        if p["source"] not in ADD[cls]:
            for row in table["pairs"]:
                if (row["source"], row["mechanism_tag"], row["statistic_family"]) == (p["source"], p["tag"], p["family"]):
                    overlap = row["case"]; break
        p["overlap"] = overlap
        p["addendum"] = p["source"] in ADD[cls]
        r["pairs"][lid] = p
    nexp = 6 if cls == "O" else 12
    if len(briefs) != nexp:
        r["issues"].append(f"{len(briefs)} briefs (planned {nexp})")
    for s, c in src_count.items():
        cap = 8 if (cls == "B-2" and s == "KAP23") else 4
        if c > cap:
            r["issues"].append(f"source {s}: {c} pairs > cap {cap}")
    if cls != "O":
        na = sum(src_count[s] for s in ADD[cls])
        r["addendum_pairs"] = na
        if na < 4:
            r["issues"].append(f"addendum pairs {na} < 4")
        indep = {s for s in src_count if s not in NOT_INDEPENDENT}
        r["independent_sources"] = sorted(indep)
        if len(indep) < 3:
            r["issues"].append(f"independent sources {sorted(indep)} < 3")
    else:
        for o in ("O-1", "O-2", "O-3"):
            if sub_count[o] != 2:
                r["issues"].append(f"{o}: {sub_count[o]} briefs (planned 2)")
    if cls == "B-2":
        for s, m in {"L1.1": 1, "L1.3": 1, "L1.4": 2, "L3.1": 2, "L3.2": 2}.items():
            if sub_count[s] < m:
                r["issues"].append(f"subtype {s}: {sub_count[s]} < {m}")
    r["per_source"] = dict(src_count)
    r["per_tag"] = dict(sub_count)
    r["overlaps"] = {k: v["overlap"] for k, v in r["pairs"].items() if v["overlap"]}
for folder, r in report.items():
    print(f"== {folder}: {len(r['pairs'])} pairs; per source {r.get('per_source')}; addendum {r.get('addendum_pairs')}; "
          f"overlaps {len(r.get('overlaps', {}))} {r.get('overlaps')}")
    for i in r["issues"]:
        print("   ISSUE", i)
if out:
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
