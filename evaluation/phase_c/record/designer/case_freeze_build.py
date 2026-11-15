"""Phase C case freeze, step 1 (designer; PREREG_PHASE_C section 5, as Phase B step 6; REVISIONS-post-freeze P-6).

Mode `cases`: copies the 52 audited pairs (designer/DESIGNER_LINES.json keys) from authors/<F>/cases/<id>/ into
REPO/evaluation/phase_c/cases/<id>/ (faulty.py, fixed.py, CASE.md, ASSIGNMENT.json) and writes
REPO/evaluation/phase_c/EXPECTED_FLAGS.json (PB section 6 list + HIGH_RATE:control:<id> and HIGH_RATE:probe:shuffle:<a>,<b>
from each case's STUDY, built with the sandbox package pkg/ = truth_gate 0.5.0; no criterion is called).
Mode `record`: copies the pre-run record into REPO/evaluation/phase_c/record/ as a selective mirror of the private
workspace (same relative paths), WITHOUT agent transcripts (*.jsonl, *.meta.json, *.prefix.json), source texts and
extracts (src/, scratchpad archive), package copies (pkg/, pkg_v041/, agent_docs_raw/) and sandbox copies. Prints every
included file count and every excluded path class. Refuses to overwrite. The freeze itself is done separately with
protocol/tools/freeze.py.

Usage: py -I case_freeze_build.py cases|record
"""
import hashlib, json, os, shutil, sys

PRIV = r"E:\Claude Projects\Kapi\phase_c_private"
REPO = r"E:\Claude Projects\kapi-oss\evaluation\phase_c"
J = lambda *p: os.path.join(PRIV, *p)
BASE = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
        "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "HIGH_RATE:probe:noise", "HIGH_RATE:world:null"]
IN_SCOPE = {"B-1", "B-2", "B-3", "B-6"}
TRANSCRIPT_SUFFIXES = (".jsonl", ".meta.json", ".prefix.json")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def folder(lid):
    return "O" if lid.startswith("O") else lid[:2]


