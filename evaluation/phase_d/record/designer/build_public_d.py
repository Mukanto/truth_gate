"""PREREG_PHASE_D section 3 item 13 (as PC section 5): assemble the public Phase D package in the repository, before the
case freeze. Copies only; nothing in the work folder changes. Refuses to run if PD/cases or PD/record exists.

PD = kapi-oss/evaluation/phase_d
  PD/cases/<id>/            all 72 case folders: brief.json, PRIVATE.json, CASE.md, faulty_body.py, fixed_body.py,
                            reference.py, MECH_CHECK.json, skeletons/W0.py and W1.py (the 20 selected)
  PD/cases/validity_log.jsonl   the validity/timing log (check_validity_log_d.py reads <cases>/validity_log.jsonl)
  PD/EXPECTED_FLAGS_D.json
  PD/record/                the pre-run record:
    work/                   the work folder's own files (RUN_LOG.md, WORLD_RUN.md, prompts, manifests, maps)
    record/                 phase_d_work/record without pkg/ and pkg_v050/ (copies of the tagged release; hashes in
                            SOFTWARE_STATE.json)
    validity/, shuffle/, world_checks/, designer/ (no __pycache__, no scratchpad archives)
    world_replay/<run>/replay_log.json
    sandboxes/<root>/...    for every agent sandbox root (authors, audit_a0, criterion, structure, audit_a, audit_b,
                            world, awareness): only the files the agent wrote or changed, i.e. files not in that root's
                            input manifest or whose SHA-256 differs from it
    TRANSCRIPTS.md          name, size and SHA-256 of every private transcript (contents are never published)
Then a scan of every copied text file for private data (prints hits; exit 1 if any)."""
import hashlib, json, os, re, shutil, sys
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
C, R = os.path.join(PD, "cases"), os.path.join(PD, "record")
assert not os.path.exists(C) and not os.path.exists(R), "PD/cases or PD/record exists"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
copied = []


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    copied.append(dst)


def cptree(src, dst, skip_dirs=()):
    for dp, dns, fs in os.walk(src):
        dns[:] = [d for d in dns if d not in skip_dirs and d != "__pycache__" and not d.startswith("scratchpad_archive")]
        for f in fs:
            cp(os.path.join(dp, f), os.path.join(dst, os.path.relpath(os.path.join(dp, f), src)))


# cases
for i in sorted(d for d in os.listdir(os.path.join(WORK, "cases")) if d.startswith("D-")):
    for dp, _, fs in os.walk(os.path.join(WORK, "cases", i)):
        for f in fs:
            s = os.path.join(dp, f)
            cp(s, os.path.join(C, os.path.relpath(s, os.path.join(WORK, "cases"))))
cp(os.path.join(WORK, "cases", "validity_log.jsonl"), os.path.join(C, "validity_log.jsonl"))
cp(os.path.join(WORK, "EXPECTED_FLAGS_D.json"), os.path.join(PD, "EXPECTED_FLAGS_D.json"))
# work-folder files
for f in sorted(os.listdir(WORK)):
    p = os.path.join(WORK, f)
    if os.path.isfile(p):
        cp(p, os.path.join(R, "work", f))
cptree(os.path.join(WORK, "record"), os.path.join(R, "record"), skip_dirs=("pkg", "pkg_v050"))
for d in ("validity", "shuffle", "world_checks", "designer"):
    cptree(os.path.join(WORK, d), os.path.join(R, d))
for run in sorted(os.listdir(os.path.join(WORK, "world_replay"))):
    p = os.path.join(WORK, "world_replay", run, "replay_log.json")
    if os.path.exists(p):
        cp(p, os.path.join(R, "world_replay", run, "replay_log.json"))
# agent outputs per sandbox root
roots = {"authors": ("authors", "MANIFEST_authors.json", ""), "audit_a0": ("audit_a0", "MANIFEST_a0.json", ""),
         "criterion": ("criterion", "MANIFEST_criterion.json", ""), "structure": ("structure", "MANIFEST_structure.json", ""),
         "audit_a": ("audit_a", "MANIFEST_audit_a.json", ""), "audit_b": ("audit_b", "MANIFEST_audit_b.json", ""),
         "world": ("world", "MANIFEST_world.json", ""), "awareness": ("awareness", "MANIFEST_awareness.json", "awareness")}
summary, fetched = {}, []
for name, (root, man, prefix) in roots.items():
    m = {k.replace("/", "\\"): v for k, v in json.load(open(os.path.join(WORK, man))).items()}
    base = os.path.join(WORK, root)
    n = 0
    for dp, dns, fs in os.walk(base):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for f in fs:
            s = os.path.join(dp, f)
            key = os.path.join(prefix, os.path.relpath(s, base)) if prefix else os.path.relpath(s, base)
            if m.get(key) != sha(s):
                if os.sep + "fetched" + os.sep in s:  # downloaded source documents: copyright, hashes only
                    fetched.append(f"| {os.path.relpath(s, WORK)} | {os.path.getsize(s)} | {sha(s)} |")
                    continue
                cp(s, os.path.join(R, "sandboxes", root, os.path.relpath(s, base)))
                n += 1
    summary[root] = n
open(os.path.join(R, "FETCHED_SOURCES.md"), "w", encoding="utf-8", newline="\n").write(
    "# Source documents downloaded by the brief authors (not published: copyright; hashes only)\n\n"
    "| file | bytes | sha256 |\n|---|---|---|\n" + "\n".join(fetched) + "\n")
copied.append(os.path.join(R, "FETCHED_SOURCES.md"))
# transcripts: hashes only
rows = ["# Private transcripts (contents not published)\n", "| file | bytes | sha256 |", "|---|---|---|"]
for f in sorted(os.listdir(os.path.join(WORK, "transcripts"))):
    p = os.path.join(WORK, "transcripts", f)
    rows.append(f"| {f} | {os.path.getsize(p)} | {sha(p)} |")
os.makedirs(R, exist_ok=True)
open(os.path.join(R, "TRANSCRIPTS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
copied.append(os.path.join(R, "TRANSCRIPTS.md"))
print("copied", len(copied), "files; agent outputs per root:", summary)
# private-data scan
pat = re.compile(open(r"E:\Claude Projects\Kapi\phase_d_private\private_patterns.txt", encoding="utf-8").read().strip(),
                 re.I)  # the pattern stays private: it names private data
hits = []
for p in copied:
    try:
        t = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    for mm in pat.finditer(t):
        ctx = t[max(0, mm.start() - 40):mm.end() + 40].replace("\n", " ")
        if "hazar.simsek.research@" in t[max(0, mm.start() - 30):mm.end() + 5]:  # the public research address
            continue
        hits.append((os.path.relpath(p, PD), ctx))
for h in hits[:50]:
    print("HIT", h)
print("private-data hits:", len(hits))
sys.exit(1 if hits else 0)
