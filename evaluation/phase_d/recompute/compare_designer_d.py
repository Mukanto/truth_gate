"""Compare RECOMPUTE_D.json (designer, independent) with score/RESULTS_D.json (official).

Reads both result files only; changes neither.  Writes COMPARE_D.json and COMPARE_D.md.
Run:  py -I -B compare_designer_d.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
MINE = json.load(open(os.path.join(HERE, "RECOMPUTE_D.json"), encoding="utf-8"))
OFF = json.load(open(os.path.join(WORK, "score", "RESULTS_D.json"), encoding="utf-8"))
TOL = 5e-7        # the official bounds are rounded to 6 decimals

items = []        # every compared item


def add(group, key, mine, off, tol=None):
    if tol is not None and mine is not None and off is not None:
        agree = abs(mine - off) <= tol
    else:
        agree = mine == off
    items.append({"group": group, "item": key, "mine": mine, "official": off, "agree": bool(agree)})


# -------------------------------------------------------------- per (id, arm)
opairs = {(p["id"], p["arm"]): p for p in OFF["pairs"]}
for arm in ("R", "W0", "W1"):
    for cid, m in MINE["pairs"][arm].items():
        o = opairs[(cid, arm)]
        k = "%s/%s" % (cid, arm)
        add("pair", k + " faulty_verdict", m["faulty_verdict"], o["faulty"]["verdict"])
        add("pair", k + " fixed_verdict", m["fixed_verdict"], o["fixed"]["verdict"])
        add("pair", k + " attrition", m["attrition"], o["attrition_any"])
        add("pair", k + " pb_detected", m["pb_detected"], o["pb"]["detected"])
        add("pair", k + " noise_only", m["noise_only"], o["pb"]["baseline_noise_only"])
        add("pair", k + " declared_only_baseline", m["declared_only_baseline"], o["pb"]["baseline_declared_only"])
        add("pair", k + " clean_pass", m["clean_pass"], o["pb"]["clean"])
        add("pair", k + " clean_pass_no_noise", m["clean_pass_no_noise"], o["pb"]["clean_wo_noise"])
        add("pair", k + " attributable", m["attributable"], o["attributable"])
        add("pair", k + " generic", m["generic"], o["generic"])
        add("pair", k + " declared", m["declared"], o["declared"])
        ms = sorted({q["stream"] for q in m["qualifying"]})
        os_ = sorted({q["stream"] for q in o["qualifying"]})
        add("pair", k + " qualifying_streams", ms, os_)
        # per stream counts + Fisher p
        om = {}
        for q in o["qualifying"]:
            om[q["stream"]] = (q["faulty_holds"], q["faulty_n"], q["fixed_holds"], q["fixed_n"], q["p"])
        mm = {}
        for q in m["qualifying"]:
            mm[q["stream"]] = (q["faulty"][0], q["faulty"][1], q["fixed"][0], q["fixed"][1], q["fisher_p"])
        for s in sorted(set(om) | set(mm)):
            a, b = mm.get(s), om.get(s)
            same = a is not None and b is not None and a[:4] == b[:4] and \
                abs(a[4] - b[4]) <= 1e-9 * max(1.0, abs(b[4])) + 1e-300
            if a is not None and b is not None and a[:4] == b[:4]:
                same = abs(a[4] - b[4]) <= 1e-9 * abs(b[4]) + 1e-300
            items.append({"group": "pair-stream", "item": "%s stream %s (faulty h/n, fixed h/n, p)" % (k, s),
                          "mine": list(a) if a else None, "official": list(b) if b else None,
                          "agree": bool(same)})

# -------------------------------------------------------------------- tables
MAP = {"pairs": "n", "pb_style": "pb_detection", "attributable": "attributable", "generic": "generic",
       "declared": "declared", "clean": "clean_pass", "clean_wo_noise": "clean_pass_no_noise",
       "baseline_noise_only": "noise_only", "baseline_declared_only": "declared_only",
       "baseline_flag_everything": "flag_everything_detection"}
LOWER = {"attributable_lower": "attributable", "clean_lower": "clean_pass", "pb_style_lower": "pb_detection"}
for arm in ("R", "W0", "W1"):
    for ocls, mcls in (("B-2", "B-2"), ("B-3", "B-3"), ("B-1", "B-1"), ("B-6", "B-6"),
                       ("decoys", "decoys(B-1+B-6)")):
        o = OFF["per_arm_class"][arm][ocls]
        m = MINE["tables"][arm][mcls]
        g = "table %s %s" % (arm, ocls)
        for ok, mk in MAP.items():
            mv = m["n"] if mk == "n" else m[mk]["count"]
            add(g, ok, mv, o[ok])
        add(g, "both", m["generic_and_declared"], o["both"])
        add(g, "generic_only", m["generic_only"], o["generic_only"])
        add(g, "declared_only", m["declared_only_attributable"], o["declared_only"])
        add(g, "attrition pairs", m["attrition_pairs"], len(o["attrition_list"]))
        for ok, mk in LOWER.items():
            add(g, ok, m[mk]["wilson_lower"], o[ok], tol=TOL)

# ---------------------------------------------------------------- hypotheses
for h in ("H-D1", "H-D2"):
    m = MINE["H-D1_H-D2"][h]
    o = OFF["hypotheses"][h]
    add(h, "n", m["n"], o["n"])
    add(h, "attributable count", m["attributable"]["count"], o["k_detect"])
    add(h, "clean count", m["clean_pass"]["count"], o["k_clean"])
    add(h, "attributable lower", m["attributable"]["wilson_lower"], o["detect_lower"], tol=TOL)
    add(h, "clean lower", m["clean_pass"]["wilson_lower"], o["clean_lower"], tol=TOL)
    add(h, "verdict", m["verdict"], o["verdict"])

m3, o3 = MINE["H-D3"], OFF["hypotheses"]["H-D3"]
add("H-D3", "pooled pairs", m3["pairs_in_pool"], o3["pooled_pairs"])
add("H-D3", "comparable pairs", sorted(p["id"] for p in m3["per_pair"] if p["comparable"]),
    sorted(o3["comparable_pairs"]))
add("H-D3", "not comparable", sorted(e["id"] for e in m3["exclusions"]), sorted(
    x["id"] if isinstance(x, dict) else x for x in o3["not_comparable"]))
for name, mm, oo in (("main", m3, o3["main"]), ("sensitivity", m3["sensitivity"],
                                                   o3["sensitivity_not_comparable_counted_as_non_detections"])):
    add("H-D3 " + name, "b (W1 only)", mm["b_W1_only"], oo["b_w1_only"])
    add("H-D3 " + name, "c (W0 only)", mm["c_W0_only"], oo["c_w0_only"])
    add("H-D3 " + name, "both", mm["both"], oo["both"])
    add("H-D3 " + name, "neither", mm["neither"], oo["neither"])
    add("H-D3 " + name, "p", mm["p_exact_one_sided"], oo["p"], tol=1e-12)
    add("H-D3 " + name, "label", mm["label"], oo["verdict"])
for k in ("B-2", "B-3"):
    add("H-D3 per class", k + " b", m3["per_class"][k]["b_W1_only"],
        o3["main"]["discordant_per_class"][k]["b_w1_only"])
    add("H-D3 per class", k + " c", m3["per_class"][k]["c_W0_only"],
        o3["main"]["discordant_per_class"][k]["c_w0_only"])

mg, og = MINE["clean_pass_guard"], OFF["hypotheses"]["clean_pass_guard"]
add("guard", "pairs", mg["n"], og["pairs"])
add("guard", "W0 clean", sum(1 for g in mg["per_pair"] if g["W0"]), og["w0_clean"])
add("guard", "W1 clean", sum(1 for g in mg["per_pair"] if g["W1"]), og["w1_clean"])
add("guard", "W0 clean only (b)", mg["b_W0_clean_W1_not"], og["w0_clean_only"])
add("guard", "W1 clean only (c)", mg["c_W1_clean_W0_not"], og["w1_clean_only"])
add("guard", "p", mg["p_exact_one_sided"], og["p"], tol=1e-12)
oa = OFF["hypotheses"]["adoption_inputs"]
add("adoption", "pooled clean difference W1-W0", mg["pooled_W1_minus_W0_clean_pass"],
    oa["pooled_clean_difference_w1_minus_w0_on_h_d3_pairs"])
add("adoption", "decoys clean W0", mg["decoy_clean_pass_W0"], oa["decoys_clean_w0"])
add("adoption", "decoys clean W1", mg["decoy_clean_pass_W1"], oa["decoys_clean_w1"])

dis = [i for i in items if not i["agree"]]
out = {"compared_items": len(items), "disagreements": len(dis),
       "by_group": {}, "disagreement_list": dis, "items": items}
for i in items:
    g = i["group"].split(" ")[0]
    out["by_group"].setdefault(g, [0, 0])
    out["by_group"][g][0] += 1
    out["by_group"][g][1] += (not i["agree"])
json.dump(out, open(os.path.join(HERE, "COMPARE_D.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

L = ["# COMPARE_D", "",
     "Designer recomputation (`RECOMPUTE_D.json`) against the official scoring (`score/RESULTS_D.json`).",
     "Compared items: %d; disagreements: %d." % (len(items), len(dis)), "",
     "| group | items | disagreements |", "|---|---|---|"]
for g, (n, d) in out["by_group"].items():
    L.append("| %s | %d | %d |" % (g, n, d))
L += ["", "## Disagreements", ""]
if not dis:
    L.append("None.")
for i in dis:
    L.append("- [%s] %s: mine = %s, official = %s" % (i["group"], i["item"], i["mine"], i["official"]))
L.append("")
open(os.path.join(HERE, "COMPARE_D.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("items", len(items), "disagreements", len(dis))
for i in dis:
    print(i["group"], "|", i["item"], "|", i["mine"], "|", i["official"])
print(out["by_group"])
