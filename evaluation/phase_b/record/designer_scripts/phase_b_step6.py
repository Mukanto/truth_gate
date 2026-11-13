"""Phase B step 6 (designer): move the audited cases into the repository, write EXPECTED_FLAGS.json, then (separately,
with protocol/tools/freeze.py) freeze them. Also copies the pre-run record (private notes, world, audits) into
evaluation/phase_b/record/ WITHOUT source texts (src/, pdf, html, xml, source-extract txt files).
Usage: py phase_b_step6.py cases | record
"""
import hashlib, json, os, shutil, sys

PB = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b"
SCR = os.path.dirname(PB)
REPO = r"E:\Claude Projects\kapi-oss\evaluation\phase_b"
idmap = json.load(open(os.path.join(PB, "ID_MAP_AND_CLASSES.json"), encoding="utf-8"))
BASE = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
        "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "HIGH_RATE:probe:noise", "HIGH_RATE:world:null"]
IN_SCOPE = {"B-1", "B-2", "B-3", "B-6"}


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def case_id(local_id):
    return local_id.upper() if local_id.lower().startswith("b2-") else local_id


def do_cases():
    sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
    import importlib.util
    sys.dont_write_bytecode = True
    out = os.path.join(REPO, "cases")
    if os.path.exists(out):
        raise SystemExit(f"{out} exists; refusing")
    flags = {"note": ("PREREG_PHASE_B.md §6: expected flags per case. In-scope classes (B-1, B-2, B-3, B-6) share one list "
                      "by design; HIGH_RATE:control:<id> is enumerated from each case's declared controls and "
                      "HIGH_RATE:probe:shuffle:<a>,<b> from its declared relational pairs (none were declared). The "
                      "out-of-scope cases (O-1..O-3) carry the same list for descriptive reporting only: no threshold."),
             "base": BASE, "cases": {}}
    for a in sorted(idmap, key=lambda z: (z["author_folder"], z["local_id"])):
        src = os.path.join(PB, a["author_folder"], "cases", a["local_id"])
        cid = case_id(a["local_id"])
        dst = os.path.join(out, cid)
        os.makedirs(dst)
        for fn in ("faulty.py", "fixed.py", "CASE.md", "ASSIGNMENT.json"):
            shutil.copyfile(os.path.join(src, fn), os.path.join(dst, fn))
            assert sha(os.path.join(src, fn)) == sha(os.path.join(dst, fn))
        spec = importlib.util.spec_from_file_location(f"c_{cid}".replace("-", "_"), os.path.join(dst, "fixed.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        st = mod.STUDY
        exp = list(BASE) + [f"HIGH_RATE:control:{c.id}" for c in st.controls] + \
              [f"HIGH_RATE:probe:shuffle:{x},{y}" for x, y in st.relational]
        flags["cases"][cid] = {"local_id": a["local_id"], "world_id": a["world_id"], "class": a["class"],
                               "subtype": a["subtype"], "source": a["source"], "in_scope": a["class"] in IN_SCOPE,
                               "expected": exp}
    json.dump(flags, open(os.path.join(REPO, "EXPECTED_FLAGS.json"), "w", encoding="utf-8", newline="\n"), indent=2)
    print("cases:", len(flags["cases"]), "->", out)


SKIP_DIRS = {"src", "__pycache__", "cases"}
SKIP_EXT = {".pdf", ".html", ".xml"}
SKIP_FILES = {"BAR05_openalex_text.txt", "SIM03_openalex_abstract.txt", "kri.txt", "mak.txt", "vul.txt", "pea.txt",
              "hur.txt", "laz.txt", "nie.txt", "nie2.txt"}


def do_record():
    out = os.path.join(REPO, "record")
    if os.path.exists(out):
        raise SystemExit(f"{out} exists; refusing")
    copied, skipped = [], []
    for top in ("B1", "B2", "B3", "B6", "O", "world", "audit"):
        for root, dirs, files in os.walk(os.path.join(PB, top)):
            rel_root = os.path.relpath(root, PB)
            keep_dirs = []
            for dname in dirs:
                # the class folders' cases/ are published in evaluation/phase_b/cases; skeleton copies are in world/
                if dname in SKIP_DIRS and not (top == "world" and dname == "skeletons"):
                    skipped.append(os.path.join(rel_root, dname) + os.sep)
                else:
                    keep_dirs.append(dname)
            dirs[:] = keep_dirs
            for fn in files:
                if fn in SKIP_FILES or os.path.splitext(fn)[1].lower() in SKIP_EXT:
                    skipped.append(os.path.join(rel_root, fn)); continue
                s = os.path.join(root, fn)
                d = os.path.join(out, rel_root, fn)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copyfile(s, d)
                copied.append(os.path.join(rel_root, fn))
    for fn in ("ID_MAP_AND_CLASSES.json", "AUTHOR_PHASE1.md", "AUTHOR_PHASE2.md", "AUDIT_PHASE.md",
               "FREEZE_SKELETONS.json", "STEP3_SKELETON_CHECK.json", "STEP5_MECH_CHECK.json"):
        shutil.copyfile(os.path.join(PB, fn), os.path.join(out, fn)); copied.append(fn)
    os.makedirs(os.path.join(out, "designer_scripts"), exist_ok=True)
    for fn in ("phase_b_step1.py", "phase_b_step3.py", "phase_b_step4.py", "phase_b_step5_mech.py", "phase_b_step6.py"):
        shutil.copyfile(os.path.join(SCR, fn), os.path.join(out, "designer_scripts", fn)); copied.append("designer_scripts/" + fn)
    print("record files:", len(copied))
    print("skipped (source texts, case copies, caches):", len(skipped))
    for s in skipped:
        print("  -", s)


if __name__ == "__main__":
    {"cases": do_cases, "record": do_record}[sys.argv[1]]()
