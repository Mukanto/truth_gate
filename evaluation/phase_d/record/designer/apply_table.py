"""PREREG_PHASE_D section 2.4: apply the decision table, with its Precedence and Counting-label rules, to the decisive
validity results (designer). Reads validity/<id>/RESULT.json for the given ids (default: all that exist) and writes
validity/TABLE_DECISIONS.json. It decides nothing that needs reading: a repair row names the stage and the error text;
the designer attributes the failing file.

Rows, in the order of the Precedence rule:
1. Drop rows, final when computed without an error in that stage: V2 failed; V1 failed (label V1a/V1b); timing failed;
   V1 erred with v1_final_drop_label set (that label). Counting label: V2 whenever V2 failed without an error, otherwise
   the V1 label, otherwise "timing infeasible".
2. Repair rows, only when no drop row applies: an error (error_in / error_stages; or reasons["setup"]); mechanical check
   (b) failed -> bodies; mechanical check (a) failed or the statistic not computable -> reference.py or the statistic.
3. valid -> pass."""
import glob, json, os, sys
W = r"E:\Claude Projects\Kapi\phase_d_work"
ids = sys.argv[1:] or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(W, "validity", "D-*", "RESULT.json")))
out = {}
for i in ids:
    r = json.load(open(os.path.join(W, "validity", i, "RESULT.json"), encoding="utf-8"))
    es = {k: v for k, v in (r.get("error_stages") or {}).items() if v}
    clean = lambda s: s not in es
    d = {"decisive": r.get("decisive"), "valid": r.get("valid"), "error_stages": sorted(es), "error_text": r.get("error_text"),
         "setup": (r.get("reasons") or {}).get("setup")}
    drops = []
    if r.get("v2") is False and clean("V2"):
        drops.append("V2")
    if r.get("v1") is False and clean("V1") and r.get("v1_label"):
        drops.append(r["v1_label"])
    if r.get("v1") is False and not clean("V1") and r.get("v1_final_drop_label"):
        drops.append(r["v1_final_drop_label"] + " (v1_final_drop_label)")
    if r.get("timing_ok") is False and clean("timing"):
        drops.append("timing infeasible")
    if drops:
        d["decision"] = "drop"
        d["failed_drop_rows"] = drops
        d["counting_label"] = "V2" if "V2" in drops else drops[0].split(" ")[0] if drops[0] != "timing infeasible" else "timing infeasible"
    elif r.get("valid"):
        d["decision"] = "pass"
    else:
        rows = []
        if es or d["setup"]:
            rows.append("error: one repair by the author of the failing file")
        if r.get("mech_b") is False and clean("mech"):
            rows.append("mechanical check (b): one repair of the bodies")
        if (r.get("mech_a") is False or r.get("structure_computable") is False) and clean("structure"):
            rows.append("mechanical check (a) / statistic: one repair of reference.py or of the statistic")
        d["decision"] = "repair" if rows else "UNCLASSIFIED (designer reads)"
        d["repair_rows"] = rows
        if r.get("v1_rate_label"):
            d["v1_rate_label_to_report_after_repair"] = r["v1_rate_label"]
    out[i] = d
json.dump(out, open(os.path.join(W, "validity", "TABLE_DECISIONS.json"), "w", encoding="utf-8"), indent=1)
from collections import Counter
print(Counter(v["decision"] for v in out.values()), Counter(v.get("counting_label") for v in out.values() if v["decision"] == "drop"))
for i, v in out.items():
    if v["decision"] not in ("pass", "drop"):
        print(i, v["decision"], v.get("repair_rows"), v["error_stages"], (v["error_text"] or "")[:200], v["setup"])
