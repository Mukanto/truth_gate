"""Phase B step 4 (designer): copy each frozen skeleton to its criterion author's folder under the real case id."""
import json, os, shutil, collections
ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b"
idmap = json.load(open(os.path.join(ROOT, "ID_MAP_AND_CLASSES.json"), encoding="utf-8"))
briefs = {b["id"]: b for b in json.load(open(os.path.join(ROOT, "world", "BRIEFS_SHUFFLED.json"), encoding="utf-8"))}
per = collections.defaultdict(list)
for a in idmap:
    case = os.path.join(ROOT, a["author_folder"], "cases", a["local_id"])
    os.makedirs(case, exist_ok=True)
    src = os.path.join(ROOT, "world", "skeletons", a["world_id"] + ".py")
    for name in ("skeleton.py", "faulty.py", "fixed.py"):
        dst = os.path.join(case, name)
        if os.path.exists(dst):
            raise SystemExit(f"refusing to overwrite {dst}")
        shutil.copyfile(src, dst)  # content only: the copies are writable, the frozen original stays read-only
    meta = {"local_id": a["local_id"], "world_id": a["world_id"], "class": a["class"], "subtype": a["subtype"],
            "source": a["source"], "brief": briefs[a["world_id"]]}
    json.dump(meta, open(os.path.join(case, "ASSIGNMENT.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    per[a["author_folder"]].append(f'{a["local_id"]}<-{a["world_id"]}')
for k in sorted(per):
    print(k, len(per[k]), " ".join(sorted(per[k])))
