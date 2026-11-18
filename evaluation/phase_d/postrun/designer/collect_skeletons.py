"""PREREG_PHASE_D item 9 / P-1 amendment 2: copy a VALID world-author batch's skeletons from its sandbox into the case
folders: world/<label>/skeletons/<id>.py -> cases/<id>/skeletons/<arm>.py (arm from SANDBOX_MAP_world.json).
The sandbox is only read. A different existing target is refused (a redo must be recorded first and the old copy moved
aside by hand). Appends {target: {sha256, source, label, batch, arm}} to MANIFEST_skeletons.json.
Usage: py -I designer/collect_skeletons.py LABEL"""
import hashlib, json, os, shutil, sys
W = r"E:\Claude Projects\Kapi\phase_d_work"
label = sys.argv[1]
s = [x for x in json.load(open(os.path.join(W, "SANDBOX_MAP_world.json"))) if x["label"] == label]
assert len(s) == 1, label
s = s[0]
mp = os.path.join(W, "MANIFEST_skeletons.json")
man = json.load(open(mp)) if os.path.exists(mp) else {}
for i in s["ids"]:
    src = os.path.join(W, "world", label, "skeletons", i + ".py")
    dst = os.path.join(W, "cases", i, "skeletons", s["arm"] + ".py")
    h = hashlib.sha256(open(src, "rb").read()).hexdigest()
    if os.path.exists(dst):
        assert hashlib.sha256(open(dst, "rb").read()).hexdigest() == h, f"refusing to overwrite different {dst}"
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    man[os.path.relpath(dst, W)] = {"sha256": h, "source": os.path.relpath(src, W), "label": label,
                                    "batch": s["batch"], "arm": s["arm"]}
    print(i, s["arm"], h[:16])
json.dump(man, open(mp, "w"), indent=1, sort_keys=True)
