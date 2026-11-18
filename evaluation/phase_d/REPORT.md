# Phase D report: Truth_Gate 0.5.1 on documented B-2 and B-3 errors, with and without a dependence checklist

**Status.**
- Written by the designer after the run, the designer's recomputation and the blind post-run audit.
- The audit's findings, and how each was handled, are in section 11. The audit's files are in `postrun/`.

All numbers come from the `run/` certificates through `score_phase_d.py` (`RESULTS_D.json`). The designer's separate
recomputation (section 9) and the post-run auditor's own recount (section 11) agree with every number they compared.

Every class result below concerns **declared worlds that may contain what the error exploits**. It is given with the
class's awareness shares (P / C / N, resolved first reading; section 6) and with this limitation, fixed by P-1
amendment 3:

> **Limitation.** "The world author is the designer's own model (Claude Opus 5.5). It was a fresh agent, not told the
> error, the class or the source, but it may share the designer's idea of realistic dependence and of the checklist's
> terms, which can favour detection and the checklist effect."

## 1. Headline

- **H-D1 (B-2) and H-D2 (B-3): no verdict, "insufficient cases" and "minimum not met".**
  - After the validity checks, B-2 kept 10 pairs and B-3 kept 7. Both are below the 16 that PREREG_PHASE_D section 6
    requires.
  - Both classes also miss the subtype minima of section 1:
    - B-2 has L3.1 = 1 and L3.2 = 0, against minima of 2 and 2;
    - B-3 has 5 ratio-shared-denominator pairs, 1 shared-measured-component, 1 ratio-vs-denominator-proxy and no
      change-vs-baseline pair, against at least 3 per tag.
  - **B-2, arm W-1:** attributable detection 9 of 10 (one-sided 95% Wilson lower bound 0.652), clean pass 10 of 10
    (0.787). Awareness P 1, C 1, N 8.
  - **B-3, arm W-1:** attributable detection 6 of 7 (0.548), clean pass 7 of 7 (0.721). Awareness P 2, C 5, N 0.
  - These bounds are descriptive. No class meets or misses the bar at this n. The limitation above applies.
  - The post-run audit found a sign of brief steering in D-042 (B-2), whose detections are counted here (section 11,
    finding 2). Without D-042, B-2 in W-1 is 8 of 9 attributable and 9 of 9 clean.
- **H-D3 (checklist effect: B-2 and B-3 pooled, declared attributable detection, W-1 against W-0): not demonstrated.**
  - All 17 pairs gave the same declared result in both arms: 14 declared detections in each arm, no discordant pair
    (b = 0, c = 0), exact one-sided McNemar p = 1.
  - **W-0 was already at a ceiling.** With 14 of 17 declared detections in W-0, at most 3 W-1-only discordant pairs were
    possible, and the smallest attainable p was 0.125. The test could not reach α = 0.05 on these pairs, whatever W-1
    did.
  - "Not demonstrated" does not mean "no effect" (section 6).
- **Clean-pass guard:** W-0 16 of 17, W-1 17 of 17 (W-0-only clean 0, W-1-only clean 1), p = 1, not significant.
- **Outcome table (I-D3), with Claude Opus 5.5 as world author (P-1 amendment 4).**
  - H-D1, H-D2 and H-D3 all read "fails", because "no verdict" is read as "fails" in this table.
  - The reading is the last row: neither class meets the bar, and no checklist effect is demonstrated.
  - The frozen miss labels (section 4.4):
    - label (b), the error's `minus` rate below the gate's flag threshold, for D-055 (B-2) and D-062 (B-3) in both
      arms;
    - no miss with label (a) or (d).
  - **Caution from the post-run audit (section 11, finding 1).** In these two pairs the structure statistic does not
    measure all that the error needs. The faulty `minus` counts are 0 or 1 of 200 in W-0 and W-1, against 149 (D-062)
    and 45 (D-055) in arm R. So label (b) here should not be read as "the structure was present".
- **Adoption (I-D2): the checklist is not proposed.** I-D2 needs at least one of H-D1 and H-D2 to hold, and H-D3 to hold.
  Neither condition is met.
- **Attrition: none.**
  - All 120 checks gave a certificate, with no timeout and no infrastructure failure.
  - No skeleton stayed invalid, and every part-B answer was "yes".
