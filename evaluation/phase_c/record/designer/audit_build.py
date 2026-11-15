"""Phase C fidelity-audit sandboxes (designer; PREREG_PHASE_C section 5, AUDIT_PHASE_C.md "What you may read").

audit/<F>/ gets read-only copies of PREREG_PHASE_C.md, PREREG_PHASE_B.md, P2_READING.md, AUDIT_PHASE_C.md (repo,
frozen), SOURCES.md (the stripped copy of the class folder), SOURCES_ADDENDUM.md, agent_docs/, MECH_CHECK.json
(designer/mech/MECH_CHECK_<F>.json) and class/ (cases/<id>/{ASSIGNMENT.json, CASE.md, skeleton.py, faulty.py, fixed.py},
PRIVATE.json, LOG.md, src/ if present); empty out/ (the audit folder) and scratch/. Refuses to overwrite.

Usage: py -I audit_build.py PHASE_C_PRIVATE REPO_PHASE_C_DIR FOLDER [FOLDER ...]
"""
import os, shutil, stat, sys

root, pc, folders = sys.argv[1], sys.argv[2], sys.argv[3:]
J = lambda *p: os.path.join(root, *p)


def ro_tree(path):
    for d, _, fs in os.walk(path):
        for f in fs:
            os.chmod(os.path.join(d, f), stat.S_IREAD)


for F in folders:
    A = J("audit", F)
    if os.path.exists(A):
        raise SystemExit(f"refusing to overwrite {A}")
    os.makedirs(os.path.join(A, "class", "cases"))
    for f in ("PREREG_PHASE_C.md", "P2_READING.md", "AUDIT_PHASE_C.md"):
        shutil.copyfile(os.path.join(pc, f), os.path.join(A, f))
    for f in ("PREREG_PHASE_B.md", "SOURCES.md", "SOURCES_ADDENDUM.md"):
        shutil.copyfile(J("authors", F, f), os.path.join(A, f))
    shutil.copytree(J("authors", F, "agent_docs"), os.path.join(A, "agent_docs"))
    shutil.copyfile(J("designer", "mech", f"MECH_CHECK_{F}.json"), os.path.join(A, "MECH_CHECK.json"))
    for f in ("PRIVATE.json", "LOG.md"):
        shutil.copyfile(J("authors", F, f), os.path.join(A, "class", f))
    if os.path.isdir(J("authors", F, "src")):
        shutil.copytree(J("authors", F, "src"), os.path.join(A, "class", "src"))
    for case in sorted(os.listdir(J("authors", F, "cases"))):
        src = J("authors", F, "cases", case)
        dst = os.path.join(A, "class", "cases", case)
        os.makedirs(dst)
        for f in ("ASSIGNMENT.json", "CASE.md", "skeleton.py", "faulty.py", "fixed.py"):
            shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
    ro_tree(A)
    os.makedirs(os.path.join(A, "out"))
    os.makedirs(os.path.join(A, "scratch"))
    n = len(os.listdir(os.path.join(A, "class", "cases")))
    print(F, n, "cases ->", A)
