"""PREREG_PHASE_D section 1 (overlap, as PC section 1), marked mechanically by the designer. This marking was omitted
after the briefs and is made after the run (REVISIONS P-7); it uses only the frozen briefs' private notes and the brief
authors' TASK.json, no result.

A pair overlaps a Phase B or C pair when (source, mechanism tag, statistic family) is one of the combinations that
Phases B and C used for that source, as listed in its brief author's TASK.json ("earlier_tag_family_combinations").
Writes score/OVERLAP_D.json (all 72 pairs) and score/RESULTS_D_WITHOUT_OVERLAP.json/.md: the per-arm, per-class
counts, H-D1/H-D2 bounds, H-D3 and the guard recomputed from score/RESULTS_D.json's per-pair rows without the
overlapping pairs (the formulas of score_phase_d.py: one-sided 95% Wilson lower bound, exact one-sided McNemar)."""
import json, math, os
W = r"E:\Claude Projects\Kapi\phase_d_work"
idmap = {m["id"]: m for m in json.load(open(os.path.join(W, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))}
tasks = {}
for half in os.listdir(os.path.join(W, "authors")):
    p = os.path.join(W, "authors", half, "TASK.json")
    if os.path.exists(p):
        tasks[half] = json.load(open(p, encoding="utf-8"))["earlier_tag_family_combinations"]
ov = {}
for i, m in sorted(idmap.items()):
    half = m["designer_id"].split("-")[0]
    p = json.load(open(os.path.join(W, "cases", i, "PRIVATE.json"), encoding="utf-8"))
    combos = [tuple(c) for c in tasks[half].get(p["source"], [])]
    ov[i] = {"class": m["class"], "half": half, "source": p["source"], "tag": p["subtype_or_tag"],
             "statistic_family": p["statistic_family"], "overlap": (p["subtype_or_tag"], p["statistic_family"]) in combos,
             "earlier_combinations_for_source": combos}
json.dump(ov, open(os.path.join(W, "score", "OVERLAP_D.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
Z = 1.6448536269514722


def wilson_lower(k, n):
    if n == 0:
        return None
    p = k / n
    d = 1 + Z * Z / n
    c = p + Z * Z / (2 * n)
    r = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return round((c - r) / d, 4)


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else sum(math.comb(n, k) for k in range(b, n + 1)) / 2 ** n


res = json.load(open(os.path.join(W, "score", "RESULTS_D.json"), encoding="utf-8"))
sel = sorted(json.load(open(os.path.join(W, "shuffle", "SUBSET_IDS.json"))))
keep = [i for i in sel if not ov[i]["overlap"]]
dropped = [i for i in sel if ov[i]["overlap"]]


def rows(arm):
    # RESULTS_D.json["pairs"] is a list of per-(id, arm) rows
    r = {x["id"]: x for x in res["pairs"] if x["arm"] == arm}
    assert len(r) == 20, (arm, len(r))
    return r


out = {"overlapping_selected": dropped, "kept": keep, "per_class_overlap": {}, "arms": {}}
for cl in ("B-2", "B-3", "B-1", "B-6"):
    ids = [i for i in sel if ov[i]["class"] == cl]
    out["per_class_overlap"][cl] = {"n": len(ids), "overlapping": sum(ov[i]["overlap"] for i in ids),
                                    "largely_repeats": sum(ov[i]["overlap"] for i in ids) * 2 > len(ids)}
for arm in ("R", "W0", "W1"):
    r = rows(arm)
    a = {}
    for cl in ("B-2", "B-3", "B-1", "B-6"):
        ids = [i for i in keep if ov[i]["class"] == cl]
        kd = sum(bool(r[i]["attributable"]) for i in ids)
        kc = sum(bool(r[i]["clean"]) for i in ids)
        a[cl] = {"n": len(ids), "attributable": kd, "declared": sum(bool(r[i]["declared"]) for i in ids), "clean": kc,
                 "attr_lower": wilson_lower(kd, len(ids)), "clean_lower": wilson_lower(kc, len(ids))}
    out["arms"][arm] = a
r0, r1 = rows("W0"), rows("W1")
pool = [i for i in keep if ov[i]["class"] in ("B-2", "B-3")]
b = sum(bool(r1[i]["declared"]) and not bool(r0[i]["declared"]) for i in pool)
c = sum(bool(r0[i]["declared"]) and not bool(r1[i]["declared"]) for i in pool)
gb = sum(bool(r0[i]["clean"]) and not bool(r1[i]["clean"]) for i in pool)
gc = sum(bool(r1[i]["clean"]) and not bool(r0[i]["clean"]) for i in pool)
out["H-D3"] = {"pairs": len(pool), "b": b, "c": c, "p": mcnemar(b, c)}
out["guard"] = {"pairs": len(pool), "w0_only": gb, "w1_only": gc, "p": mcnemar(gb, gc)}
json.dump(out, open(os.path.join(W, "score", "RESULTS_D_WITHOUT_OVERLAP.json"), "w"), indent=1)
L = ["# Phase D results without the overlapping pairs (PREREG section 1; marking in OVERLAP_D.json)", "",
     f"Overlapping selected pairs: {', '.join(dropped) or 'none'}.", "",
     "| class | n | overlapping | more than half |", "|---|---|---|---|"]
L += [f"| {k} | {v['n']} | {v['overlapping']} | {'yes' if v['largely_repeats'] else 'no'} |" for k, v in out["per_class_overlap"].items()]
L += ["", "| arm | class | n | attributable | declared | clean | attr. lower | clean lower |", "|---|---|---|---|---|---|---|---|"]
for arm, a in out["arms"].items():
    L += [f"| {arm} | {k} | {v['n']} | {v['attributable']} | {v['declared']} | {v['clean']} | {v['attr_lower']} | {v['clean_lower']} |" for k, v in a.items()]
L += ["", f"H-D3 without overlap: {out['H-D3']['pairs']} pairs, b = {b}, c = {c}, p = {out['H-D3']['p']:.4f}.",
      f"Clean-pass guard without overlap: W0-only {gb}, W1-only {gc}, p = {out['guard']['p']:.4f}."]
open(os.path.join(W, "score", "RESULTS_D_WITHOUT_OVERLAP.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