- **Overlap (section 1, P-7):**
  - 5 of the 20 pairs overlap a Phase B or C setting: B-2 2 of 10 (D-011, D-066); B-3 3 of 7 (D-008, D-040, D-067).
    No class has more than half.
  - Without them, H-D3 has 12 pairs with b = 0 and c = 0, p = 1 (`RESULTS_D_WITHOUT_OVERLAP.md`).

**Allowed claims** (REVISIONS-post-freeze P-1 amendment 3, replacing I-D6's sentences). Every detection and clean-pass
number above is "what Truth_Gate 0.5.1 did on pairs carrying errors documented in the literature, whose error made
the faulty criterion hold in at least a quarter of the samples of a reference world without the effect, built by an
agent told the error, and whose correction was clean there, with worlds declared by Claude Opus 5.5 — the same model
as the evaluation's designer, who wrote the pre-registration, the world instructions and the checklist, and of a line
that took part in writing the gate, but of a different line from the Claude Sonnet agents that wrote the briefs,
criteria and reference worlds — which was not told the error". For W-1 the sentence goes on: "but was given a
checklist naming the dependence kinds that B-2 and B-3 errors exploit (time order, grouped or repeated units, shared
components including common denominators and totals, many variables) and told to keep them in the `minus` world".

## 2. What was run

- **Gate.** Truth_Gate tag `v0.5.1` (commit `0aed4249f902`), full mode, default settings, one check at a time, from a
  clean worktree. Runner `run_phase_d.py` (SHA-256 `30fa161f…`), written after the case-freeze push.
- **Pre-flight.** Before the first check, the runner verified the three freezes and protocol rule 17: case-freeze
  commit `25bdbb2` is an ancestor of `origin/main`, and the freeze manifests are byte-equal in that commit. It also
  verified the worktree.
- **Checks.** 20 pairs: B-2 10, B-3 7, decoys 3 (B-1 1, B-6 2). For each pair, the faulty and the fixed twin were run in
  arms R (reference world), W-0 and W-1: 120 checks in 1303 s, the longest 114 s.
- **Freezes.**
  - `FREEZE_PREREG_D.json`: the pre-registration, pushed as `77e5c1d`.
  - `record/record/FREEZE_VALIDITY_MANIFEST.json` (validity), `FREEZE_CASES_D.json` (546 files) and
    `FREEZE_RECORD_D.json` (1805 files), pushed as `25bdbb2` before any gate run.
- **Transcripts.** Agent transcripts stay private; their SHA-256 are in `record/TRANSCRIPTS.md`.
- **Revisions after the freeze.** `REVISIONS-post-freeze.md` P-1 to P-7, summarised in section 8.

## 3. Hypotheses

### 3.1 H-D1 and H-D2 (arm W-1)

| Hypothesis | Class | n | Attributable | Clean pass | Lower bound, detection | Lower bound, clean pass | Awareness P / C / N | Verdict |
|---|---|---|---|---|---|---|---|---|
| H-D1 | B-2 | 10 | 9 | 10 | 0.6523 | 0.7871 | 1 / 1 / 8 | insufficient cases; minimum not met |
| H-D2 | B-3 | 7 | 6 | 7 | 0.5477 | 0.7212 | 2 / 5 / 0 | insufficient cases; minimum not met |

These results concern declared worlds that may contain what the error exploits. The limitation at the top of this
report applies.
- **Detection type, B-2:** of the 9 detections, 6 are generic and 9 declared (6 both).
- **Detection type, B-3:** of the 6 detections, 5 are generic and 5 declared (4 both).
- **D-023 (B-3)** is attributable only through the noise probe in both arms.
- **Without the overlapping pairs:**
  - B-2 W-1: 7 of 8 attributable, 8 of 8 clean.
  - B-3 W-1: 3 of 4 attributable, 4 of 4 clean.

### 3.2 H-D3 (W-1 against W-0, B-2 and B-3 pooled)

| Analysis | Pairs | W-1 declared | W-0 declared | b (W-1 only) | c (W-0 only) | p | Label |
|---|---|---|---|---|---|---|---|
| Comparable pairs | 17 | 14 | 14 | 0 | 0 | 1.0000 | not demonstrated |
| Sensitivity (not comparable counted as non-detections) | 17 | 14 | 14 | 0 | 0 | 1.0000 | not demonstrated |
| Without the overlapping pairs | 12 | 9 | 9 | 0 | 0 | 1.0000 | not demonstrated |

- No pair was "not comparable".
- Discordant counts per class: B-2 0 and 0; B-3 0 and 0.
- The three pairs without a declared detection are the same in both arms:
  - D-055 and D-062 are misses;
  - D-023 is detected only through the noise probe.
- Without D-042 (section 11, finding 2): 16 pairs, 13 and 13, b = c = 0.

### 3.3 Clean-pass guard and the adoption numbers (I-D2)

| Quantity | Value |
|---|---|
| Guard pairs | 17 |
| W-0 clean / W-1 clean | 16 / 17 |
| W-0 clean only / W-1 clean only | 0 / 1 |
| Guard p (W-0 better than W-1) | 1.0000 |
| Pooled W-1 minus W-0 clean difference | +1 |
| Decoys' clean pass W-0 / W-1 (n = 3) | 3 / 3 |

The guard conditions of I-D2 hold, but its first two conditions do not.

## 4. Per arm (descriptive)

### 4.1 Counts

| Arm | Class | n | Attributable (generic / declared) | PB-style | Clean | Clean without noise |
|---|---|---|---|---|---|---|
| R | B-2 | 10 | 10 (6 / 10) | 10 | 10 | 10 |
| R | B-3 | 7 | 7 (5 / 7) | 7 | 7 | 7 |
| R | decoys | 3 | 3 (0 / 3) | 3 | 3 | 3 |
| W-0 | B-2 | 10 | 9 (6 / 9) | 9 | 9 | 9 |
| W-0 | B-3 | 7 | 6 (5 / 5) | 6 | 7 | 7 |
| W-0 | decoys | 3 | 1 (0 / 1) | 2 | 3 | 3 |
| W-1 | B-2 | 10 | 9 (6 / 9) | 9 | 10 | 10 |
| W-1 | B-3 | 7 | 6 (5 / 5) | 6 | 7 | 7 |
| W-1 | decoys | 3 | 2 (0 / 2) | 3 | 3 | 3 |

- **Secondary scorings.** The draft-1 rule and the noise-only, declared-only and flag-everything baselines are in
  `RESULTS_D.md`. The tables without the overlapping pairs are in `RESULTS_D_WITHOUT_OVERLAP.md`.
- **Awareness, first reading resolved.**
  - W-0: B-2 P 5, C 3, N 2; B-3 P 4, C 1, N 2.
  - W-1: B-2 P 1, C 1, N 8; B-3 P 2, C 5, N 0.
- **Arm R (I-D4).** Every pair is attributable and passes clean in arm R, so there is nothing to list. The post-run
  audit answered (i) "yes" for all 20.

### 4.2 Decoys per arm and mechanism

| Pair | Class, tag | R | W-0 | W-1 |
|---|---|---|---|---|
| D-047 | B-1, extreme-group-change | attributable, clean | miss (b), clean | attributable, clean |
| D-052 | B-6, significant-here-not-there | attributable, clean | PB-detected, not attributable (c), clean | PB-detected, not attributable (c), clean |
| D-012 | B-6, units-not-independent | attributable, clean | attributable, clean | attributable, clean |

Three decoys allow no statement about the checklist's genericity (I-D2 calls the decoy condition a guard, not a test).

### 4.3 W-0 next to Phases B and C

This comparison is descriptive and not a test. The briefs, sizes, validity selection, pairs and world-author model all
differ:
- Phase B: a model of the gate's line;
- Phase C: Fable;
- Phase D: Claude Opus 5.5.

| Class | W-0 pairs | W-0 attributable | W-0 PB-style | W-0 clean | PB pairs / detections / clean (gate 0.4.0) | PC pairs / detections / clean (gate 0.5.0) |
|---|---|---|---|---|---|---|
| B-2 | 10 | 9 | 9 | 9 | 12 / 7 / 11 | 12 / 7 / 8 |
| B-3 | 7 | 6 | 6 | 7 | 12 / 8 / 8 | 10 / 8 / 8 |
| B-1 | 1 | 0 | 0 | 1 | 12 / 7 / 7 | 12 / 12 / 11 |
| B-6 | 2 | 1 | 2 | 2 | 12 / 11 / 11 | 12 / 10 / 12 |

Phase D's pairs had to pass V1 and V2 first (section 5), so the two sets of phases measure different populations.

### 4.4 Miss labels, clean-pass classes and structure statistics

- **Misses (frozen `miss_label.py`):**
  - W-0: D-055 (B-2) b, D-062 (B-3) b, D-047 (B-1) b, D-052 (B-6) c.
  - W-1: D-055 b, D-062 b, D-052 c.
  - No (a), (d) or (e).
- **What the statistic measures in D-062 and D-055** (post-run audit, verified by the designer from the files).
  - **D-062.** The structure statistic is Pearson's approximation from the coefficients of variation. It does not
    register the scaling of the bones with body length that the W-0 skeleton builds
    (`femur = rf * body + …`). The faulty `minus` count is 0 of 200 in W-0 and 1 of 200 in W-1, against 149 in R.
  - **D-055.** The statistic measures the predictors' autocorrelation only, not the persistence of the outcome. The
    faulty `minus` count is 0 and 1 of 200, against 45 in R.
- **Failed clean passes (frozen `clean_pass_class.py`):** one, D-035 (B-2) in W-0, class 3 (fixed weak in `plus`). The
  post-run audit traced it to the skeleton (low power in `plus`). There were none in W-1 or R.
- **Structure statistic** (share of 200 `minus` samples at or beyond the half-way point; 5 B-2 statistics are set by the
  brief and not measured):
  - R: every measured pair at or above 0.5.
  - W-0: below 0.5 only D-012 (0.015) and D-052 (0.155).
  - W-1: below 0.5 only D-068 (0.000) and D-052 (0.155).
  - D-068 W-1 and D-012 W-0 are attributable all the same, which again shows that the statistic is only a partial
    measure of what the error exploits.

## 5. Validity selection (I-D1)

The 72 built pairs were checked as follows (`record/validity/FREEZE_VALIDITY.json`):

| Class | Built | Passed | Dropped | Labels of the drops |
|---|---|---|---|---|
| B-1 | 6 | 1 | 5 | V2 5 |
| B-2 | 30 | 11 | 19 | V2 11, V1a 3, V1b 2, reference rejected by `check_skeletons_d` 2, timing infeasible 1 |
| B-3 | 30 | 8 | 22 | V2 12, V1a 6, V1b 3, fidelity A (h) 1 |
| B-6 | 6 | 2 | 4 | V1b 2, V2 1, fidelity A (h) 1 |

- **Unused reserves.** Two passed reserves (D-026, D-070) were not used, because no main pair of their subtype or tag
  dropped.
- **V1 by subtype and tag.**
  - V1a: B-2 L3.1 1, B-2 L3.2 2; B-3 change-vs-baseline 1, ratio-shared-denominator 1, ratio-vs-denominator-proxy 3,
    shared-measured-component 1.
  - V1b: B-2 L1.3 1, B-2 L3.2 1; B-3 ratio-vs-denominator-proxy 2, shared-measured-component 1; B-6 2.
- **Reading 1 (I-D1).** The V1a rate, 9 of 72 built pairs, estimates how often a documented error, as these agents built
  it at these sizes, changes no decision.
- **Reading 2 (I-D1).** An outcome-level check that cannot see an inflation below the threshold has a tool limit.
- **V1b** pairs are excluded by design: 7.
- **V2** is the largest cause of drops (29). Section 2.3's V2 requires three things of the fixed twin:
  - it holds in at most 0.065 of 1000 reference `minus` samples;
  - it holds in at most 0.065 of 1000 noise-probe samples;
  - it holds in at least 0.70 of 1000 reference `plus` samples.
- **Change-vs-baseline pairs.** All 9 dropped (V2 7, V1a 1, fidelity A (h) 1). The designer's reading of their
  noise-probe failures, not a test: on pure noise, a change-from-baseline claim shows regression to the mean, which the
  corrected criterion also counts as change.
- **The shortfall.** The drops left both classes below 16 pairs and below their subtype minima. The author chose on
  2026-11-18 to continue as pre-registered, knowing this (decision register).

## 6. Awareness of the world authors (descriptive)

- **Readers (REVISIONS P-6 and its addendum).**
  - The designer knew the arms, so the designer did not read.
  - The first reading was made by two fresh Sonnet-line readers on `WORLD_LOG.md` only. The entries came in one
    shuffled set, without arm or batch labels.
  - Reader r1 did not count an entry's general notes, against its prompt. Before any tally, it was replaced once by a
    fresh reader, r1b, with the identical prompt and files. r1's reading is kept, excluded.
  - The second reading of W-1, with `CHECKLIST_LOG.md`, was made by two other fresh readers after the first was frozen.
  - A disagreement resolves to the higher level.

| Reading | Arm | P | C | N |
|---|---|---|---|---|
| first | W-0 (20) | 11 | 4 | 5 |
| first | W-1 (20) | 4 | 6 | 10 |
| second (with `CHECKLIST_LOG.md`) | W-1 (20) | 11 | 8 | 1 |

- **Second reading per class:** B-2 P 4, C 5, N 1; B-3 P 4, C 3, N 0.
- **What the first reading shows.** It sees fewer planted mechanisms in W-1's world logs. The W-1 instructions sent the
  dependence answers to a separate log, which the first reading does not see. With that log added, W-1 is mostly P
  or C.
- **No interpretation.** The levels are descriptive. Detection by level is in `RESULTS_D.md`.

## 7. Roles and models

| Role | Model (from the transcripts) |
|---|---|
| Designer (pre-registration, instructions, checklist, checks, this report) | Claude Opus 5.5 (`claude-opus-5-5`) |
| World authors, W-0 and W-1 (4 valid batches; 2 stopped, 1 invalid) | Claude Opus 5.5 (`claude-opus-5-5`), effort `xhigh`, harness 2.1.326 |
| Brief, criterion and structure authors | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Fidelity auditors, parts A0, A and B | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Awareness readers (r1, r1b, r2, r3, r4) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Designer's coding agents (runner, scoring, recomputation, checks) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Post-run auditor (independent session, fresh agent) | Claude Opus 5.5 (`claude-opus-5-5`) |

## 8. Events and revisions after the freeze (`REVISIONS-post-freeze.md`)

- **P-1.** The world-author model is Claude Opus 5.5 by the author's decision, because Fable needed paid credits.
  - The revision was reviewed in the independent session.
  - 13 amendments followed, among them the frozen launch prompt, a provenance check, the claim wording and the
    same-model limitation.
- **P-2.** The session scratchpad is kept empty before each agent. A statistic set by the brief takes its value at the
  brief's sizes.
- **P-3.** The check script's `sizes` adapter, as in Phase C. D-014 and D-041 were dropped, because their briefs need
  NaN. Guard questions were left to fidelity A (d).
- **P-4.** The batch check got a decoded term scan with a pre-flight baseline, and provenance by replay
  (`designer/world_run_check_v2.py`). The trigger was one stopped batch whose check showed two defects in the check
  itself; no valid batch existed yet.
- **P-5.** One timing log line was lost to a concurrent append (D-052 W1). That timing run was repeated with one
  process, and every log-writing run is now sequential.
- **P-6 and addendum.** The awareness readers, including the replacement of r1 (section 6).
- **P-7.** The overlap marking was made after the run, mechanically from frozen inputs (section 1).
- **World-author runs** (`record/work/WORLD_RUN.md`):
  - Batch 1 W-0 stopped twice: once on the API usage limit, once on a connection error.
  - Batch 2 W-1's first agent was invalid. It made two forbidden tool calls (a ToolSearch for `TaskStop`, then
    `TaskStop` on its own background command) and read its own background-task file outside the sandbox.
  - Each went to a fresh agent in a new sandbox, under the frozen prompt.
  - No exception to a mechanical rule was made.
