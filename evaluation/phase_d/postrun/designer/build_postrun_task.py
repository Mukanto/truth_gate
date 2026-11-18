"""PREREG_PHASE_D section 7: build the post-run audit task folder for the independent session (designer).
E:\\Independent\\tasks\\phase_d_postrun\\ with copies only, every input read-only, empty out\\ and scratch\\; part2\\ holds
the draft report and the scoring output. Withheld: the designer's recomputation, the designer's run log and notes,
transcripts, earlier reviews. Manifest (SHA-256) in phase_d_private/MANIFEST_phase_d_postrun.json. Refuses if the
task folder exists."""
import hashlib, json, os, shutil, stat
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
REPO = r"E:\Claude Projects\kapi-oss"
T = r"E:\Independent\tasks\phase_d_postrun"
assert not os.path.exists(T), T
ids = json.load(open(os.path.join(WORK, "shuffle", "SUBSET_IDS.json")))
pairs = []


def cp(src, rel):
    pairs.append((src, rel))


cp(os.path.join(WORK, "POSTRUN_AUDIT_INSTRUCTIONS_D.md"), "POSTRUN_AUDIT_INSTRUCTIONS_D.md")
for f in ("PREREG_PHASE_D.md", "REVISIONS-post-freeze.md", "EXPECTED_FLAGS_D.json", "WORLD_INSTRUCTIONS_D0.md",
          "WORLD_INSTRUCTIONS_D1.md", "AWARENESS_RULE_D.md", "FIDELITY_AUDIT_D.md", "P2_READING_D.md", "SOURCES_D.md"):
    cp(os.path.join(PD, f), os.path.join("phase_d", f))
cp(os.path.join(REPO, "evaluation", "phase_b", "PREREG_PHASE_B.md"), os.path.join("phase_b", "PREREG_PHASE_B.md"))
cp(os.path.join(REPO, "evaluation", "phase_c", "PREREG_PHASE_C.md"), os.path.join("phase_c", "PREREG_PHASE_C.md"))
for i in ids:
    for f in ("brief.json", "PRIVATE.json", "CASE.md", "faulty_body.py", "fixed_body.py", "reference.py",
              os.path.join("skeletons", "W0.py"), os.path.join("skeletons", "W1.py")):
        cp(os.path.join(PD, "cases", i, f), os.path.join("phase_d", "cases", i, f))
run = os.path.join(WORK, "run")
cp(os.path.join(run, "RUNLOG.jsonl"), os.path.join("phase_d", "run", "RUNLOG.jsonl"))
for sub in ("certs", "studies"):
    for dp, _, fs in os.walk(os.path.join(run, sub)):
        for f in fs:
            s = os.path.join(dp, f)
            cp(s, os.path.join("phase_d", "run", os.path.relpath(s, run)))
for label, name in (("eb6876", "W0_batch1"), ("c13bd2", "W1_batch1"), ("5f14e6", "W0_batch2"), ("d5f53a", "W1_batch2")):
    for f in ("WORLD_LOG.md", "CHECKLIST_LOG.md"):
        s = os.path.join(WORK, "world", label, f)
        if os.path.exists(s):
            cp(s, os.path.join("phase_d", "record", "world", name, f))
cp(os.path.join(WORK, "WORLD_RUN.md"), os.path.join("phase_d", "record", "WORLD_RUN.md"))
for g in ("B2", "B3", "DEC"):
    cp(os.path.join(WORK, "audit_b", g, "AUDIT_B.json"), os.path.join("phase_d", "record", "audit_b", g, "AUDIT_B.json"))
cp(os.path.join(WORK, "AUDIT_B_MAP.json"), os.path.join("phase_d", "record", "audit_b", "AUDIT_B_MAP.json"))
for r in ("r1b", "r2", "r3", "r4"):
    cp(os.path.join(WORK, "awareness", r, "READING.json"), os.path.join("phase_d", "record", "awareness", r, "READING.json"))
for m in ("AWARENESS_MAP_first.json", "AWARENESS_MAP_second.json"):
    cp(os.path.join(WORK, m), os.path.join("phase_d", "record", "awareness", m))
for f in ("README_TOOL.md", "GATE.md", "SPEC.md"):
    cp(os.path.join(WORK, "record", "agent_docs", f), os.path.join("docs", f))
cp(os.path.join(PD, "REPORT.md"), os.path.join("part2", "REPORT.md"))
for f in ("RESULTS_D.md", "RESULTS_D.json"):
    cp(os.path.join(WORK, "score", f), os.path.join("part2", f))
man = {}
for s, rel in pairs:
    d = os.path.join(T, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copyfile(s, d)
    os.chmod(d, stat.S_IREAD)
    man[rel] = hashlib.sha256(open(d, "rb").read()).hexdigest()
os.makedirs(os.path.join(T, "out"))
os.makedirs(os.path.join(T, "scratch"))
json.dump(man, open(r"E:\Claude Projects\Kapi\phase_d_private\MANIFEST_phase_d_postrun.json", "w"), indent=1, sort_keys=True)
print(len(man), "files ->", T)
