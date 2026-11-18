"""PREREG_PHASE_D section 3 item 4: criterion-author sandboxes, one per class half and one for the decoys (designer).

Each sandbox: CRITERION_AUTHOR_D.md; the half's folder (BRIEFS.json, PRIVATE.json, LOG.md and source extracts from the
brief author; cases/<id>/brief.json; CASE_IDS.json mapping local_id -> neutral id); SOURCES.md, SOURCES_D.md (the brief
author's copies); agent_docs/ and pkg/ (frozen, v0.5.1). Inputs read-only; the half folder stays writable for the case
files, LOG.md (copied writable so the author can append) and work/. Manifest MANIFEST_criterion.json.
"""
import hashlib, json, os, shutil, stat
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
OUT = os.path.join(WORK, "criterion")
assert not os.path.exists(OUT)
idmap = json.load(open(os.path.join(WORK, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))
manifest = {}
for a in ["B2A", "B2B", "B3A", "B3B", "DEC"]:
    sb = os.path.join(OUT, a)
    half = os.path.join(sb, "half")
    os.makedirs(half)
    src = os.path.join(WORK, "authors", a)
    for f in ("BRIEFS.json", "PRIVATE.json", "LOG.md"):
        shutil.copy2(os.path.join(src, f), os.path.join(half, f))
    if os.path.isdir(os.path.join(src, "fetched")):
        shutil.copytree(os.path.join(src, "fetched"), os.path.join(half, "fetched"))
    ids = {m["designer_id"]: m["id"] for m in idmap if m["designer_id"].startswith(a + "-")}
    json.dump(ids, open(os.path.join(half, "CASE_IDS.json"), "w", encoding="utf-8"), indent=1)
    for local, nid in ids.items():
        os.makedirs(os.path.join(half, "cases", nid))
        shutil.copy2(os.path.join(WORK, "cases", nid, "brief.json"), os.path.join(half, "cases", nid, "brief.json"))
    shutil.copy2(os.path.join(PD, "CRITERION_AUTHOR_D.md"), os.path.join(sb, "CRITERION_AUTHOR_D.md"))
    for f in ("SOURCES.md", "SOURCES_D.md"):
        shutil.copy2(os.path.join(src, f), os.path.join(sb, f))
    shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(sb, "agent_docs"))
    shutil.copytree(os.path.join(WORK, "record", "pkg"), os.path.join(sb, "pkg"))
    for dp, _, fs in os.walk(sb):
        for f in fs:
            q = os.path.join(dp, f)
            manifest[os.path.relpath(q, OUT)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
            if os.path.basename(q) != "LOG.md":
                os.chmod(q, stat.S_IREAD)
            else:
                os.chmod(q, stat.S_IREAD | stat.S_IWRITE)
    print(a, len(ids), "cases")
json.dump(manifest, open(os.path.join(WORK, "MANIFEST_criterion.json"), "w"), indent=1, sort_keys=True)