- **The author's decisions during execution:**
  - "Plana göre devam": continue although both classes fell below 16;
  - "xhigh ile devam et": keep effort `xhigh` for the world authors;
  - the approval of the case-freeze push.

## 9. Recomputation

- **The designer's separate script.** `recompute/recompute_designer_d.py` was written from the rule text, without
  reading the scoring script or the frozen attribution tool. It recomputed every certificate-based number.
- **Agreement.** 1158 items were compared: 720 pair-and-arm decisions, 143 stream counts with Fisher p, 255 table
  numbers, and the H-D1, H-D2, H-D3, guard and adoption inputs. There were 0 disagreements (`recompute/COMPARE_D.md`).
- **The pre-freeze check agrees.** The independent attribution recomputation written before the freeze
  (`recompute_d/round4`) gives the same 60 pair-and-arm outputs.
- **One definition was not spelled out.** The text does not define "clean pass without the noise stream" exactly. The
  recomputation's reading gave the same cells as the scoring.

## 10. Limitations

> "The world author is the designer's own model (Claude Opus 5.5). It was a fresh agent, not told the error, the class
> or the source, but it may share the designer's idea of realistic dependence and of the checklist's terms, which can
> favour detection and the checklist effect."

- **n far below plan.** The validity checks left 10 and 7 pairs, and both classes miss their subtype minima. The
  intervals are wide, and H-D1 and H-D2 have no verdict. B-3 rests mostly on one tag (5 of 7 ratio-shared-denominator).
