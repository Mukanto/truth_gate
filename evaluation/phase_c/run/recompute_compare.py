"""Designer: compare run_phase_c.py RESULTS.json with recompute_designer.py output (PB section 7)."""
import json, re, sys
res = json.load(open(sys.argv[1], encoding="utf-8"))
txt = open(sys.argv[2], encoding="utf-8").read().splitlines()
# recompute per-pair sections: first = v050, second = v041
sections, cur = [], None
for l in txt:
    if l.strip() == "-- per pair --":
        cur = {}; sections.append(cur); continue
    m = re.match(r"^(B\d-\d\d|O\d-[AB])\s.*?faulty=(\S+)\s+det=([Yn])\s*(generic|declared)?.*\| fixed=(\S+)\s+clean=([Yn])", l)
    if cur is not None and m:
        cur[m.group(1)] = (m.group(2), m.group(3) == "Y", m.group(4), m.group(5), m.group(6) == "Y")
    elif cur is not None and l.startswith("===="):
        cur = None
print("recompute per-pair sections:", [len(s) for s in sections])
pairs = res["pairs"]
sample = pairs[0] if isinstance(pairs, list) else next(iter(pairs.values()))
print("RESULTS pair keys:", sorted(sample.keys())[:30])
mism = 0
for vi, v in enumerate(("v050", "v041")):
    rc = sections[vi]
    for p in (pairs if isinstance(pairs, list) else pairs.values()):
        cid = p.get("case") or p.get("case_id")
        e = p.get(v) or p.get("versions", {}).get(v)
        if e is None:
            print("no version entry", cid, v); mism += 1; continue
        mine = (e["faulty_verdict"], e["detected"], e["label"], e["fixed_verdict"], e["clean"])
        theirs = rc.get(cid)
        if theirs is None or tuple(theirs) != mine:
            print("MISMATCH", v, cid, "runner", mine, "recompute", theirs); mism += 1
print("pair mismatches:", mism)
c = res["comparison"]
print("comparison: informative", c["informative"], "files_with_undefined_v041", c.get("files_with_undefined_v041") if not isinstance(c.get("files_with_undefined_v041"), list) else len(c["files_with_undefined_v041"]),
      "detections_lost", c["detections_lost"], "clean_passes_lost", c["clean_passes_lost"], "not_comparable", c["not_comparable"])
for k, v in c["per_class"].items():
    print("  ", k, {kk: vv for kk, vv in v.items() if kk in ("undefined_v041", "causes", "detections_gained", "clean_passes_gained", "k1_abstained_majority", "faulty_undefined_to_falsifiable_or_weak", "fixed_undefined_to_not_falsifiable")})
print("abstention:", json.dumps(res["abstention"], ensure_ascii=False)[:900])
