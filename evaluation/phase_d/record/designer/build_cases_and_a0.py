"""PREREG_PHASE_D section 2.1 (case files) and section 3 item 3 (fidelity part A0 sandboxes), designer.

cases/<id>/brief.json   {"id", "claim", "data_keys" (with dims), "sizes"} from shuffle/BRIEFS_SHUFFLED.json
cases/<id>/PRIVATE.json the author's note: local_id -> neutral id; mechanism_tag and subtype -> subtype_or_tag; class
                        from the allocation; approved_value is added after part A0 (and written into
                        structure_statistic.note_value). Every other field is copied unchanged.
audit_a0/<B2|B3|DEC>/   FIDELITY_AUDIT_D.md, PREREG_PHASE_D.md, P2_READING_D.md, SOURCES.md, SOURCES_D.md, agent_docs/,
                        and class/<id>/ with brief.json, PRIVATE.json and PASSAGE.md (the documenting passage from
                        SOURCES_D.md and the note's own passage). Inputs read-only; manifest MANIFEST_a0.json.
"""
import hashlib, json, os, shutil, stat
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
shuf = json.load(open(os.path.join(WORK, "shuffle", "BRIEFS_SHUFFLED.json"), encoding="utf-8"))
idmap = {m["id"]: m for m in json.load(open(os.path.join(WORK, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))}
notes = {}
for a in ["B2A", "B2B", "B3A", "B3B", "DEC"]:
    for p in json.load(open(os.path.join(WORK, "authors", a, "PRIVATE.json"), encoding="utf-8")):
        notes[p["local_id"]] = p
CASES = os.path.join(WORK, "cases")
assert not os.path.exists(CASES)
for b in shuf:
    i = b["id"]; m = idmap[i]; p = dict(notes[m["designer_id"]])
    d = os.path.join(CASES, i); os.makedirs(d)
    json.dump({"id": i, "claim": b["claim"], "data_keys": b["data_keys"], "sizes": b["sizes"]},
              open(os.path.join(d, "brief.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    priv = {"id": i}
    for k, v in p.items():
        if k == "local_id":
            continue
        if k in ("mechanism_tag", "subtype"):
            continue
        priv[k] = v
    priv["subtype_or_tag"] = p["mechanism_tag"]
    priv["class"] = m["class"]
    priv["approved_value"] = None  # set from part A0
    json.dump(priv, open(os.path.join(d, "PRIVATE.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# SOURCES_D rows by key (for PASSAGE.md)
rows = {}
for l in open(os.path.join(PD, "SOURCES_D.md"), encoding="utf-8").read().split("\n"):
    if l.startswith("| ") and not l.startswith("| Key"):
        rows[l.split("|")[1].strip().split(" ")[0]] = l
A0 = os.path.join(WORK, "audit_a0")
assert not os.path.exists(A0)
groups = {"B2": ["B-2"], "B3": ["B-3"], "DEC": ["B-1", "B-6"]}
manifest = {}
for g, classes in groups.items():
    d = os.path.join(A0, g); os.makedirs(os.path.join(d, "class"))
    for f in ("FIDELITY_AUDIT_D.md", "PREREG_PHASE_D.md", "P2_READING_D.md"):
        shutil.copy2(os.path.join(PD, f), os.path.join(d, f))
    shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(d, "agent_docs"))
    ids = sorted(i for i, m in idmap.items() if m["class"] in classes)
    keys = sorted({idmap[i]["source"] for i in ids})
    open(os.path.join(d, "SOURCES.md"), "w", encoding="utf-8", newline="\n").write(
        "# Sources (keys and references)\n\n" + "\n".join(f"- **{k}**: {rows[k].split('|')[2].strip()}" for k in keys) + "\n")
    open(os.path.join(d, "SOURCES_D.md"), "w", encoding="utf-8", newline="\n").write(
        "# Sources of this class (rows of SOURCES_D.md)\n\n" + "\n".join(rows[k] for k in keys) + "\n")
    for i in ids:
        cd = os.path.join(d, "class", i); os.makedirs(cd)
        shutil.copy2(os.path.join(CASES, i, "brief.json"), os.path.join(cd, "brief.json"))
        shutil.copy2(os.path.join(CASES, i, "PRIVATE.json"), os.path.join(cd, "PRIVATE.json"))
        p = json.load(open(os.path.join(CASES, i, "PRIVATE.json"), encoding="utf-8"))
        open(os.path.join(cd, "PASSAGE.md"), "w", encoding="utf-8", newline="\n").write(
            f"# Source passage for {i}\n\n**Source:** {p['source']}\n\n**Documenting passage (SOURCES_D.md):**\n\n{rows[p['source']]}\n\n"
            f"**Passage quoted in the private note:** {p.get('passage')}\n")
    for dp, _, fs in os.walk(d):
        for f in fs:
            q = os.path.join(dp, f); os.chmod(q, stat.S_IREAD)
            manifest[os.path.relpath(q, A0)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
    print(g, len(ids), "cases")
json.dump(manifest, open(os.path.join(WORK, "MANIFEST_a0.json"), "w"), indent=1, sort_keys=True)
