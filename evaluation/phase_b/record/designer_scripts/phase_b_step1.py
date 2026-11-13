"""Phase B step 1 (designer): strip source remarks from B-1 sizes, assign classes, shuffle briefs for the world author."""
import json, os, re, secrets, shutil, datetime

ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b"
BACKUP = r"E:\Claude Projects\Kapi\phase_b_private"
CLASSES = {"B1": "B-1", "B2": "B-2", "B3": "B-3", "B6": "B-6", "O": "O"}
STAMP = datetime.datetime.now().isoformat(timespec="seconds")

# 1. B-1 sizes: remove parenthetical remarks that mention the source; keep them in the private note.
b1 = os.path.join(ROOT, "B1")
briefs = json.load(open(os.path.join(b1, "BRIEFS.json"), encoding="utf-8"))
priv = json.load(open(os.path.join(b1, "PRIVATE.json"), encoding="utf-8"))
pmap = {p["local_id"]: p for p in priv}
log = []
for b in briefs:
    m = re.search(r"\s*\(([^)]*)\)\s*\.?\s*$", b["sizes"])
    if m and re.search(r"source|VUL09|KRI09|MAK19|BAR05", m.group(1), re.I):
        removed = m.group(1)
        b["sizes"] = b["sizes"][: m.start()].rstrip() + "."
        pmap[b["local_id"]]["notes"] = (pmap[b["local_id"]].get("notes", "") + f" [Designer {STAMP}: removed from the brief's sizes field because it referred to the source: '{removed}'.]").strip()
        log.append(f"- {b['local_id']}: removed from sizes: ({removed})")
json.dump(briefs, open(os.path.join(b1, "BRIEFS.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(priv, open(os.path.join(b1, "PRIVATE.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
with open(os.path.join(b1, "LOG.md"), "a", encoding="utf-8") as f:
    f.write(f"\n\n## Designer edit, {STAMP} (step 1, before shuffling)\n\nSource remarks removed from the `sizes` field of the "
            "public briefs (moved to the private notes); claims and data keys untouched.\n" + "\n".join(log) + "\n")
print("B-1 sizes edits:", len(log))

# 2. Class assignment (PREREG §1): every brief keeps its author's class; B-2 subtype from the private note.
assignment = []
public = []
for d, cls in CLASSES.items():
    bl = json.load(open(os.path.join(ROOT, d, "BRIEFS.json"), encoding="utf-8"))
    pv = {p["local_id"]: p for p in json.load(open(os.path.join(ROOT, d, "PRIVATE.json"), encoding="utf-8"))}
    for b in bl:
        p = pv[b["local_id"]]
        sub = p.get("subtype", "").split()[0] if cls in ("B-2", "O") and p.get("subtype") else ""
        assignment.append({"local_id": b["local_id"], "author_folder": d, "class": cls, "subtype": sub,
                           "source": p["source"].split()[0].strip(",;").upper()})
        public.append({"local_id": b["local_id"], "claim": b["claim"], "data_keys": b["data_keys"], "sizes": b["sizes"]})

# 3. Random ids and shuffle.
order = list(range(len(public)))
for i in range(len(order) - 1, 0, -1):  # Fisher-Yates with a cryptographic generator
    j = secrets.randbelow(i + 1)
    order[i], order[j] = order[j], order[i]
id_map = []
shuffled = []
for k, idx in enumerate(order, start=1):
    wid = f"W{k:02d}"
    pb = public[idx]
    shuffled.append({"id": wid, "claim": pb["claim"], "data_keys": pb["data_keys"], "sizes": pb["sizes"]})
    a = dict(assignment[idx]); a["world_id"] = wid
    id_map.append(a)

os.makedirs(os.path.join(ROOT, "world"), exist_ok=True)
json.dump(shuffled, open(os.path.join(ROOT, "world", "BRIEFS_SHUFFLED.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(id_map, open(os.path.join(ROOT, "ID_MAP_AND_CLASSES.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("shuffled briefs:", len(shuffled))

# 4. Backup (the private map lives outside the world folder).
shutil.copytree(ROOT, BACKUP, dirs_exist_ok=True)
print("backup refreshed")
