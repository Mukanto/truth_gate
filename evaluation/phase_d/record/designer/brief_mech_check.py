"""Designer's mechanical checks of the briefs and notes (PREREG_PHASE_D section 3 item 2): counts against TASK.json,
closed lists, required note fields, dtypes, size limits, key/shape consistency. Prints one line per problem."""
import json, math, re, sys, collections
TAGS_B2 = ["L1.1", "L1.2", "L1.3", "L1.4", "L3.1", "L3.2"]
TAGS_B3 = ["ratio-shared-denominator", "ratio-vs-denominator-proxy", "change-vs-baseline", "shared-measured-component"]
TAGS_B1 = ["extreme-group-change", "split-by-baseline-compare-change", "select-then-test-same-data"]
TAGS_B6 = ["significant-here-not-there", "units-not-independent"]
FAM = ["classification", "R-squared", "regression-slope", "correlation", "proportion", "mean", "other"]
NOTE_FIELDS = ["local_id", "source", "passage", "faulty", "fixed", "estimand", "model_family", "mechanism_tag",
               "statistic_family", "guard_minimum", "subtype", "sizes_note", "exploited_structure", "structure_statistic", "notes"]
probs = []
summary = {}
for a in ["B2A", "B2B", "B3A", "B3B", "DEC"]:
    task = json.load(open(f"authors/{a}/TASK.json", encoding="utf-8"))
    B = json.load(open(f"authors/{a}/BRIEFS.json", encoding="utf-8"))
    P = {p["local_id"]: p for p in json.load(open(f"authors/{a}/PRIVATE.json", encoding="utf-8"))}
    assert [b["local_id"] for b in B] and set(b["local_id"] for b in B) == set(P), a
    cnt = collections.Counter()
    for b in B:
        i = b["local_id"]; p = P[i]
        if not i.startswith(task["local_id_prefix"]): probs.append((i, "prefix"))
        for f in NOTE_FIELDS:
            if f not in p: probs.append((i, f"note field missing: {f}"))
        tag, fam = p.get("mechanism_tag"), p.get("statistic_family")
        allowed = TAGS_B2 if a.startswith("B2") else TAGS_B3 if a.startswith("B3") else TAGS_B1 + TAGS_B6
        if tag not in allowed: probs.append((i, f"tag {tag}"))
        if fam not in FAM: probs.append((i, f"family {fam}"))
        if a.startswith("B2") and p.get("subtype") != tag: probs.append((i, f"subtype {p.get('subtype')} != tag {tag}"))
        if not p.get("estimand"): probs.append((i, "estimand empty"))
        if not p.get("model_family"): probs.append((i, "model_family empty"))
        ss = p.get("structure_statistic")
        if ss is None:
            if not a == "DEC": probs.append((i, "structure_statistic null outside decoys"))
        else:
            for k in ("code", "direction", "null_value", "note_value", "note_value_source", "set_by_brief"):
                if k not in ss: probs.append((i, f"structure_statistic.{k} missing"))
            if ss.get("direction") not in ("greater", "less"): probs.append((i, f"direction {ss.get('direction')}"))
            try:
                nv, nu = float(ss["note_value"]), float(ss["null_value"])
                if (nv - nu) * (1 if ss.get("direction") == "greater" else -1) <= 0: probs.append((i, f"direction vs note-null: {ss.get('direction')} {nv} {nu}"))
            except Exception as e:
                probs.append((i, f"note/null not numeric: {e}"))
        # sizes and keys
        sizes = b["sizes"]
        if not isinstance(sizes, dict): probs.append((i, f"sizes not a dict: {type(sizes).__name__}"))
        for k in b["data_keys"]:
            if k.get("dtype") not in ("float", "bool"): probs.append((i, f"dtype {k.get('key')}={k.get('dtype')}"))
            shape = k.get("shape")
            axes = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(shape))
            dims = []
            for ax in axes:
                v = sizes.get(ax) if isinstance(sizes, dict) else None
                if not isinstance(v, int): probs.append((i, f"axis {ax} of {k.get('key')} has no integer size")); continue
                dims.append(v)
                if v > 2000: probs.append((i, f"axis {ax}={v} > 2000"))
            if dims and math.prod(dims) > 2_000_000: probs.append((i, f"{k.get('key')} has {math.prod(dims)} values"))
        src = p.get("source")
        cnt[(src, tag if not a == "DEC" else None)] += 1
    summary[a] = {"n": len(B), "by_source_tag": {f"{s}|{t}": n for (s, t), n in sorted(cnt.items(), key=str)},
                  "task_pairs": task["pairs"], "task_reserves": task["reserves"]}
for i, msg in probs: print("PROBLEM", i, msg)
print(json.dumps(summary, indent=1))
