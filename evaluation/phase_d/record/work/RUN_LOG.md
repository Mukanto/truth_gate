# Phase D execution log (designer, private)

## 2026-11-17
- Item 0 (start conditions):
  - agent_docs built from v0.5.1 (`record/build_agent_docs_d.py`).
  - Scan: 62 hits. Two-reader triage: designer READER1, fresh kodlayici reader 2 (agent ac853424fe580d4a3). 6 sentences removed, 59 lines listed; final scan exit 0.
  - pkg/ is v0.5.1 and pkg_v050/ is v0.5.0. The smoke test gives FALSIFIABLE with both.
  - The Fable pre-flight failed (agent aa92c2228cc59608d): "Fable 5.2 requires usage credits".
  - Author's decision: Opus 5.5. Recorded as REVISIONS-post-freeze.md P-1, in the repo, uncommitted.
  - The Opus pre-flight passed (agent a7db422431a547b92): 3 of 3 assistant messages are claude-opus-5-5.
  - Frozen in `record/FREEZE_AGENT_DOCS.json` (92 files, core 8e94dd364741b98b).
- P-1 review sent to the Independent session (task phase_d_p1_review). It must finish before any skeleton exists.
- Item 2 (brief authors): five sandboxes in `authors/` (`build_author_sandboxes.py`; MANIFEST_authors.json, 45 inputs).
  - The prompt is `BRIEF_AUTHOR_PROMPT.md`. It adds the ctx_* ban and a curl fallback when WebFetch is redirected.
  - Agents (kodlayici, Sonnet 5.5): B2A a4a4a89eebcfe6026, B2B af560fa650007dcf8, B3A a66194589676ba09b,
    B3B a2122ad113d9cffa9, DEC a125dd54bda6411e1.

## 2026-11-18
- P-1 review (Independent agent ad268b9007a43ecc9): 0 blocking, 5 major, 9 minor. All accepted. The amendments are in
  REVISIONS-post-freeze.md, and the world-author prompt is frozen as WORLD_AUTHOR_PROMPT_D.md (sha256 cc028f55…).
  Session scratchpad: 99 files moved to designer/scratchpad_archive_2026-11-17/ (PC P-2 practice).
- Brief authors: B3A and DEC stopped on the usage limit and were resumed. All five finished, 72 briefs in total.
  Sonnet check (record/AUTHOR_RUN.md): all valid, no outside path, no ctx_* call, no repository URL.
- Designer checks: mechanical checks (designer/brief_mech_check.py) found 0 problems. term_check_d found 0 hits. The
  reading review is in record/designer/BRIEF_REVIEW.md: no rejection.
- shuffle_d: seed from FREEZE_PREREG_D.json (a3dd33fa…). Ids D-001..D-072; 6 batches of 12 in shuffle/.
- Case folders are in cases/ (brief.json with dims; PRIVATE.json with approved_value pending).
- A0 sandboxes are in audit_a0/{B2,B3,DEC} (MANIFEST_a0.json). Auditors (general-purpose, sonnet): B2 a70c44458567dba9d,
  B3 a022fc96f3a0a65ee, DEC a4cf5b3e2c6c5da36.
- A0 first pass: B2 28 yes, 2 no (D-011, D-013); B3 29 yes, 1 no (D-017); DEC 9 yes, 2 no (D-028, D-033), 1 n/a (D-032).
  Auditors on Sonnet, no outside paths, except that the B2 auditor wrote and read v.txt in the session scratchpad.
  v.txt moved to designer/scratchpad_archive_2026-11-18/ (P-2 event 1). set_by_brief check: D-061 has the same defect
  and is sent back (P-2 event 2).
- Revisions done by the brief authors (resumed): B2B-13 27.78, B2B-07 50.0, B3A-02 0.1, DEC-02 1000, DEC-R1 1000,
  DEC-01 1500. Only note_value and note_value_source changed. Propagated to cases/ and to the A0 sandboxes. A0 re-audit
  sent to the same three auditors.
- Criterion authors (kodlayici) started: B2A af71d71744b42e486, B2B a7d3292312140f1a8, B3A a987caff7ebb6ec1f,
  B3B a32bf8196f7e404ae, DEC abc58c474656d8fe0. Their PRIVATE.json copies predate the six A0 revisions. The
  revisions touch only structure_statistic, which no body reads.
