"""Phase C part 2 setup (designer; PREREG_PHASE_C section 4 item 5, AUTHOR_PHASE2_C.md "Your cases").

For every id in designer/ID_MAP.json: authors/<folder>/cases/<local_id>/ with skeleton.py (read-only reference copy),
faulty.py and fixed.py (writable copies) of the frozen skeleton fable/batchNN/skeletons/<Cnn>.py, and ASSIGNMENT.json
(case id, world id, class, subtype, source, the brief as the world author saw it). Copies AUTHOR_PHASE2_C.md into every
class folder, creates work/, and copies the B-1 brief author's own source extracts (written to the session scratchpad in
step 2, archived by P-2) into authors/B1/src/. Refuses to overwrite. Checks every copy against FREEZE_SKELETONS.json.

Usage: py -I part2_build.py PHASE_C_PRIVATE REPO_PHASE_C_DIR
"""
import hashlib, json, os, shutil, stat, sys
from collections import defaultdict

root, pc = sys.argv[1], sys.argv[2]
J = lambda *p: os.path.join(root, *p)
idmap = json.load(open(J("designer", "ID_MAP.json"), encoding="utf-8"))
briefs = {b["id"]: b for b in json.load(open(J("world", "BRIEFS_SHUFFLED.json"), encoding="utf-8"))}
frozen = json.load(open(J("FREEZE_SKELETONS.json"), encoding="utf-8"))["files"]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def batch_of(cid):
    n = int(cid[1:])
    return "batch01" if n <= 15 else "batch02" if n <= 30 else "batch03" if n <= 45 else "batch04"


def copy_new(src, dst):
    if os.path.exists(dst):
        raise SystemExit(f"refusing to overwrite {dst}")
    shutil.copyfile(src, dst)


notes = {}
for folder in ("B1", "B2", "B3", "B6", "O"):
    for n in json.load(open(J("authors", folder, "PRIVATE.json"), encoding="utf-8")):
        notes[(folder, n["local_id"])] = n

per = defaultdict(list)
for a in idmap:
    folder, lid, cid, cls = a["folder"], a["local_id"], a["id"], a["class"]
    n = notes[(folder, lid)]
    rel = f"fable/{batch_of(cid)}/skeletons/{cid}.py"
    src = J(*rel.split("/"))
    if sha(src) != frozen[rel]:
        raise SystemExit(f"{rel} does not match FREEZE_SKELETONS.json")
    case = J("authors", folder, "cases", lid)
    os.makedirs(case, exist_ok=True)
    for name in ("skeleton.py", "faulty.py", "fixed.py"):
        copy_new(src, os.path.join(case, name))
        if sha(os.path.join(case, name)) != frozen[rel]:
            raise SystemExit(f"copy mismatch {case}/{name}")
    os.chmod(os.path.join(case, "skeleton.py"), stat.S_IREAD)
    subtype = n.get("subtype") if cls == "B-2" else (n.get("mechanism_tag") if cls == "O" else None)
    meta = {"case_id": lid, "world_id": cid, "class": cls, "subtype": subtype, "source": n["source"],
            "brief": briefs[cid]}
    p = os.path.join(case, "ASSIGNMENT.json")
    if os.path.exists(p):
        raise SystemExit(f"refusing to overwrite {p}")
    json.dump(meta, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    per[folder].append(f"{lid}<-{cid}")

for folder in ("B1", "B2", "B3", "B6", "O"):
    copy_new(os.path.join(pc, "AUTHOR_PHASE2_C.md"), J("authors", folder, "AUTHOR_PHASE2_C.md"))
    os.makedirs(J("authors", folder, "work"), exist_ok=True)
os.makedirs(J("authors", "B1", "src"), exist_ok=True)
for f in ("kri09.txt", "kri10.txt", "mak19.txt"):
    copy_new(J("designer", "scratchpad_archive_2026-11-15", f), J("authors", "B1", "src", f))

for k in sorted(per):
    print(k, len(per[k]), " ".join(sorted(per[k])))
