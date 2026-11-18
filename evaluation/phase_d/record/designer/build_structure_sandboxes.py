"""PREREG_PHASE_D section 3 item 5 / section 2.2: structure-author sandboxes, one per class half and one for the decoys.

Each sandbox: STRUCTURE_AUTHOR_D.md; cases/<id>/brief.json and cases/<id>/NOTE.json holding only the note fields the
instruction lists (source, passage, estimand, exploited_structure, structure_statistic, sizes_note, approved_value);
SOURCES_D.md (the half's rows, from the brief author's sandbox); agent_docs/ and pkg/ (frozen, v0.5.1). Inputs read-only;
the author writes cases/<id>/reference.py and STRUCTURE_LOG.md. Manifest MANIFEST_structure.json.
"""
import hashlib, json, os, shutil, stat
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
OUT = os.path.join(WORK, "structure")
assert not os.path.exists(OUT)
FIELDS = ("source", "passage", "estimand", "exploited_structure", "structure_statistic", "sizes_note", "approved_value")
idmap = json.load(open(os.path.join(WORK, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))
manifest = {}
for a in ["B2A", "B2B", "B3A", "B3B", "DEC"]:
    sb = os.path.join(OUT, a)
    os.makedirs(sb)
    shutil.copy2(os.path.join(PD, "STRUCTURE_AUTHOR_D.md"), os.path.join(sb, "STRUCTURE_AUTHOR_D.md"))
    shutil.copy2(os.path.join(WORK, "authors", a, "SOURCES_D.md"), os.path.join(sb, "SOURCES_D.md"))
    shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(sb, "agent_docs"))
    shutil.copytree(os.path.join(WORK, "record", "pkg"), os.path.join(sb, "pkg"))
    ids = sorted(m["id"] for m in idmap if m["designer_id"].startswith(a + "-"))
    for i in ids:
        cd = os.path.join(sb, "cases", i)
        os.makedirs(cd)
        shutil.copy2(os.path.join(WORK, "cases", i, "brief.json"), os.path.join(cd, "brief.json"))
        p = json.load(open(os.path.join(WORK, "cases", i, "PRIVATE.json"), encoding="utf-8"))
        json.dump({"id": i, **{k: p.get(k) for k in FIELDS}}, open(os.path.join(cd, "NOTE.json"), "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
    for dp, _, fs in os.walk(sb):
        for f in fs:
            q = os.path.join(dp, f)
            manifest[os.path.relpath(q, OUT)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
            os.chmod(q, stat.S_IREAD)
    print(a, len(ids), "cases")
json.dump(manifest, open(os.path.join(WORK, "MANIFEST_structure.json"), "w"), indent=1, sort_keys=True)
