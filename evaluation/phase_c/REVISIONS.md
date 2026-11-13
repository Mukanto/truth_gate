# Revisions to the Phase C pre-registration

Decisions by Claude under the author's delegation.

## Draft v1 → v2 (2026-11-13), answering `REVIEW1.md` (5 blocking, 9 major, 7 minor)

| # | Finding | Change |
|---|---|---|
| 1 | Public docs carry Phase B results (blocking) | §4 item 0: an **agent document set** built from tag `v0.5.0` (GATE, MANIFEST, SPEC, tool parts of README), every evaluation-result sentence removed, mechanical scan recorded, frozen (`FREEZE_AGENT_DOCS.json`) before any agent reads it; CHANGELOG and EVALUATION excluded. All instruction files point to `agent_docs/` only. |
| 2 | Fable identification and fallback (blocking) | §4 item 3: pre-flight agent with no brief; evidence = model ids recorded in the harness transcript (`subagents/agent-<id>.jsonl`, field `model`), copied into `WORLD_RUN.md`; any other model in a batch invalidates it (one redo, then stop); if Fable cannot be started, wait without limit; a substitute requires a reviewed revision before any skeleton. The designer ran such a pre-flight on 2026-11-13: the request metadata says `fable`, every recorded assistant message says `claude-fable-5-2`. |
| 3 | Invalid skeletons (blocking) | §4 item 4: frozen `tools/check_skeletons.py`; one redo by a fresh Fable agent with only the error list; still failing = dropped "skeleton invalid", reported by id; unscriptable properties are not grounds for a redo. The wrong reference ("step-3 script") is corrected to PB §4 step 4 / Phase B P-1. 12 pairs planned per class (no oversampling; drops accepted, "insufficient cases" below 10). |
| 4 | "Does not know the error" presupposes what Phase B refuted (blocking) | §0 and I-8: "is not told"; every class verdict statement carries the class's P/C/N shares and the wording "declared worlds that may contain what the error exploits"; banned wordings ("unaware", "did not know", "blind"). |
| 5 | No preventive rule against brief steering (blocking) | §2 "Briefs state only the setting"; keys name what was measured; new fidelity item **(h)**; `AUTHOR_PHASE1_C.md` and `AUDIT_PHASE_C.md` carry it. |
| 6 | Overlap not operational (major) | §1: overlap key (same source key AND mechanism AND statistic name) against the frozen `PHASE_B_TABLE.json`; > half overlapping → fixed wording; ≥ 4 of 12 pairs per class on passages not used in Phase B, ensured by the designer before the briefs (addendum if needed). |
| 7 | Primary comparison: deterministic, no informativeness rule, "counts against" undefined (major) | §2: exactly one criterion `C` per file (unit = that component); §6: a loss is a regression against spec 0.7 §4 → patch, rerun, both reported; fewer than 5 files with an UNDEFINED component under 0.4.1 → "not informative"; causes listed; I-7 adds the documentation exposure. |
| 8 | Guard rule vs 0.5 docs (major) | §2 and `AUTHOR_PHASE2_C.md`: the guard list is exhaustive; minimum = smallest size at which the statistic is defined, stated in the note; docs advice does not widen it; audit (d) checks it; abstention shares reported per class (§6). |
| 9 | Size cap keeps errors too small (major) | §2: caps raised to 1000 rows and 500 features, timing rule binding; source sizes where they fit; the note cites the source on size dependence; size ratio per pair reported; "error too small" label in the report where it applies. |
| 10 | B-3 estimand (major) | §2 "Estimand": the claim is about the fixed analysis's quantity; the note names both estimands; new fidelity item **(i)**. |
| 11 | World prompt not pinned (major) | `WORLD_INSTRUCTIONS_PHASE_C.md` and the other instruction files are written now and frozen with the prereg, each with a table of differences from Phase B; the log requirement is unchanged; log length per brief reported (§4 item 4). |
| 12 | Contamination paths (major) | §4 items 1 and 3: sandbox folders with copies of only the allowed files; no fetching from the project's repository or published Phase B material; URLs logged; `SOURCES.md` stripped of Phase B notes; the designer rejects briefs only for listed reasons, logs each rejection, never edits a claim; §4 item 7 states the honour-system limit. |
| 13 | Single-reader awareness (major) | §4 item 4: a second blind reader (fresh agent, logs and rule only); disagreement → higher level; both reported; rule copied in `AWARENESS_RULE_C.md`. |
| 14 | Continuity (major) | §4 item 3: fixed Fable batches of at most 15 in shuffle order, fresh agent per batch, identical instructions, progress = files passing the check script, stopped batches continued by a fresh Fable agent, model ids per batch; item 5: body authors always fresh agents. |
| 15 | "Source caps" ambiguous (minor) | "per-source pair caps (section 1)". |
| 16 | "Independent read sources" undefined (minor) | §1: "read" = the documenting passage read and quoted or located (abstract counts if the passage is in it). |
| 17 | Per-version timeouts (minor) | §6: a timeout is a miss / failed clean pass in that version's table and "not comparable" in the primary comparison. |
| 18 | Baselines' version (minor) | §6: noise-only and declared-only from 0.5.0 with a 0.4.1 line; out-of-scope cases carry the list for description only. |
| 19 | Software state (minor) | §4 item 0: commits of both tags, Python, numpy, machine recorded; smoke test under both tags; §6: infrastructure failure rerun once, both logged. |
| 20 | Push approval (minor) | §5: no approval, no run; runner and recomputation written after the push, reading only frozen files. |
| 21 | Class fixed at the shuffle (minor) | §1: class and subtype fixed at the shuffle, never changed; disagreements reported. |

