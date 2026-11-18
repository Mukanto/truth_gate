"""PREREG_PHASE_D section 1 (reserve) and 2.4 (Reserves): which pairs form each class after validity (designer).

Main pairs are those with reserve false. A dropped main pair is replaced first from its own half's reserves of the same
subtype or tag, then from the other half's, in reserve-number order (designer_id ...-R1, -R2, ...), skipping a reserve
that did not pass, is already used, or would break a source cap (6 per source per class; KAP23 10 in B-2). Pending
results are shown as pending and block no decision they cannot affect; the output is provisional until none is pending.
Decoys (B-1, B-6) have no halves, and ALLOCATION_D.json lists their reserves by source only: a dropped decoy is
replaced from its own decoy class's reserves in order (designer reading). Status per id: validity TABLE_DECISIONS.json (pass/drop), pre-validity drops given in PRE_DROPS."""
import collections, json, os, re
W = r"E:\Claude Projects\Kapi\phase_d_work"
PRE_DROPS = {"D-014": "reference rejected by check_skeletons_d", "D-041": "reference rejected by check_skeletons_d"}
idmap = json.load(open(os.path.join(W, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))
dec = json.load(open(os.path.join(W, "validity", "TABLE_DECISIONS.json"), encoding="utf-8"))
# fidelity part A outcomes (audit_a/<G>/AUDIT_A.json): a brief item (e, f, h, i) is a drop; any other failed item is a
# repair (pending until the repaired pair is re-validated and re-audited); a pair not yet audited is pending.
BRIEF_ITEMS = ("e", "f", "h", "i")
audit = {}
for g in ("B2", "B3", "DEC"):
    f = os.path.join(W, "audit_a", g, "AUDIT_A.json")
    if os.path.exists(f):
        for x in json.load(open(f, encoding="utf-8")):
            audit[x["case"]] = x
def status(i):
    if i in PRE_DROPS: return "drop", PRE_DROPS[i]
    if i not in dec: return "pending", None
    d = dec[i]
    if d["decision"] != "pass": return d["decision"], d.get("counting_label")
    a = audit.get(i)
    if a is None: return "pending", "fidelity A not done"
    if a["overall"] == "pass": return "pass", None
    failed = [k for k in "abcdefghijkmp" if a.get(k) == "no"]
    if any(k in BRIEF_ITEMS for k in failed): return "drop", "fidelity A (" + ",".join(failed) + ")"
    return "pending", "fidelity A repair (" + ",".join(failed) + ")"
cap = lambda cls, src: 10 if (cls == "B-2" and src == "KAP23") else 6
rnum = lambda m: int(re.search(r"(\d+)$", m["designer_id"]).group(1))  # B2A-R1 -> 1, B3B-13 -> 13 (reserve order)
report = {}
for cls in ("B-2", "B-3", "B-1", "B-6"):
    ms = [m for m in idmap if m["class"] == cls]
    if not ms: continue
    main = sorted([m for m in ms if not m["reserve"]], key=lambda m: m["designer_id"])
    res = sorted([m for m in ms if m["reserve"]], key=lambda m: (m["half"], rnum(m)))
    sel, used, notes = [], set(), []
    srccount = collections.Counter(m["source"] for m in main if status(m["id"])[0] == "pass")
    for m in main:
        st, lab = status(m["id"])
        if st == "pass": sel.append((m, "main")); continue
        if st == "pending": notes.append(f"{m['id']} ({m['designer_id']}, {m['subtype_or_tag']}) pending"); continue
        repl = None
        for half_pref in (m["half"], "B" if m["half"] == "A" else "A"):
            for r in res:
                if r["id"] in used: continue
                if cls in ("B-2", "B-3") and (r["half"] != half_pref or r["subtype_or_tag"] != m["subtype_or_tag"]): continue
                rst, _ = status(r["id"])
                if rst == "pending": notes.append(f"replacement for {m['id']} waits on reserve {r['id']}"); repl = "WAIT"; break
                if rst != "pass": continue
                if srccount[r["source"]] + 1 > cap(cls, r["source"]): notes.append(f"{r['id']} skipped: source cap"); continue
                repl = r; break
            if repl: break
        if repl == "WAIT": continue
        if repl:
            used.add(repl["id"]); srccount[repl["source"]] += 1; sel.append((repl, f"replaces {m['id']} ({lab})"))
        else:
            notes.append(f"{m['id']} ({m['designer_id']}, {m['subtype_or_tag']}, {lab}) not replaced")
    per_sub = collections.Counter(m["subtype_or_tag"] for m, _ in sel)
    report[cls] = {"selected": [(m["id"], m["designer_id"], m["subtype_or_tag"], m["source"], how) for m, how in sel],
                   "n_selected": len(sel), "per_subtype_or_tag": dict(per_sub), "notes": notes,
                   "sources_selected": dict(collections.Counter(m["source"] for m, _ in sel))}
json.dump(report, open(os.path.join(W, "validity", "SELECTION_provisional.json"), "w"), indent=1)
for cls, r in report.items():
    print(f"== {cls}: {r['n_selected']} selected; per subtype/tag {r['per_subtype_or_tag']}; sources {r['sources_selected']}")
    for n in r["notes"]: print("   ", n)
