"""PREREG_PHASE_D section 3 item 7: fidelity audit part A sandboxes, one per class group (B2, B3, DEC), designer.

Only pairs that passed validity (validity/TABLE_DECISIONS.json decision "pass") enter. No validity result, log or
RESULT.json is copied. audit_a/<G>/: FIDELITY_AUDIT_D.md, PREREG_PHASE_D.md, P2_READING_D.md, SOURCES.md, SOURCES_D.md
(rows of the class's sources), agent_docs/; class/cases/<id>/: brief.json, PRIVATE.json, PASSAGE.md, CASE.md,
faulty_body.py, fixed_body.py, reference.py, MECH_CHECK.json, STRUCTURE_LOG.md (the structure author's log of that
half, whole); class/logs/<half>/: LOG.md (brief author's log with the criterion author's section, as written in the
criterion sandbox), BRIEF_LOG.md (the brief author's final log, with any A0 revision), extracts/ (source extracts of
the brief author, if any). Inputs read-only. Manifest MANIFEST_audit_a.json (updated when cases are added).
Usage: build_audit_a.py [ID ...]  (default: every passed pair; an existing case folder is never overwritten)."""
import hashlib, json, os, shutil, stat, sys
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
dec = json.load(open(os.path.join(WORK, "validity", "TABLE_DECISIONS.json"), encoding="utf-8"))
idmap = {m["id"]: m for m in json.load(open(os.path.join(WORK, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))}
ids = sys.argv[1:] or sorted(i for i, d in dec.items() if d["decision"] == "pass")
assert all(dec.get(i, {}).get("decision") == "pass" for i in ids), "only passed pairs enter part A"
group = lambda m: {"B-2": "B2", "B-3": "B3"}.get(m["class"], "DEC")
rows = {}
for l in open(os.path.join(PD, "SOURCES_D.md"), encoding="utf-8").read().split("\n"):
    if l.startswith("| ") and not l.startswith("| Key"):
        rows[l.split("|")[1].strip().split(" ")[0]] = l
A = os.path.join(WORK, "audit_a")
mp = os.path.join(WORK, "MANIFEST_audit_a.json")
manifest = json.load(open(mp)) if os.path.exists(mp) else {}
for g in ("B2", "B3", "DEC"):
    gids = [i for i in ids if group(idmap[i]) == g]
    if not gids:
        continue
    d = os.path.join(A, g)
    if not os.path.exists(d):
        os.makedirs(os.path.join(d, "class", "cases"))
        for f in ("FIDELITY_AUDIT_D.md", "PREREG_PHASE_D.md", "P2_READING_D.md"):
            shutil.copy2(os.path.join(PD, f), os.path.join(d, f))
        shutil.copytree(os.path.join(WORK, "record", "agent_docs"), os.path.join(d, "agent_docs"))
        keys = sorted({m["source"] for m in idmap.values() if group(m) == g})
        open(os.path.join(d, "SOURCES.md"), "w", encoding="utf-8", newline="\n").write(
            "# Sources (keys and references)\n\n" + "\n".join(f"- **{k}**: {rows[k].split('|')[2].strip()}" for k in keys) + "\n")
        open(os.path.join(d, "SOURCES_D.md"), "w", encoding="utf-8", newline="\n").write(
            "# Sources of this class (rows of SOURCES_D.md)\n\n" + "\n".join(rows[k] for k in keys) + "\n")
    for i in gids:
        m = idmap[i]; half = m["designer_id"].split("-")[0]
        cd = os.path.join(d, "class", "cases", i)
        assert not os.path.exists(cd), f"{cd} exists"
        os.makedirs(cd)
        for f in ("brief.json", "PRIVATE.json", "CASE.md", "faulty_body.py", "fixed_body.py", "reference.py", "MECH_CHECK.json"):
            shutil.copy2(os.path.join(WORK, "cases", i, f), os.path.join(cd, f))
        shutil.copy2(os.path.join(WORK, "structure", half, "STRUCTURE_LOG.md"), os.path.join(cd, "STRUCTURE_LOG.md"))
        p = json.load(open(os.path.join(WORK, "cases", i, "PRIVATE.json"), encoding="utf-8"))
        open(os.path.join(cd, "PASSAGE.md"), "w", encoding="utf-8", newline="\n").write(
            f"# Source passage for {i}\n\n**Source:** {p['source']}\n\n**Documenting passage (SOURCES_D.md):**\n\n{rows[p['source']]}\n\n"
            f"**Passage quoted in the private note:** {p.get('passage')}\n")
        ld = os.path.join(d, "class", "logs", half)
        if not os.path.exists(ld):
            os.makedirs(ld)
            shutil.copy2(os.path.join(WORK, "criterion", half, "half", "LOG.md"), os.path.join(ld, "LOG.md"))
            shutil.copy2(os.path.join(WORK, "authors", half, "LOG.md"), os.path.join(ld, "BRIEF_LOG.md"))
            if os.path.isdir(os.path.join(WORK, "authors", half, "fetched")):
                shutil.copytree(os.path.join(WORK, "authors", half, "fetched"), os.path.join(ld, "extracts"))
    for dp, _, fs in os.walk(d):
        for f in fs:
            q = os.path.join(dp, f)
            rel = os.path.relpath(q, A)
            if rel not in manifest:
                os.chmod(q, stat.S_IREAD)
                manifest[rel] = hashlib.sha256(open(q, "rb").read()).hexdigest()
    print(g, len(gids), "cases:", " ".join(gids))
json.dump(manifest, open(mp, "w"), indent=1, sort_keys=True)
