"""PREREG_PHASE_D item 9, PC section 4 item 3: a stopped or invalid world-author batch goes to a NEW fresh agent in a NEW
sandbox (the old sandbox stays untouched, so the new agent never sees files it did not write).

Usage: py -I designer/add_world_sandbox.py BATCH_NUMBER W0|W1 REASON
Builds world/<new neutral label>/ exactly as build_world_sandboxes.py does (same inputs, read-only, empty skeletons/),
appends the entry to SANDBOX_MAP_world.json (with "redo_of" = the earlier labels of that batch and arm, and the reason)
and the input hashes to MANIFEST_world.json. Prints the new label."""
import glob, hashlib, json, os, secrets, shutil, stat, sys
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
OUT = os.path.join(WORK, "world")
n, arm, reason = int(sys.argv[1]), sys.argv[2], sys.argv[3]
instr = {"W0": "WORLD_INSTRUCTIONS_D0.md", "W1": "WORLD_INSTRUCTIONS_D1.md"}[arm]
b = os.path.join(WORK, "shuffle", "batches_subset_%02d.json" % n)
assert os.path.exists(b), b
mp = os.path.join(WORK, "SANDBOX_MAP_world.json")
mf = os.path.join(WORK, "MANIFEST_world.json")
smap = json.load(open(mp))
manifest = json.load(open(mf))
used = {s["label"] for s in smap} | set(os.listdir(OUT))
label = secrets.token_hex(3)
while label in used:
    label = secrets.token_hex(3)
sb = os.path.join(OUT, label)
os.makedirs(os.path.join(sb, "skeletons"))
shutil.copy2(os.path.join(PD, instr), os.path.join(sb, "WORLD_INSTRUCTIONS_D.md"))
shutil.copy2(b, os.path.join(sb, "BATCH.json"))
shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(sb, "agent_docs"))
shutil.copytree(os.path.join(WORK, "record", "pkg"), os.path.join(sb, "pkg"))
for dp, _, fs in os.walk(sb):
    for f in fs:
        q = os.path.join(dp, f)
        manifest[os.path.relpath(q, OUT)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
        os.chmod(q, stat.S_IREAD)
earlier = [s["label"] for s in smap if s["batch"] == n and s["arm"] == arm]
smap.append({"label": label, "batch": n, "arm": arm, "instructions": instr,
             "ids": [x["id"] for x in json.load(open(b, encoding="utf-8"))], "sandbox": sb,
             "redo_of": earlier, "reason": reason})
json.dump(smap, open(mp, "w"), indent=1)
json.dump(manifest, open(mf, "w"), indent=1, sort_keys=True)
print(label)
