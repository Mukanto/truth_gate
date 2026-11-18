"""After the run: copy the run, scoring, recomputation and post-run audit files into kapi-oss/evaluation/phase_d (new
folders only; the frozen cases/ and record/ are not touched). Refuses to overwrite. Private-data scan as
build_public_d.py (pattern kept outside the repository).
  PD/run/        RUNLOG.jsonl, STUDIES.json, certs/, logs/, studies/ (run_phase_d.py output)
  PD/score/      RESULTS_D.json/.md, OVERLAP_D.json, RESULTS_D_WITHOUT_OVERLAP.json/.md, tools/ (frozen tool outputs)
  PD/recompute/  recompute_designer_d.py, compare_designer_d.py, RECOMPUTE_D.*, COMPARE_D.*
  PD/postrun/    POSTRUN_AUDIT_INSTRUCTIONS_D.md, POSTRUN_AUDIT.json/.md, POSTRUN_AUDIT_PART2.md
  PD/postrun/designer/  the designer files written or changed after the case freeze (RUN_LOG.md as of now, scripts)"""
import os, re, shutil, sys
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
copied = []


def cp(src, dst):
    assert not os.path.exists(dst), dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    copied.append(dst)


def tree(src, dst):
    for dp, dns, fs in os.walk(src):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for f in fs:
            if f.endswith(".lock"):
                continue
            cp(os.path.join(dp, f), os.path.join(dst, os.path.relpath(os.path.join(dp, f), src)))


tree(os.path.join(WORK, "run"), os.path.join(PD, "run"))
tree(os.path.join(WORK, "score"), os.path.join(PD, "score"))
tree(os.path.join(WORK, "recompute"), os.path.join(PD, "recompute"))
tree(os.path.join(WORK, "postrun"), os.path.join(PD, "postrun"))
for f in ("RUN_LOG.md", "run_stdout.log", "score_stdout.log"):
    cp(os.path.join(WORK, f), os.path.join(PD, "postrun", "designer", f))
for f in ("overlap_d.py", "build_postrun_task.py", "build_public_postrun_d.py", "build_awareness.py",
          "build_public_d.py", "collect_skeletons.py", "run_timing_arms.py", "build_timing_arms.py", "build_audit_b.py"):
    cp(os.path.join(WORK, "designer", f), os.path.join(PD, "postrun", "designer", f))
pat = re.compile(open(r"E:\Claude Projects\Kapi\phase_d_private\private_patterns.txt", encoding="utf-8").read().strip(), re.I)
hits = []
for p in copied + [os.path.join(PD, "REPORT.md"), os.path.join(PD, "REVISIONS-post-freeze.md"),
                   os.path.join(PD, "run_phase_d.py"), os.path.join(PD, "score_phase_d.py")]:
    try:
        t = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    for m in pat.finditer(t):
        if "hazar.simsek.research@" in t[max(0, m.start() - 30):m.end() + 5]:
            continue
        hits.append((os.path.relpath(p, PD), t[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")))
print("copied", len(copied), "files; private-data hits:", len(hits))
for h in hits[:20]:
    print("HIT", h)
sys.exit(1 if hits else 0)
