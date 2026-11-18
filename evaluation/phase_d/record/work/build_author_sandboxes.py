"""Phase D section 3 item 2: build the five brief-author sandboxes (designer).

Each sandbox holds copies of only: BRIEF_AUTHOR_D.md, SOURCES.md (keys and references of the author's sources),
SOURCES_D.md (the intro and the author's rows), TASK.json, agent_docs/ (frozen, FREEZE_AGENT_DOCS.json). Inputs are made
read-only and hashed (MANIFEST_authors.json). TASK.json follows the frozen content rule (PREREG_PHASE_D section 3 item 2):
class, half, the counts of pairs and reserves per subtype or tag and source, the sources, and the (tag, family)
combinations that Phases B and C used for those sources.
"""
import collections
import hashlib
import json
import os
import shutil
import stat

REPO = r"E:\Claude Projects\kapi-oss"
PD = os.path.join(REPO, "evaluation", "phase_d")
PC = os.path.join(REPO, "evaluation", "phase_c")
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
OUT = os.path.join(WORK, "authors")
assert not os.path.exists(OUT)
ALLOC = json.load(open(os.path.join(PD, "ALLOCATION_D.json"), encoding="utf-8"))

# earlier (tag, family) combinations by source: Phase B table and Phase C private notes
combos = collections.defaultdict(set)
for x in json.load(open(os.path.join(PC, "PHASE_B_TABLE.json"), encoding="utf-8"))["pairs"]:
    combos[x["source"]].add((x.get("mechanism_tag"), x.get("statistic_family")))
for cls in ("B1", "B2", "B3", "B6", "O"):
    for x in json.load(open(os.path.join(PC, "record", "authors", cls, "PRIVATE.json"), encoding="utf-8")):
        combos[x["source"]].add((x.get("mechanism_tag"), x.get("statistic_family")))

# SOURCES_D.md rows by key
src_lines = open(os.path.join(PD, "SOURCES_D.md"), encoding="utf-8").read().split("\n")
intro_end = next(i for i, l in enumerate(src_lines) if l.startswith("## B-2"))
INTRO = "\n".join(src_lines[:intro_end]).rstrip() + "\n"


def rows_for(section_title, keys):
    i = next(k for k, l in enumerate(src_lines) if l.startswith(section_title))
    j = next((k for k in range(i + 1, len(src_lines)) if src_lines[k].startswith("## ")), len(src_lines))
    sec = src_lines[i:j]
    header = [l for l in sec if l.startswith("| Key") or l.startswith("|---")]
    rows = [l for l in sec if l.startswith("| ") and not l.startswith("| Key")]
    pick = [r for r in rows if r.split("|")[1].strip().split(" ")[0] in keys]
    assert len(pick) == len(keys), (section_title, keys, [r[:20] for r in pick])
    notes = [l for l in sec if l and not l.startswith("|") and not l.startswith("## ")]
    return sec[0], header, pick, notes


def reference(row):
    return row.split("|")[2].strip()


def counts(pairs):
    return {src: dict(v) for src, v in pairs.items()}


AUTHORS = {
    "B2A": ("B-2", "A", ALLOC["B-2"]["half_A"], "## B-2"),
    "B2B": ("B-2", "B", ALLOC["B-2"]["half_B"], "## B-2"),
    "B3A": ("B-3", "A", ALLOC["B-3"]["half_A"], "## B-3"),
    "B3B": ("B-3", "B", ALLOC["B-3"]["half_B"], "## B-3"),
}
manifest = {}
for aid, (cls, half, alloc, sec_title) in AUTHORS.items():
    keys = alloc["sources"]
    title, header, rows, notes = rows_for(sec_title, keys)
    task = {
        "author": aid, "class": cls, "half": half, "local_id_prefix": aid + "-",
        "pairs": counts(alloc["pairs"]),
        "reserves": [{"source": s, ("subtype" if cls == "B-2" else "mechanism_tag"): t} for s, t in alloc["reserve_order"]],
        "sources": keys,
        "earlier_tag_family_combinations": {k: sorted([list(c) for c in combos.get(k, set())]) for k in keys},
        "total_pairs": sum(sum(v.values()) for v in alloc["pairs"].values()),
        "total_reserves": len(alloc["reserve_order"]),
    }
    os.makedirs(os.path.join(OUT, aid))
    json.dump(task, open(os.path.join(OUT, aid, "TASK.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    sd = INTRO + "\n" + title + "\n\n" + "\n".join(header + rows) + "\n" + ("\n" + "\n".join(notes) + "\n" if notes else "")
    open(os.path.join(OUT, aid, "SOURCES_D.md"), "w", encoding="utf-8", newline="\n").write(sd)
    s = "# Sources (keys and references)\n\n" + "\n".join(f"- **{r.split('|')[1].strip().split(' ')[0]}**: {reference(r)}" for r in rows) + "\n"
    open(os.path.join(OUT, aid, "SOURCES.md"), "w", encoding="utf-8", newline="\n").write(s)

# decoys
dec = ALLOC["decoys"]
keys = sorted(set(list(dec["B-1"]["pairs"]) + list(dec["B-6"]["pairs"]) + [r[0] for r in dec["B-1"]["reserve_order"]] + [r[0] for r in dec["B-6"]["reserve_order"]]))
title, header, rows, notes = rows_for("## Decoys", keys)
task = {
    "author": "DEC", "class": "decoys (B-1 and B-6)", "half": "all", "local_id_prefix": "DEC-",
    "pairs": {"B-1": dec["B-1"]["pairs"], "B-6": dec["B-6"]["pairs"]},
    "reserves": [{"class": "B-1", "source": r[0]} for r in dec["B-1"]["reserve_order"]] +
                [{"class": "B-6", "source": r[0]} for r in dec["B-6"]["reserve_order"]],
    "sources": keys,
    "earlier_tag_family_combinations": {k: sorted([list(c) for c in combos.get(k, set())]) for k in keys},
    "total_pairs": 8, "total_reserves": 4,
}
os.makedirs(os.path.join(OUT, "DEC"))
json.dump(task, open(os.path.join(OUT, "DEC", "TASK.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
sd = INTRO + "\n" + title + "\n\n" + "\n".join(header + rows) + "\n"
open(os.path.join(OUT, "DEC", "SOURCES_D.md"), "w", encoding="utf-8", newline="\n").write(sd)
open(os.path.join(OUT, "DEC", "SOURCES.md"), "w", encoding="utf-8", newline="\n").write(
    "# Sources (keys and references)\n\n" + "\n".join(f"- **{r.split('|')[1].strip().split(' ')[0]}**: {reference(r)}" for r in rows) + "\n")

# common files, read-only, manifest
for aid in list(AUTHORS) + ["DEC"]:
    d = os.path.join(OUT, aid)
    shutil.copy2(os.path.join(PD, "BRIEF_AUTHOR_D.md"), os.path.join(d, "BRIEF_AUTHOR_D.md"))
    shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(d, "agent_docs"))
    for dp, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(dp, f)
            os.chmod(p, stat.S_IREAD)
            manifest[os.path.relpath(p, OUT)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
json.dump(manifest, open(os.path.join(WORK, "MANIFEST_authors.json"), "w"), indent=1, sort_keys=True)
print(len(manifest), "input files in 5 sandboxes")