- A0 re-audit: all six revisions are yes. A0 is final: 71 yes, 1 n/a (D-032). approved_value is written into
  cases/*/PRIVATE.json (and structure_statistic.note_value). Frozen as record/FREEZE_A0.json (core f91c94e2…).
- Structure authors (kodlayici, fresh), sandboxes in structure/ (MANIFEST_structure.json; NOTE.json holds the allowed
  fields only): B2A a11199196e334e5e0, B2B aa1f289e148303b66, B3A ae7959dba03f3368a, B3B a1a5e977f194b55b8,
  DEC a16327a1facfa3522.
- Criterion authors B2A, B3A, B3B and DEC finished (B2B still running). All four valid (record/AUTHOR_RUN.md: Sonnet
  only, no ctx_*/agent calls, no outside path, no URL; inputs unchanged per designer/manifest_check.py; LOG.md
  append-only). Transcripts copied to transcripts/criterion_<half>_agent-<id>.jsonl.
- Usage limit (5-hour) stopped criterion B2B and all five structure authors; resumed after the reset with the
  content-free message "Continue from where you stopped." (same practice as the brief authors).
- Author questions on guards: B3B (D-019, D-048, D-051, D-002, D-001, D-063) and B3A (D-006, D-015) return None when
  a measurement-error-corrected variance is not positive, read as "a zero variance" (variance component truncated at
  zero; the corrected statistic is undefined). Every CASE.md states this reading. Decision (Claude, delegated): the
  designer gives no ruling and changes no body; the frozen place for judging guards is fidelity audit part A item (d)
  (FIDELITY_AUDIT_D.md, "Judge every comparison listed in MECH_CHECK.json"); a rejection there follows the section
  2.4 repair path. The same holds for the guard-minimum deviations (B3A D-040, D-062, D-008, D-031: minimum lowered to
  the smallest defined size; B2A D-029: raised to 2, the smallest size at which leave-one-out 1-NN is defined).
  No result of any kind had been seen.
- Criterion author B2B finished after the resume; valid (record/AUTHOR_RUN.md). All 72 cases have both bodies and
  CASE.md (144 body files, each importing only numpy).
- Structure authors: all five finished after the resume; valid (record/AUTHOR_RUN.md). 72 reference.py.
- Case folders assembled (designer/assemble_cases.py; MANIFEST_cases_assembled.json, 288 files). B3B's reference.py was
  first copied while its author was still running; those 15 copies were removed and re-copied after it finished.
- Skeleton check of reference.py: first run, 57/57 failed on "TypeError: ... 'dict' and 'str'" (the frozen tool reads
  sizes as text; Phase C P-3 again). Decision as PC P-3, recorded as REVISIONS-post-freeze.md P-3 event 1: check folders
  validity/skelcheck/<id>/ with sizes as JSON text (designer/skelcheck_folders.py); case folders unchanged. Second run on
  all 72: 70 pass; D-014 and D-041 fail "X has non-finite values" (their briefs define missing values as NaN).
