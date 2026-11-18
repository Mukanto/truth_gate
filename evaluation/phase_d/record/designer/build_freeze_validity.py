"""PREREG_PHASE_D section 3 item 8: FREEZE_VALIDITY.json (designer).

"pairs": every validated pair, each {"id", "result" (its decisive RESULT.json), "repairs": [...], "decision",
"counting_label", "fidelity_a"}; the extra keys are ignored by tools/check_validity_log_d.py. Also "pre_validity_drops"
(the reference-check drops), "selection" (validity/SELECTION_*.json: the pairs and decoys that go to the world authors,
with substitutions), "audit_a" (per pair: overall and failed items), "label_counts", and the SHA-256 of the inputs.
Usage: build_freeze_validity.py OUT.json [--allow-pending]"""
import glob, hashlib, json, os, sys
W = r"E:\Claude Projects\Kapi\phase_d_work"
out = sys.argv[1]
allow_pending = "--allow-pending" in sys.argv
dec = json.load(open(os.path.join(W, "validity", "TABLE_DECISIONS.json"), encoding="utf-8"))
idmap = {m["id"]: m for m in json.load(open(os.path.join(W, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))}
REPAIRS = {}  # id -> list of {"file", "reason", "after_run_sha256"}; none so far
PRE = {"D-014": "reference rejected by check_skeletons_d (P-3 event 2)", "D-041": "reference rejected by check_skeletons_d (P-3 event 2)"}
audit = {}
for g in ("B2", "B3", "DEC"):
    f = os.path.join(W, "audit_a", g, "AUDIT_A.json")
    if os.path.exists(f):
        for x in json.load(open(f, encoding="utf-8")):
            audit[x["case"]] = {"overall": x["overall"], "failed_items": [k for k in "abcdefghijkmp" if x.get(k) == "no"]}
pending = sorted(set(idmap) - set(dec) - set(PRE))
assert allow_pending or not pending, f"pending: {pending}"
pairs = []
for i in sorted(dec):
    r = json.load(open(os.path.join(W, "validity", i, "RESULT.json"), encoding="utf-8"))
    pairs.append({"id": i, "result": r, "repairs": REPAIRS.get(i, []), "decision": dec[i]["decision"],
                  "counting_label": dec[i].get("counting_label"), "fidelity_a": audit.get(i)})
sel = json.load(open(os.path.join(W, "validity", "SELECTION_provisional.json"), encoding="utf-8"))
from collections import Counter
labels = Counter(p["counting_label"] for p in pairs if p["decision"] == "drop")
labels.update({"reference rejected by check_skeletons_d": len(PRE)})
labels.update(f"fidelity A ({','.join(a['failed_items'])})" for a in audit.values() if a["overall"] != "pass")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
freeze = {"note": "PREREG_PHASE_D section 3 item 8; built by designer/build_freeze_validity.py", "pairs": pairs,
          "pre_validity_drops": PRE, "audit_a": audit, "selection": sel, "label_counts": dict(labels),
          "pending": pending,
          "inputs_sha256": {"validity/TABLE_DECISIONS.json": sha(os.path.join(W, "validity", "TABLE_DECISIONS.json")),
                            "cases/validity_log.jsonl": sha(os.path.join(W, "cases", "validity_log.jsonl")),
                            "validity/SELECTION_provisional.json": sha(os.path.join(W, "validity", "SELECTION_provisional.json"))}}
json.dump(freeze, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(pairs), "pairs;", "pending:", pending, "; labels:", dict(labels))