- **H-D3 met a ceiling in W-0.** With 14 of 17 declared detections in W-0, the smallest attainable p was 0.125. On
  these pairs the design could not show a checklist effect on declared detection.
- **The structure statistic is a partial measure.** In D-055 and D-062 it reports the structure as present, while the
  worlds lack part of what the error needs. In D-068 it reads 0.000 for a detected pair (section 4.4).
- **D-042's brief steered both world authors** (post-run audit, (iii)). Under section 7 the case stays in the table.
- **Reference worlds.** They were written by agents told the error (I-D7), so arm R is a consistency check only.
- **Model lines.** The authors of the briefs, criteria and reference worlds, and the auditors and readers, are Sonnet
  5.5. The world authors, the designer and the post-run auditor are Opus 5.5.
- **What the claims cover.** Every number describes Truth_Gate 0.5.1 on these frozen pairs and worlds only.

## 11. Blind post-run audit (independent session)

- **The audit.** A fresh Claude Opus 5.5 agent in the independent session made it, from a task folder of copies
  (`postrun/POSTRUN_AUDIT_INSTRUCTIONS_D.md`). It was withheld the designer's recomputation, run log and notes.
  - Part 1: per pair and arm, PC §7's questions (i)–(iii), from the certificates, cases, skeletons and logs.
  - Part 2: this report's draft and the scoring output, opened only after part 1 was written.
