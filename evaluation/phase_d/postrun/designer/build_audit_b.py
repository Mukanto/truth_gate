"""PREREG_PHASE_D section 3 item 11: fidelity audit part B sandboxes, one per class group (B2, B3, DEC), designer.

Only the selected pairs and decoys (validity/SELECTION.json) enter; each must have both skeletons in cases/<id>/skeletons/
(W0.py, W1.py; collected from valid batches). audit_b/<G>/: FIDELITY_AUDIT_D.md, PREREG_PHASE_D.md, P2_READING_D.md,
SOURCES.md, SOURCES_D.md, agent_docs/ (copied from the part-A sandbox audit_a/<G>/, which holds the same frozen files);
class/cases/<id>/: the part-A case files (brief.json, PRIVATE.json, PASSAGE.md, CASE.md, faulty_body.py, fixed_body.py,
reference.py, MECH_CHECK.json, STRUCTURE_LOG.md, copied from audit_a/<G>/class/cases/<id>/) and the two skeletons under
random labels X.py and Y.py; class/logs/: as in part A. No part-A audit output, no world log, no checklist log, no
validity or timing result. Inputs read-only. The label map (id -> {"X": arm, "Y": arm}) is AUDIT_B_MAP.json in the work
folder, outside audit_b/. Manifest MANIFEST_audit_b.json. Refuses to run if audit_b/ exists."""
import hashlib, json, os, secrets, shutil, stat
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
A, B = os.path.join(WORK, "audit_a"), os.path.join(WORK, "audit_b")
assert not os.path.exists(B), "audit_b/ exists"
sel = json.load(open(os.path.join(WORK, "validity", "SELECTION.json"), encoding="utf-8"))
groups = {"B2": [x[0] for x in sel["B-2"]["selected"]], "B3": [x[0] for x in sel["B-3"]["selected"]],
          "DEC": [x[0] for x in sel["B-1"]["selected"]] + [x[0] for x in sel["B-6"]["selected"]]}
for g, ids in groups.items():
    for i in ids:
        for arm in ("W0", "W1"):
            assert os.path.exists(os.path.join(WORK, "cases", i, "skeletons", arm + ".py")), f"{i} {arm} missing"
        assert os.path.isdir(os.path.join(A, g, "class", "cases", i)), f"{i} not in audit_a/{g}"
amap, manifest = {}, {}
for g, ids in groups.items():
    d = os.path.join(B, g)
    os.makedirs(os.path.join(d, "class", "cases"))
    for f in ("FIDELITY_AUDIT_D.md", "PREREG_PHASE_D.md", "P2_READING_D.md", "SOURCES.md", "SOURCES_D.md"):
        shutil.copy2(os.path.join(A, g, f), os.path.join(d, f))
    shutil.copytree(os.path.join(A, g, "agent_docs"), os.path.join(d, "agent_docs"))
    shutil.copytree(os.path.join(A, g, "class", "logs"), os.path.join(d, "class", "logs"))
    for i in sorted(ids):
        cd = os.path.join(d, "class", "cases", i)
        shutil.copytree(os.path.join(A, g, "class", "cases", i), cd)
        arms = ["W0", "W1"]
        if secrets.randbelow(2):
            arms.reverse()
        amap[i] = {"X": arms[0], "Y": arms[1]}
        for lab, arm in amap[i].items():
            shutil.copyfile(os.path.join(WORK, "cases", i, "skeletons", arm + ".py"), os.path.join(cd, lab + ".py"))
    for dp, _, fs in os.walk(d):
        for f in fs:
            q = os.path.join(dp, f)
            os.chmod(q, stat.S_IREAD)
            manifest[os.path.relpath(q, B)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
    print(g, len(ids), "cases:", " ".join(sorted(ids)))
json.dump(amap, open(os.path.join(WORK, "AUDIT_B_MAP.json"), "w"), indent=1, sort_keys=True)
json.dump(manifest, open(os.path.join(WORK, "MANIFEST_audit_b.json"), "w"), indent=1, sort_keys=True)