## Draft v2 → v3, for freeze (2026-11-13), answering `REVIEW2.md` (1 blocking, 9 major, 10 minor)

| # | Finding | Change |
|---|---|---|
| 1 | "Setting only" has two readings; (h) worded twice (blocking) | One verbatim text ("what a brief may state", the reviewer's proposal with "time in order" as setting and "no data key names a variable by its role in the error") in §2, `AUTHOR_PHASE1_C.md` and `AUDIT_PHASE_C.md` (h); (h) is answered by the text; four worked examples (pass/fail) for B-1, B-2, B-3, B-6. |
| 2 | "New passage" undefined; input leaks Phase B (major) | Replaced by **new sources**: ≥ 4 of 12 pairs per in-scope class from the frozen `SOURCES_ADDENDUM.md` (KRI10, MOR03, VAR06, CUR13, LAZ18; passages read by the designer); authors are not told which passages Phase B used; fewer than 4 → one return, then "new-source minimum not met" reported; counted on surviving pairs. |
| 3 | Overlap key not applicable with one reading (major) | Closed `mechanism_tag` and `statistic_family` vocabularies in `PHASE_B_TABLE.json` (Phase B pairs tagged by the designer before any Phase C brief); notes carry tag and family; key = same source AND tag AND family, applied mechanically; addendum pairs cannot overlap; "strictly more than half of the pairs entering a class table"; I-9 states that overlap above one half is plausible in B-1, B-3, B-6. |
| 4 | B-3 has no slack; feasibility not shown (major) | CUR13 added (B-3 now 4 sources, up to 16 pairs within caps); the B-3 example in `AUTHOR_PHASE1_C.md` shows a claim at the fixed estimand without banned terms. |
| 5 | No timing remedy after the skeleton freeze (major) | §2 timing remedy: make the fixed criterion faster; then one size request executed by a fresh Fable agent; then drop as "timing infeasible"; restored in `AUTHOR_PHASE2_C.md`. |
| 6 | Package not specified (major) | §4 item 0(b): a clean copy of `truth_gate/` and `kapi/` from tag `v0.5.0` as `pkg/` in every sandbox, first on `sys.path`; frozen in `FREEZE_AGENT_DOCS.json`; the editable install is named in the honour-system limit. |
| 7 | Fable sub-agents; evidence not frozen (major) | World instructions forbid starting agents or model-running tools; a batch that called such a tool or has a linked agent transcript is invalid; tool names per batch in `WORLD_RUN.md`; batch transcript SHA-256 frozen with the skeletons; a new pre-flight at item 0, frozen. |
| 8 | Difference tables incomplete; (d), (g) weakened (major) | Phase B wording of (d) and (g) restored; dropped sentences restored (setting the source describes, open full texts, other authors' folders, describing the faulty procedure, `work\` folder, "never saw those notes"); the auditor gets stripped `SOURCES.md` and the addendum; every table rewritten line by line against the Phase B file. |
| 9 | Script's 100 ms limit not stated (major) | Rule 6 of the world instructions now states the 100 ms limit (worlds and controls) and the 10 ms aim; the script times controls too. |
| 10 | Loss rule could read as weaker than R3 (major) | §6: "The v0.5.0 table is the pre-registered primary table"; a loss counts against 0.5.0 whatever a later release does; a patch result is secondary. I-8 states that its claims wording is stricter than R3's sentence. |
| 11 | P-2 for sources without sizes (minor) | §2 sizes: the note gives the largest size within the timing estimate or why a smaller one is realistic; `P2_READING.md` applies with that note. |
| 12 | Docstring period (minor) | Template without the period; exact rule stated. |
| 13 | `np.random` (minor) | "do not use `np.random` at all". |
| 14 | Script hardening (minor) | Banned names → no execution; caps checked (1000 per axis, 500 000 values); controls timed and control worlds checked; every dimension must be stated as a number in `sizes`. |
| 15 | Batch cut and redo (minor) | Consecutive blocks of 15 (last shorter); a continuation after a stop is the first attempt. |
| 16 | Freeze list (minor) | The header lists every frozen file including `P2_READING.md`, the addendum and all five scripts; shuffle seeded from the bytes of `FREEZE_PREREG_C.json`; the agent documents, package copy, smoke test, pre-flight and software state frozen at item 0. |
| 17 | Scan terms (minor) | `scan_docs.py` terms extended (pilot, case study, Tenkit, E1–E3, external, detection rate, miss, private, audit, Phase A/B/C, B-1–B-6); a hit that cannot be removed blocks the first agent. |
| 18 | Which P/C/N reading (minor) | The resolved (higher) reading in verdict sentences; both in the table. |
| 19 | "Not informative" files (minor) | Defined: Phase C study files, faulty and fixed, all classes; a component whose verdict under 0.4.1 is UNDEFINED; I-7 says "not informative" is probable. |
| 20 | Smaller points (minor) | P-1 reference dropped (script frozen); Phase B P-3 carried into §2; new-source count on surviving pairs; the designer checks the brief half of (h) and (i) at step 2. |

## Draft v3 → v3 with the review-3 fixes, for freeze (2026-11-13), answering `REVIEW3.md` (0 blocking, 3 major, 13 minor)

The review's header counts 12 minor findings; its list has 13 (m1–m13). All are answered; no design change.

| # | Finding | Change |
|---|---|---|
| M1 | `scan_docs.py` crashes on a cp1252 console; "no hit" unattainable with tool vocabulary | Script: UTF-8 output with replacement, exit 3 on any exception, `--allow FILE` (hits listed by file, exact line text and tokens; stale entries reported). §4 item 0(a): every hit read by the designer and a fresh agent; removed if either reader finds an evaluation, result, count, case, source key or Phase B/C class; otherwise listed as tool vocabulary in `agent_docs/SCAN_REVIEW.json` (frozen with `FREEZE_AGENT_DOCS.json`); ready when no unlisted hit remains. The token lists are unchanged. |
| M2 | Feature cap stated two ways | One rule, §2 as written: at most 1000 along any axis and 500 000 values per array, no separate feature cap; "500 features" removed from `P2_READING.md` and audit item (f); §2 says so explicitly. |
| M3 | Overlap vocabulary without definitions | One-line definitions and a precedence order for every tag and family in `AUTHOR_PHASE1_C.md` ("Closed lists, with definitions"), copied verbatim (checked by script) into `PHASE_B_TABLE.json` `vocabulary` (`definitions`, `precedence`); §1: an ambiguous label is resolved by the definitions, the designer may change a label only to the one they require, each change logged. The designer re-read all 54 Phase B rows against the definitions and precedence: no tag or family changed (edge cases checked: B3-02 and B3-03, a ratio related to its own divisor, are `shared-measured-component`, which precedes `target-from-labels`; B6-12, a test on per-participant slopes, is `regression-slope`; B1-08, responders selected by a test, is `select-then-test-same-data` with `proportion`). |
| m1 | `numpy.random` passed the skeleton check | Both check scripts flag `.random` on every numpy binding (`np`, `numpy`, import aliases) and an assignment that aliases numpy or `numpy.random`; `rng.random(...)` stays allowed; in the twins only `<numpy>.random.default_rng(<int>)` inside the criterion. |
| m2 | Package root not verified | Both scripts fail (exit 2) unless the imported `truth_gate` lies under `--package-root PKG_DIR`, refuse a `truth_gate` already imported, and record `truth_gate_file` in the report. |
| m3 | Script rules not stated to the world author | World instructions rule 8 lists what the check script rejects; `sys.path` is for the author's own test scripts only. |
| m4 | VAR06 as L1.3 against PB §1 | §1 and audit instructions: an extension of PB §1's L1.3 to classifier parameters, not a change of PB §1; not reported as a disagreement. |
| m5 | B-3 example from a Phase B source; steering | The B-3 example uses a setting from no listed source (leaf nitrogen and photosynthetic capacity, adjusted for leaf area); the B-1 and B-6 examples, which resembled VUL09 and HUR84 settings, are replaced likewise (study items and hours; pupils in classrooms); "do not copy an example"; one paragraph on how the estimand is named for each B-3 mechanism; I-6 states that B-3 briefs name the adjusted-for quantity by rule. |
| m6 | Omissions in the difference tables | Audit (e) restored to Phase B's wording; `AUTHOR_PHASE2_C.md` regains the dropped sentences (no new imports or module-level code, the note written before the skeleton, "the criterion must not know how the worlds were built", the syntax-check command, pre-check logging with counts and rates, "for example a missing key", `CASE.md` items 5 and 6 in full); tables list the remaining differences. |
| m7 | Identification covers batches only | §4 item 3: every Fable agent of Phase C (pre-flight, batches, continuations, redos, regenerations, skeleton changes) falls under the identification and invalid-run rules. |
| m8 | No slack in the new-source minimum | §1: for B-2, B-3 and B-6 "not met" is expected to be common; a report line, not a verdict change. |
| m9 | Independent source count | Addendum: MOR03, VAR06 and CUR13 count as independent when read; KRI10 and LAZ18 do not; any 3 independent read sources from both lists. |
| m10 | `BATCH_01.json` vs `BATCH.json`; folder names; seed known early | §4 item 2: class folders `B1`, `B2`, `B3`, `B6`, `O`; each `BATCH_<nn>.json` copied unchanged as the batch's `BATCH.json`; the seed is known after the freeze, the order also depends on the briefs. |
| m11 | Freeze list and header | `REVIEW3.md` added to the header and to the frozen list; status line names v3 with these fixes. |
| m12 | Closed lists reveal Phase B structure | §1: the vocabulary is a designer's tool; the exposure (mechanism names, not cases, settings or passages) is accepted and reported. |
| m13 | B-2 pass example states a fact about rows | "rows: registry entries". |

After these edits the designer checked by script that the "what a brief may state" text is still identical in the
prereg, `AUTHOR_PHASE1_C.md` and `AUDIT_PHASE_C.md` (yes), and that the 54 Phase B rows and the tag lists of
`PHASE_B_TABLE.json` are unchanged (yes).
