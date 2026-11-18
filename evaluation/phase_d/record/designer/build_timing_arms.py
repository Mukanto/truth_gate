"""PREREG_PHASE_D item 10: write TIMING_ARMS.json from the decisive "timing_arm" lines of cases/validity_log.jsonl
(format of tools/check_validity_log_d.py: a list of {"id", "arm", "skeleton_sha256", "body_sha256", "estimate_s", "redo"};
redo is true exactly when the estimate is above 1800 s). One entry per (id, arm, skeleton hash, fixed-body hash) whose
skeleton is the one now in cases/<id>/skeletons/<arm>.py. Usage: py -I designer/build_timing_arms.py OUT.json"""
import hashlib, json, os, sys
W = r"E:\Claude Projects\Kapi\phase_d_work"
cur = {}
for i in sorted(os.listdir(os.path.join(W, "cases"))):
    for arm in ("W0", "W1"):
        p = os.path.join(W, "cases", i, "skeletons", arm + ".py")
        if os.path.exists(p):
            cur[(i, arm)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
out = []
for ln in open(os.path.join(W, "cases", "validity_log.jsonl"), encoding="utf-8"):
    e = json.loads(ln)
    if e.get("mode") != "timing_arm" or e.get("dev") or e.get("decisive") is not True:
        continue
    k = (e["case"], e["arm"])
    if cur.get(k) != e["sha256"]["skeleton"]:
        continue
    est = e["result"]["estimate_s"]
    out.append({"id": e["case"], "arm": e["arm"], "skeleton_sha256": e["sha256"]["skeleton"],
                "body_sha256": e["sha256"]["fixed_body.py"], "estimate_s": est, "redo": est is not None and est > 1800})
missing = sorted(set(cur) - {(t["id"], t["arm"]) for t in out})
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), indent=1)
print(f"{len(out)} entries; redo {sum(t['redo'] for t in out)}; skeletons without a decisive timing run: {missing}")