- **The designer's checks of the audit.**
  - The transcript is Opus only, with no forbidden tool, no path outside the task folder and no URL.
  - The task folder's inputs are unchanged (manifest).
  - The part-2 files were first read after both part-1 files were written, and the part-1 files were not touched
    afterwards.
- **Part 1.**
  - (i) "yes" for every detected pair-arm: R 20, W-0 17, W-1 18.
  - (ii) one failed clean pass, D-035 W-0, traced to the skeleton.
  - (iii) "yes" only for D-042, in W-0 and W-1.
- **Part 2.** Every table number equals the scoring output and the auditor's own recount from the 120 certificates.
  The ten statements it found unsupported, and the omission, were handled as follows (the draft's wording was replaced):

| # | Finding | Handling |
|---|---|---|
| 1 | Label (b) for D-055 and D-062 suggests the structure was present; the statistic does not measure what the error needs there | Verified (counts 0–1 of 200 in W-0/W-1 against 149 and 45 in R; the D-062 W-0 skeleton scales the bones with body length). Caution added in sections 1, 4.4 and 10. The labels stay as the frozen tool gave them. |
| 2 | D-042's detections rest on duplicates that the brief's wording steered | Verified (the brief's "compound record", "records" and "new compounds"). Notes and numbers without D-042 added in sections 1, 3.2 and 10. The case stays (section 7). |
| 3 | "Minimum not met" missing | Added: both classes miss their subtype minima (sections 1, 3.1, 10). |
| 4 | "No information" / "any size" wording; the limit is W-0's ceiling | Replaced by the ceiling statement (smallest attainable p 0.125). |
| 5 | V2 described incompletely | Replaced by section 2.3's three conditions (section 5). |
| 6 | r1's replacement is not in the revision log | Recorded as the P-6 addendum. r1's reading is in the record. |
| 7 | One forbidden call named, two recorded | Corrected (section 8). |
| 8 | Awareness shares and PC's wording missing from the class statements | Added (sections 1 and 3.1, and the top of the report). |
| 9 | The fixed limitation sentence not printed in section 10 or next to the verdicts | Printed at the top, in section 3.1 by reference and in section 10. |
| 10 | The I-D3 reading lacks "with Claude Opus 5.5 as world author" | Added (section 1). |
| — | No overlap marking and no tables without overlapping pairs | Marking made after the run, mechanically from frozen inputs (P-7). Tables without overlap added (sections 1, 3). |
