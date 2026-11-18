p = r"C:\Users\user\.claude\projects\E--Claude-Projects\memory\kuanto-current-state.md"
s = open(p, encoding="utf-8").read()
anchor = "**RESUME HERE — 2026-11-18 (pre-compact). PHASE D EXECUTION in progress"
assert s.count(anchor) == 1
block = """**RESUME HERE — 2026-11-18 (later, ~05:30 UTC). PHASE D: items 4-5 DONE, item 6 validity mostly done, item 7 fidelity part A RUNNING. Read phase_d_work/RUN_LOG.md tail first. The block below (pre-compact) still holds the rules.**
- Items 4-5: all 10 authors valid (record/AUTHOR_RUN.md). Cases assembled (designer/assemble_cases.py). REVISIONS-post-freeze.md P-3 written (uncommitted): event 1 sizes-as-text adapter = validity/skelcheck/<id>/ (designer/skelcheck_folders.py), event 2 D-014+D-041 dropped (NaN briefs vs check, one return done), event 3 guard questions left to fidelity A item (d).
- Item 6: designer/run_validity.py (5 workers); 65 light runs done: 24 pass, 41 drop (V2 28, V1b 7, V1a 6), no repairs; validity/TABLE_DECISIONS.json via designer/apply_table.py. 5 slow B2B runs still running in background (D-058, D-018, D-065, D-059, D-013; hours; likely timing drops but wait for results). Log cases/validity_log.jsonl.
- Provisional selection (designer/selection.py): B-2 ~10, B-3 8, B-1 1, B-6 3 -> both classes < 16 = "insufficient cases" (section 6). Plan: finish items 7-8, then ASK THE AUTHOR before item 9 (Opus world authors) whether to continue, with facts and options.
- Item 7: audit_a/{B2,B3,DEC} (designer/build_audit_a.py), auditors general-purpose sonnet: B2 ad3c3617321082f3a, B3 a5efff89549f1383f, DEC ac17ad9d643bd1460. On completion: copy transcripts, author_run_check-style check (sandbox audit_a/<G>), apply section 2.4 rows for fidelity fails (repair once via the same author, request quotes only the failing item, no rates), then rerun validity on repaired pairs.
- designer/world_run_check.py DONE and tested (89 tests). Item 8: FREEZE_VALIDITY.json {"pairs":[{"id","result","repairs"}]} + extra keys for drops/selection; check with tools/check_validity_log_d.py --freeze ... --cases cases.
"""
s = s.replace(anchor, block + "\n" + anchor, 1)
open(p, "w", encoding="utf-8").write(s)
m = r"C:\Users\user\.claude\projects\E--Claude-Projects\memory\MEMORY.md"
t = open(m, encoding="utf-8").read()
old = "RESUME 2026-11-18 pre-compact: Truth_Gate Phase D execution, items 0-3 done, criterion+structure authors running; work folder Kapi/phase_d_work (RUN_LOG.md)"
assert old in t
t = t.replace(old, "RESUME 2026-11-18 later: Truth_Gate Phase D execution, items 0-5 done, validity and audit part A in progress; work folder Kapi/phase_d_work (RUN_LOG.md)")
open(m, "w", encoding="utf-8").write(t)
print("ok")