def do_cases():
    out = os.path.join(REPO, "cases")
    if os.path.exists(out) or os.path.exists(os.path.join(REPO, "EXPECTED_FLAGS.json")):
        raise SystemExit("cases/ or EXPECTED_FLAGS.json exists; refusing")
    sys.path.insert(0, J("pkg"))
    sys.dont_write_bytecode = True
    import importlib.util
    import truth_gate
    assert os.path.realpath(truth_gate.__file__).startswith(os.path.realpath(J("pkg"))), truth_gate.__file__
    keep = json.load(open(J("designer", "DESIGNER_LINES.json"), encoding="utf-8"))
    flags = {"note": ("PREREG_PHASE_C.md §6: expected flags per case, as PB §6. In-scope classes (B-1, B-2, B-3, B-6) "
                      "share one list; HIGH_RATE:control:<id> is enumerated from each case's declared controls and "
                      "HIGH_RATE:probe:shuffle:<a>,<b> from its declared relational pairs, at the freeze. Information "
                      "flags (K1_ABSTAINED:*, K2_MINUS_UNREAD, K8_SOME_CHANGES, BAD_RETURN) and the capping flag "
                      "K1_ABSTAINED_MAJORITY:* never count. The out-of-scope cases (O-1..O-3) carry the same list for "
                      "description only."),
             "base": BASE, "cases": {}}
    for lid in sorted(keep):
        src = J("authors", folder(lid), "cases", lid)
        dst = os.path.join(out, lid)
        os.makedirs(dst)
        for fn in ("faulty.py", "fixed.py", "CASE.md", "ASSIGNMENT.json"):
            shutil.copyfile(os.path.join(src, fn), os.path.join(dst, fn))
            assert sha(os.path.join(src, fn)) == sha(os.path.join(dst, fn))
        a = json.load(open(os.path.join(src, "ASSIGNMENT.json"), encoding="utf-8"))
        spec = importlib.util.spec_from_file_location("c_" + lid.replace("-", "_"), os.path.join(dst, "fixed.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        st = mod.STUDY
        exp = list(BASE) + [f"HIGH_RATE:control:{c.id}" for c in st.controls] + \
              [f"HIGH_RATE:probe:shuffle:{x},{y}" for x, y in st.relational]
        flags["cases"][lid] = {"case_id": lid, "world_id": a["world_id"], "class": a["class"], "subtype": a["subtype"],
                               "source": a["source"], "in_scope": a["class"] in IN_SCOPE, "expected": exp}
    json.dump(flags, open(os.path.join(REPO, "EXPECTED_FLAGS.json"), "w", encoding="utf-8", newline="\n"), indent=2)
    print("cases:", len(flags["cases"]), "->", out)


TOP_FILES = ["FREEZE_AGENT_DOCS.json", "FREEZE_SKELETONS.json", "READER1.json", "SCAN_REMOVALS.md", "SCAN_REPORT.json",
             "SOFTWARE_STATE.json", "SOURCES_STRIPPED.md", "build_agent_docs.py", "scan_initial.json", "scan_initial.txt",
             "scan_after_removal.json", "scan_final_unlisted.json", "scan_initial.err", "scan2.err", "scan3.err"]
TREES = ["agent_docs", "smoke", "world", "designer", "fable", "authors", "audit", "awareness_reader2", "sandbox_scan_reader"]


def include(rel):
    """Decide for a file path relative to the private workspace (forward slashes)."""
    parts = rel.split("/")
    if rel.endswith(TRANSCRIPT_SUFFIXES):
        return False, "agent transcript"
    if parts[0] == "designer" and len(parts) > 1 and parts[1] in ("scratchpad_archive_2026-11-15", "skeletons_all"):
        return False, "scratchpad archive / duplicate skeletons"
    if parts[0] == "authors":
        if len(parts) == 3 and parts[2] in ("BRIEFS.json", "PRIVATE.json", "LOG.md"):
            return True, ""
        if len(parts) > 3 and parts[2] == "work":
            return True, ""
        return False, "author sandbox copies, cases (published in cases/), source extracts"
    if parts[0] == "fable":
        if len(parts) == 2 and parts[1] != "":
            return True, ""                                   # WORLD_RUN.md, batch check reports
        if len(parts) == 3 and parts[2] == "WORLD_LOG.md":
            return True, ""
        if len(parts) == 4 and parts[2] == "skeletons":
            return True, ""
        if parts[1] == "transcripts" and rel.endswith(".py"):
            return True, ""                                   # the batches' own scratchpad scripts (P-2)
        return False, "world-author sandbox copies"
    if parts[0] == "audit":
        if len(parts) >= 3 and parts[2] in ("out", "scratch"):
            return True, ""
        if len(parts) == 3 and parts[2] == "MECH_CHECK.json":
            return True, ""
        return False, "auditor sandbox copies"
    if parts[0] == "awareness_reader2":
        return (parts[1] == "READING2.json"), "reader sandbox copies"
    if parts[0] == "sandbox_scan_reader":
        return (len(parts) == 2), "reader sandbox copies"
    return True, ""


def do_record():
    out = os.path.join(REPO, "record")
    if os.path.exists(out):
        raise SystemExit(f"{out} exists; refusing")
    copied, excluded = [], {}
    for fn in TOP_FILES:
        shutil.copyfile(J(fn), os.path.join(os.makedirs(out, exist_ok=True) or out, fn)); copied.append(fn)
    for top in TREES:
        for root, dirs, files in os.walk(J(top)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), PRIV).replace("\\", "/")
                ok, why = include(rel)
                if not ok:
                    excluded.setdefault(why, []).append(rel); continue
                d = os.path.join(out, *rel.split("/"))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copyfile(os.path.join(root, fn), d)
                assert sha(os.path.join(root, fn)) == sha(d)
                copied.append(rel)
    print("record files:", len(copied))
    for why, rels in sorted(excluded.items()):
        print(f"excluded ({why}): {len(rels)}")
    json.dump({"included": sorted(copied), "excluded": {k: sorted(v) for k, v in excluded.items()}},
              open(J("designer", "RECORD_MANIFEST.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    {"cases": do_cases, "record": do_record}[sys.argv[1]]()
