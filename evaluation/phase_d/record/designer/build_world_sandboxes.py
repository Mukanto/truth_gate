"""PREREG_PHASE_D section 3 item 9 (with REVISIONS-post-freeze P-1): world-author sandboxes, one per batch and arm.

Input: shuffle/batches_subset_NN.json (tools/shuffle_d.py --subset, after FREEZE_VALIDITY.json). For every batch and each
arm, a sandbox world/<label>/ with a neutral random label (no path names an arm): WORLD_INSTRUCTIONS_D.md (a copy of
WORLD_INSTRUCTIONS_D0.md for W-0, WORLD_INSTRUCTIONS_D1.md for W-1), BATCH.json (the batch file, unchanged), agent_docs/
and pkg/ (record/, frozen), and an empty skeletons/ folder. Inputs read-only. The private map (label -> batch, arm) is SANDBOX_MAP_world.json in the work folder,
outside world/; the manifest of the inputs is MANIFEST_world.json. Refuses to run if
world/ exists."""
import glob, hashlib, json, os, secrets, shutil, stat
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
OUT = os.path.join(WORK, "world")
assert not os.path.exists(OUT), "world/ exists"
batches = sorted(glob.glob(os.path.join(WORK, "shuffle", "batches_subset_*.json")))
assert batches, "no subset batches"
os.makedirs(OUT)
smap, manifest, used = [], {}, set()
for b in batches:
    n = int(os.path.basename(b).split("_")[-1].split(".")[0])
    for arm, instr in (("W0", "WORLD_INSTRUCTIONS_D0.md"), ("W1", "WORLD_INSTRUCTIONS_D1.md")):
        label = secrets.token_hex(3)
        while label in used:
            label = secrets.token_hex(3)
        used.add(label)
        sb = os.path.join(OUT, label)
        os.makedirs(os.path.join(sb, "skeletons"))
        shutil.copy2(os.path.join(PD, instr), os.path.join(sb, "WORLD_INSTRUCTIONS_D.md"))
        shutil.copy2(b, os.path.join(sb, "BATCH.json"))
        shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(sb, "agent_docs"))
        shutil.copytree(os.path.join(WORK, "record", "pkg"), os.path.join(sb, "pkg"))
        ids = [x["id"] for x in json.load(open(b, encoding="utf-8"))]
        smap.append({"label": label, "batch": n, "arm": arm, "instructions": instr, "ids": ids,
                     "sandbox": sb})
        for dp, _, fs in os.walk(sb):
            for f in fs:
                q = os.path.join(dp, f)
                manifest[os.path.relpath(q, OUT)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
                os.chmod(q, stat.S_IREAD)
json.dump(smap, open(os.path.join(WORK, "SANDBOX_MAP_world.json"), "w"), indent=1)
json.dump(manifest, open(os.path.join(WORK, "MANIFEST_world.json"), "w"), indent=1, sort_keys=True)
for s in smap:
    print(s["batch"], s["arm"], s["label"], len(s["ids"]))