- §2.4 row applied: one return to structure author B2A (message quoted only the issue list). It changed nothing (reason
  in its STRUCTURE_LOG.md). Recheck: both rejected again -> D-014 and D-041 DROPPED (label "reference rejected by
  check_skeletons_d"), P-3 event 2. Transcript recheck valid.
- mech_check_bodies.py on all 72: ok (includes the reference arm's single-difference check); MECH_CHECK.json in each
  case folder.
- Validity runs started for the 70 remaining cases (designer/run_validity.py, 5 workers on 6 physical cores, BLAS
  threads 1; order in validity/RUN_ORDER.txt, slow criteria first). Results go to validity/<id>/RESULT.json (outside the
  case folders, never shown to auditors); the tool's log is cases/validity_log.jsonl.
- Guard questions: P-3 event 3 (no designer ruling; fidelity A item (d) judges).
- designer/world_run_check.py commissioned from kodlayici (agent a2dcdbaf87c072712), with tests.
- designer/world_run_check.py done (kodlayici a2dcdbaf87c072712): the ten checks of P-1 amendments 1, 2, 6, 7 (meta,
  frozen prompt + injected remainder, no later user message, claude-opus-5-5 only, forbidden tools, linked transcript,
  term scan of remainder/attachments/prefix, outside paths, settings incl. effort xhigh and harness version, skeleton
  provenance by rebuilding Write/Edit with the Edit line-ending behaviour measured on this machine). Tests:
  designer/tests/test_world_run_check.py, 89 passed (rerun by the designer). Smoke on the Opus pre-flight:
  designer/check_world_preflight_smoke.json (valid false only because the prompt is not the frozen one, as expected).
- Validity, 65 light runs done (05:11-05:21 UTC): 24 pass, 41 drop (counting labels: V2 28, V1b 7, V1a 6); no error,
  so no repair row. Log cases/validity_log.jsonl: 65 lines, 65 decisive, all parse. Decisions:
  validity/TABLE_DECISIONS.json (designer/apply_table.py, Precedence and Counting-label rules). The five slow B2B runs
  (D-058, D-018, D-065, D-059, D-013) are still running.
- V2 failures were read for a systematic tool defect: none seen. They split into noise-probe failures (mostly
  change-vs-baseline claims: noise creates regression to the mean that the corrected criterion also flags) and plus
  failures (the reference plus world too weak for the fixed criterion), both what V2 is there to remove.
- Provisional selection (designer/selection.py -> validity/SELECTION_provisional.json): B-2 10 (4 pending), B-3 8,
  B-1 1, B-6 3. Decoy reading: decoys have no halves and ALLOCATION_D.json lists their reserves by source only, so a
  dropped decoy is replaced from its decoy class's reserves in order. Section 6: a class with fewer than 16 pairs is
  "insufficient cases" (no verdict); the protocol neither stops nor allows new pairs. Items 7-8 continue (cheap,
  Sonnet); the author will be asked before item 9 (Opus world authors) whether to continue, with the facts.
- Fidelity part A sandboxes (designer/build_audit_a.py; MANIFEST_audit_a.json): passed pairs only, no validity result
  (scanned). B2 11, B3 9, DEC 4. Prompt A_PROMPT.md (adds the scratchpad sentence of P-2). Auditors (general-purpose,
  sonnet, fresh): B2 ad3c3617321082f3a, B3 a5efff89549f1383f, DEC ac17ad9d643bd1460.
- Fidelity A, B-2 (ad3c3617321082f3a): 11/11 pass. Transcript valid (Sonnet only, no forbidden tool, no outside path;
  URLs: PMC10499856, pubmed 12509396). Inputs unchanged. Remark: PB §4's term list is not in the sandbox; the auditor
  scanned the briefs itself (the designer's term_check_d found 0 hits earlier).
- Fidelity A, decoys (ac17ad9d643bd1460): 3 pass, D-046 fails item (h) ("Ten animals each received a different dose":
  a fact about how a variable is arranged). Brief item -> DROP (label "fidelity A (h)"); PB has no designer override
  (a disputed pair is dropped). Transcript valid; inputs unchanged. designer/selection.py now reads AUDIT_A.json.
- Fidelity A, B-3 (a5efff89549f1383f): 8 pass, D-045 fails item (h) (baseline_score_retest described as "a second,
  independent reading": a stated relation between variables) -> DROP ("fidelity A (h)"). Transcript valid; inputs
  unchanged. Its one Python read hung on a malformed heredoc (reading its own sandbox extracts); the designer stopped
  that bash process (pid 11908 and child 18452) after the auditor had written its files; it produced no output.
- Selection now (designer/selection.py): B-3 7 (nothing pending); B-2 10 now, at most 15 even if all five slow runs
  pass validity and audit. Both classes are certain to be below 16 = "insufficient cases" (section 6): no verdict for
  H-D1, H-D2. H-D3 (pooled, n about 17-22) stays testable at low power. Decoys: B-1 1, B-6 2. Author asked whether to
  continue to item 9 (Opus world authors); item 8 (freeze) proceeds when the slow runs end, whatever the answer.
- AUTHOR DECISION (2026-11-18, AskUserQuestion): "Plana göre devam (Önerilen)" — continue as pre-registered: freeze
  validity, then the W-0 and W-1 world authors (Opus). H-D1/H-D2 will read "insufficient cases"; H-D3 at low power.
- Prepared for item 9 (not run): designer/build_world_sandboxes.py (world/<neutral label>/ per batch and arm;
  WORLD_INSTRUCTIONS_D.md = D0 or D1 copy, BATCH.json, agent_docs/, pkg/, empty skeletons/; private map
  SANDBOX_MAP_world.json outside world/). Term list for the injected-context scan: designer/world_terms.txt (90 terms:
  28 source keys, class and subtype labels, 15 tags, error names, designer files, arm names). Pre-scan of today's
  injected files (MEMORY.md index, the three CLAUDE.md): no hit.
- designer/build_freeze_validity.py written; dry run (65 decided pairs, 5 pending) passes
  tools/check_validity_log_d.py: 65/65 (validity/check_log_dryrun.json).

- (2026-11-18 ~11:30 UTC) Slow validity runs ended (runner exit 0): D-013 V2; D-059, D-065, D-058 V1a + timing infeasible
  (label V1a); D-018 timing infeasible. All five dropped (rows computed without error, final). Table: 24 pass, 46 drop.
- Final selection (designer/selection.py -> validity/SELECTION.json, copy of SELECTION_provisional.json): B-2 10, B-3 7,
  decoys 3 (B-1 1, B-6 2). Passed but unused reserves: D-026 (B3B-11) and D-070 (B2B-11), whose subtype/tag had no dropped
  main. Every selected pair passed fidelity A. B-2 and B-3 are below 16 pairs -> insufficient cases (section 6); the
  author's decision "Plana göre devam" applies.
- Item 8: designer/build_freeze_validity.py -> validity/FREEZE_VALIDITY.json (70 pairs, pending none, REPAIRS none).
  tools/check_validity_log_d.py: 70/70 pass (validity/check_log_final.json). Log snapshot validity/validity_log_at_freeze.jsonl.
  protocol/tools/freeze.py write: 585 files (FREEZE_VALIDITY, SELECTION, TABLE_DECISIONS, the log check, the log snapshot,
  70 RESULT.json, AUDIT_A json+md of the three classes, the input files of all 72 case folders) ->
  record/FREEZE_VALIDITY_MANIFEST.json, core_sha256 dce6b4a4d7b5273ead799e552b8a31e4e7254472f002006b55a211636f594176.
- Item 9 setup: shuffle/SUBSET_IDS.json (20 ids); tools/shuffle_d.py --subset -> batches_subset_01 (12), _02 (8).
  designer/build_world_sandboxes.py -> 4 sandboxes in world/ (map private: SANDBOX_MAP_world.json; MANIFEST_world.json).
  Scratchpad empty; memory index neutral. Harness is now 2.1.326 (pre-flight: 2.1.325); same major version, so allowed
  under P-1 amendment 7; recorded in WORLD_RUN.md. Effort passed as xhigh (P-1 amendment 7).
  Order, Claude (yetki devriyle): strict alternation, one agent at a time: batch 1 W0, batch 1 W1, batch 2 W0, batch 2 W1.

- (2026-11-18 ~13:00 UTC) Item 9, batch 1 W0 (sandbox cd14f4, agent a15737ab198e93dbf) STOPPED by the API usage limit
  (HTTP 429). The harness suggested resuming it by message; not done (P-1 amendment 1: no designer message after the
  prompt; a stopped batch goes to a new fresh agent). Transcript -> transcripts/world_b1_stopped1_agent-*.jsonl
  (16414bf3c2e7f793). v1 check: (i) 5 term hits in the injected context, all in generic harness text (the context-mode
  hook's `tool_selection_hierarchy`, skill listing `DOM structure`, `a checklist`, `a review checklist`, Wiki CLAUDE.md
  `## wiki/ structure`), the same hits are in the 2026-11-17 pre-flight transcript (plus `B-1` inside UUID text there):
  a matching defect of the term scan (serialized JSON, substrings), not a leak; (ii) skeletons/D-042.py was changed by a
  Bash `py -I - <<EOF` script, so the Write/Edit rebuild cannot match (P-1 amendment 2 would make every such batch
  invalid). Next agent held until world_run_check_v2.py (decoded scan, word boundaries, pre-flight baseline exemption;
  provenance by full replay in an isolated replica) is written and tested (kodlayici a90760aff2848bcbd). Recorded as P-4.
  designer/add_world_sandbox.py written (new sandbox per redo; old sandbox untouched).

- TIME CORRECTION: the two entries above marked "~11:30 UTC" and "~13:00 UTC" used PowerShell `Get-Date -Format u`,
  which prints local time (UTC+3) with a Z. Actual UTC: ~08:30 and ~10:00. Python timestamps (runner.stdout, JSONL logs)
  are true UTC.
- world_run_check_v2.py by kodlayici a90760aff2848bcbd (sha256 940f7ecee76d7305; v1 cc2e4d79b4ab7f0c unchanged). Designer
  reran the tests: 157 pass (v1 89, v2 68). v2 on the stopped transcript: no invalidating hit (3 baseline, 1 new in an
  informational request blob), D-042.py replayed_match (25 replayed calls, 0 timeouts, 0 refused); replay dir
  world_replay/cd14f4_20261118T101313. Recorded as REVISIONS-post-freeze.md P-4 (uncommitted).

- (10:16 UTC, true) Usage before launch: 5-hour window 14 %, weekly 71 % (resets 2026-11-22). New sandbox e515ad
  (designer/add_world_sandbox.py, redo_of cd14f4). Scratchpad empty. Batch 1 W0 redo launched: general-purpose, opus,
  effort xhigh, frozen prompt with <SANDBOX> = E:\Claude Projects\Kapi\phase_d_work\world\e515ad (agent a565a633763173ab2).
  All batches are checked with designer/world_run_check_v2.py (P-4).

- (10:38 UTC) Batch 1 W0 redo (e515ad, a565a633763173ab2) STOPPED by an API connection error (SSL certificate
  verification failed) after 7 of 12 skeletons. Transcript world_b1_stopped2_* (028aba18c40c22a3). v2 check: no
  invalidating hit, 7/7 match. Not resumed; next redo in a new sandbox.

- (10:40 UTC) Usage: 5-hour 32 %, weekly 73 %. New sandbox eb6876 (redo_of cd14f4, e515ad). Scratchpad empty. Batch 1 W0
  third agent launched (a4e666972a482843b), same frozen prompt with <SANDBOX> = ...\world\eb6876, opus, xhigh.

- AUTHOR DECISION (2026-11-18, ~10:50 UTC): asked whether world authors could run at effort high instead of xhigh (to save
  quota); designer recommended keeping xhigh (P-1 amendment 7, world quality, small saving). Author: "xhigh ile devam et".
  Effort stays xhigh for every world-author batch.

- (10:58 UTC) Batch 1 W0 (eb6876, a4e666972a482843b) COMPLETED: 12 skeletons + WORLD_LOG.md; v2 check VALID
  (world_checks/b1_W0_v2.json; transcript 1132fa2e37cf4893). Recorded in WORLD_RUN.md. Effort xhigh is now fixed for all
  batches (P-1 amendment 7; author decision).

- (11:00 UTC) Usage: 5-hour 50 %, weekly 75 % (one full batch ~ 18 % of the 5-hour window, ~ 2 % weekly). Scratchpad empty.
  Batch 1 W1 launched in c13bd2 (agent a3cc033baa3d37a06), same frozen prompt, opus, xhigh.

- (11:25 UTC) Batch 1 W1 (c13bd2, a3cc033baa3d37a06) COMPLETED: 12 skeletons + WORLD_LOG.md + CHECKLIST_LOG.md; v2 check
  VALID (world_checks/b1_W1_v2.json; transcript e3cec5edb200e956).

- (11:30 UTC) designer/collect_skeletons.py (new): copied the valid batch 1 skeletons (eb6876 -> W0.py, c13bd2 -> W1.py)
  into cases/<id>/skeletons/; MANIFEST_skeletons.json. designer/skelcheck_folders.py: small fix (remove an existing
  read-only copy before copy2; the frozen case files are read-only since item 8); reran for the 12 batch 1 ids.
  tools/check_skeletons_d.py --case validity/skelcheck/<id> (12) --require-arms --package-root record/pkg:
  36/36 pass (reference, W0, W1; validity/skeleton_check_world_b1.json/.stdout). No return needed.

- (11:31 UTC) Usage before launch: 5-hour 71 % (batch of 8 expected ~ 12-15 %), weekly 78 %. Scratchpad empty. Batch 2 W0
  launched in 5f14e6 (agent a7c61e6cd14264fb2), frozen prompt, opus, xhigh. Batch 2 W1 to follow when the 5-hour
  window has room (reset 15:00 UTC).

- (11:38 UTC) Batch 2 W0 (5f14e6, a7c61e6cd14264fb2) COMPLETED: 8 skeletons + WORLD_LOG.md; v2 check VALID
  (world_checks/b2_W0_v2.json; transcript 07aa6e34ee78854d).

- (11:42 UTC) Usage 5-hour 83 % (batch 2 W0 used ~ 12 %), weekly 80 %. Batch 2 W1 held until the 15:00 UTC reset so it is not
  cut off. Item 10 for batch 1 started meanwhile (local CPU only): designer/run_timing_arms.py (new; same process settings
  as run_validity.py, 5 workers) on the 12 batch 1 cases x W0/W1 -> validity/<id>/TIMING_<arm>.json, log lines
  mode timing_arm in cases/validity_log.jsonl, runner stdout validity/timing_runner_b1.stdout.

- (11:39-11:40 UTC, true) Item 10 batch 1: 24/24 timing runs OK, all decisive; estimates 2.0-206.5 s (max D-035 W0), none
  above 1800 s, no redo. designer/build_timing_arms.py (new) -> validity/TIMING_ARMS_b1_draft.json (24 entries);
  check_validity_log_d.py --timing-arms: 24/24 pass, the 70 freeze pairs still pass (validity/check_log_timing_b1_draft.json).
  Final TIMING_ARMS.json after batch 2.

- (15:03 UTC) Usage after reset: 5-hour 0 %, weekly 80 %. Harness 2.1.326. Scratchpad empty. Batch 2 W1 launched in 3d2b82
  (agent aae5eeac665b6a413), frozen prompt, opus, xhigh.

- (15:25 UTC approx.) Batch 2 W1 (3d2b82, aae5eeac665b6a413) completed but INVALID (v2 check): TaskStop + ToolSearch for it
  (forbidden tools) and a Read of its own background-task output file outside the sandbox (disclosed by the agent). The
  rules are mechanical and pre-registered; no exception (it would be a post-hoc change). Outputs unused; redo in a new
  sandbox, logged next to batch 2 W0.

- Usage: 5-hour 21 %, weekly 83 %. New sandbox d5f53a (redo_of 3d2b82). Scratchpad empty. Batch 2 W1 redo launched
  (agent aa6b4334a3206fad1), frozen prompt, opus, xhigh.

- (15:43 UTC) Batch 2 W1 redo (d5f53a, aa6b4334a3206fad1) VALID (world_checks/b2_W1_redo1_v2.json; e701d4a182626f52).
  All four batches now valid (orders 3, 4, 5, 7 of WORLD_RUN.md). Batch 2 skeletons collected (5f14e6 W0, d5f53a W1);
  check_skeletons_d: 24/24 pass (validity/skeleton_check_world_b2.json). Item 10 batch 2: 16 runs, all OK, max 48.7 s.
  One log line (D-052 W1) lost to a concurrent append -> REVISIONS P-5; D-052 rerun with one process; TIMING_ARMS.json
  final: 40 entries, redo 0; check_validity_log_d.py --timing-arms 40/40 pass, freeze pairs 70/70
  (validity/check_log_timing.json). Log-writing runs are sequential from now on.

- (15:47 UTC) Item 11: designer/build_audit_b.py (new) -> audit_b/{B2 (10), B3 (7), DEC (3)}: part-A case files + X.py/Y.py
  (random labels; private map AUDIT_B_MAP.json; MANIFEST_audit_b.json); no audit output, world logs, checklist logs or
  results. Prompt B_PROMPT.md (<G> replaced). Fresh Sonnet general-purpose auditors (P-1 amendment 10): B2
  ade37970402e2eb7f, B3 a760024aad93074cd, DEC a27c75bf9dc22c8dc. Usage before: 5-hour 38 %, weekly 85 %. Scratchpad empty.

- Item 12: tools/expected_flags_d.py --case cases/<id> (the 20 selected) --package-root record/pkg --phase-c-expected
  kapi-oss/evaluation/phase_c/EXPECTED_FLAGS.json -> EXPECTED_FLAGS_D.json: 60 case/arm entries (reference, W0, W1);
  base list equals Phase C's. (Part B has no replacement, so the skeletons are final.)

- Item 11 results so far: DEC (a27c75bf9dc22c8dc, transcript 75c7085ad06dc02d): 3/3 cases X yes, Y yes; remark: the
  `change` string of one D-047 skeleton names "regression to the mean" (no key/variable named by its role; judged no
  leak; no change allowed, P-1 amendment 2). B2 (ade37970402e2eb7f, 0703e087edc76623): 10/10 X yes, Y yes. Both
  transcripts checked with designer/author_run_check.py: Sonnet only, no forbidden tool, no outside path, no URL; reads
  cover every X.py/Y.py (loops over the case folders).

- Item 11 B3 (a760024aad93074cd, f4cb674f6eedfb44): 7/7 X yes, Y yes (remarks: wording in a D-056 minus docstring, judged no
  leak). Transcript check: Sonnet only, no forbidden tool (one TaskStop on its own background command, allowed for
  auditors), no outside path, no URL. ITEM 11 DONE: 20/20 pairs, both skeletons yes; no part-B attrition.
- Awareness readings (AWARENESS_RULE_D.md) still to do: readers must not know the arm. The designer knows the arms (sandbox
  map, agents' final reports), so the designer cannot be the arm-blind first reader that P-1 amendment 10 assumed (as in
  PC) -> decision pending (P-6).

- P-6 recorded (two fresh Sonnet readers; designer not a reader). designer/build_awareness.py (new) first ->
  awareness/r1, awareness/r2 (READER_RULE.md + ENTRIES.md, 40 entries E01..E40; map AWARENESS_MAP_first.json private;
  MANIFEST_awareness.json). Arm/label scan of ENTRIES.md: no arm or sandbox label (only domain words "batch").

- Awareness first reading: r1 (a5480c3f73eb1710d, be5089a63770a479) and r2 (ad3d105f96c903abe, fda29edf3c350498) valid
  runs (Sonnet, sandbox only, no URL), 40/40 entries each. r1 stated that it did not count an entry's general notes as
  awareness by themselves, against the prompt ("applied to the text of that entry only (its general notes included)").
  Decision (Claude, delegated), made before any per-arm or per-case look at the readings: r1 is replaced ONCE by a fresh
  reader r1b with the identical prompt and identical files (awareness/r1b, same hashes); r1b's reading is used whatever
  it says; r1's reading stays in the record, marked excluded with this reason.

- r1b (ade213fe9ac941553, bea5b64101769af5): valid (Sonnet, sandbox only), 40/40. First reading FROZEN:
  record/FREEZE_AWARENESS_FIRST.json (r1 [excluded], r1b, r2 READING.json/.md + AWARENESS_MAP_first.json), core
  28972bb17b4ce21db847d64935c7a8b854a28e08a4d5a2b6c168ae17e78de87c. No per-arm tally computed yet.
- Second reading (W-1, WORLD_LOG + CHECKLIST_LOG): build_awareness.py second -> awareness/r3, r4 (20 entries F01..F20;
  AWARENESS_MAP_second.json private).

- Second reading: r3 (aa6da8fddbf6aa1de, 0e4a3f7e0ae6bd75) and r4 (ad55c89ef6720ae7b, 6a4a6617c675cd52) valid (Sonnet,
  sandbox only), 20/20 each. FROZEN: record/FREEZE_AWARENESS_SECOND.json, core
  5ba1438b64464905e186301b1e814f2949c55fce915f9e3ccce701b705cc29b3. Per-arm tallies left for the report (descriptive).
- Item 13 (preparation): designer/build_public_d.py copies the case folders, the expected flags and the pre-run record
  into kapi-oss/evaluation/phase_d (cases/, EXPECTED_FLAGS_D.json, record/), with a private-data scan; then
  FREEZE_CASES_D.json and FREEZE_RECORD_D.json; commit and push only with the author's explicit approval.
