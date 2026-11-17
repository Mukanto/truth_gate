# Phase D: leakage and coupling errors with validated pairs — pre-registration (DRAFT 2)

## Status

- **Draft 2, 2026-11-17, not frozen.** Designer: Claude, under the author's delegation.
- Draft 1 had one blind review (review 1: 2 blocking, 15 major, 7 minor). Every finding is addressed;
  `REVISIONS_D.md` maps each one to its change.
- "PB" is `evaluation/phase_b/PREREG_PHASE_B.md` and "PC" is `evaluation/phase_c/PREREG_PHASE_C.md`. "As PC §n" means
  the rule applies unchanged.
- No Phase D case exists when this text is written.

**Frozen with this text** (`FREEZE_PREREG_D.json`):
- this file and `REVISIONS_D.md`;
- `ALLOCATION_D.json` and `SOURCES_D.md`;
- the instruction files `BRIEF_AUTHOR_D.md`, `CRITERION_AUTHOR_D.md`, `STRUCTURE_AUTHOR_D.md`, `WORLD_INSTRUCTIONS_D0.md`,
  `WORLD_INSTRUCTIONS_D1.md`, `FIDELITY_AUDIT_D.md` and `AWARENESS_RULE_D.md`;
- the scripts `tools/validity_check.py`, `tools/structure_stat.py`, `tools/attributable.py`, `tools/assemble.py`,
  `tools/check_skeletons_d.py`, `tools/term_check.py`, `tools/scan_docs.py` and `tools/shuffle.py`, with their
  tests.

After the freeze nothing above changes; process events go to `REVISIONS-post-freeze.md`.

## 0. Why Phase D, and its questions

### 0.1 What Phases B and C measured

B-2 (procedure-level leakage) and B-3 (coupling by construction) failed the bar in both phases. The bar is a one-sided
95% Wilson lower bound of at least 0.6 for both detection and clean pass.

| Class | Phase B (detections / clean passes of n) | Phase C (detections / clean passes of n) |
|---|---|---|
| B-2 | 7 / 11 of 12 | 7 / 8 of 12 |
| B-3 | 8 / 8 of 12 | 8 / 8 of 10 |

### 0.2 What those verdicts mix

The reports and their post-run audits point to three things:

- **D-1.** Several misses have a faulty criterion that fails in `minus` at about the nominal rate. Either the declared
  worlds held too little of what the error exploits, or the error raised the statistic without crossing the claim's
  threshold at the brief's size.
- **D-2.** Several fixed twins were not clean tests of the claim on the declared worlds: a threshold without a test at a
  small size, an ordinary test on autocorrelated data, or a correction that changes the estimand.
- **D-3.** In Phase C, six detections would also occur with the fixed criterion.

A post hoc validity audit (`evaluation/validity_audit_b2b3/`) is consistent with D-1 to D-3. Its categories were set
after the results, and each phase had one reader.
- Of 16 misses: 10 are attributed to the worlds, 4 to size, 1 to the tool, and 1 to mixed causes. The tool case has the
  same sub-threshold mechanism as the 4 size cases.
- Of 11 failed clean passes: 9 are attributed to the fixed criterion and 2 to mixed causes.

The B and C verdicts therefore mix:
- the gate's behaviour;
- whether the world author put in the structure;
- whether each pair was valid.

Phase D checks each pair's validity before any gate run (section 2). It scores only detections that the error explains
(section 5). It measures the structure in every declared world (section 5).

### 0.3 Questions

- **Main (confirmatory, H-D1 for B-2, H-D2 for B-3).** Consider pairs that are valid by the pre-run checks of section 2,
  with worlds declared by a world author who is not told the error, the class or the source but is given the
  dependence checklist of section 4 (arm W-1). Does the system of Truth_Gate 0.5.1 and that world author flag the
  faulty criterion with a detection attributable to the error, and pass the fixed criterion? Two shares are reported
  separately:
  - the share of attributable detections that needs no declared world (the noise probe);
  - the share that the declared streams carry.
- **Arm comparison (confirmatory, H-D3).** Does the checklist raise attributable detection on the declared streams,
  against the same world-author model without it (arm W-0, PC's instructions)?
- **Descriptive.**
  - Arm R: the gate on the reference worlds, as a consistency check.
  - The decoy pairs (section 1) in both arms, to show the checklist's cost outside its target classes.
  - Phase B/C-style scoring.
  - Validity drop rates by subtype and tag, with their causes.
  - The structure statistics and the miss labels.
  - Awareness readings.

## 1. Classes, subtypes, tags, sources, decoys, reserve

- **B-2**, 20 pairs. Subtypes as PC §1 (L1.1, L1.2, L1.3, L1.4, L3.1, L3.2), allocated 4, 4, 3, 3, 3, 3.
- **B-3**, 20 pairs, tagged with PC's closed `mechanism_tag` list for B-3, with its definitions and precedence
  (`AUTHOR_PHASE1_C.md`). The allocation is 5 pairs each for `ratio-shared-denominator`, `ratio-vs-denominator-proxy`,
  `change-vs-baseline` and `shared-measured-component`. `target-from-labels` is not allocated. Because the tags are PC's,
  the overlap key applies directly.
- **Decoys**, 8 pairs (4 B-1, 4 B-6). They are written and validated like the others (section 2; a structure statistic
  is not required) and go to both world-author arms. They are reported descriptively, as a check of the checklist's
  cost, and are excluded from H-D1 to H-D3.
- **Sources** as PC §1, with the caps scaled to 20 pairs:
  - at most 6 pairs per source per class (KAP23 at most 10 B-2 pairs);
  - at least 4 independent read sources per class;
  - within a class, every pair differs from every other as PB §4.

  The sources are listed in `SOURCES_D.md` before any brief.
- **Overlap**, as PC §1. A pair overlaps a Phase B or C pair when source, mechanism tag and statistic family agree; the
  designer marks it mechanically after the briefs.
  - To keep overlap low, each brief author receives the (mechanism tag, statistic family) combinations that Phases B and
    C used for its sources, without any case content, and prefers other statistic families where the source allows.
  - If strictly more than half of a class's pairs overlap, the report says that the class result "largely repeats Phase
    B and C settings".
  - Every table is also given without the overlapping pairs.
  - The allocation is in `ALLOCATION_D.json`. B-2 half A rests on KAP23 (10 pairs). Half B rests on SIM03, SAN18,
    AMB02, VAR06, ROB17 and SAE17. B-3 rests on PEA97, ARC81, TU07, ATC76, KRO93, CUR13 and BLO77. The new sources
    are SAN18, SAE17, ROB17, TU07, ATC76 and BLO77; they are verified in `SOURCES_D.md` before the freeze.
- **Reserve.** 10 reserve slots per class and 2 per decoy class, drawn in a fixed order within the same subtype (B-2),
  tag (B-3) or class (decoys). A class whose subtype or tag minimum cannot be met is reported as such.

## 2. The case, the reference world, and validity (all before any world author starts)

### 2.1 The case

As PC §2 (one criterion, the imports, the allowed guards, the estimand rule, what a brief may state, the banned terms),
with these changes:

- **Sizes.** At most 2000 units along any axis and at most 2 000 000 values in any array. The timing limit is 30 minutes
  per check, by PB §2's formula, measured in every arm (section 3 item 9).
- **Model.** Where the source names a model family, both twins use it. Otherwise the private note names the family and
  the reason. The model never changes after the brief.
- **Criteria are bodies.** Each twin is a file holding helper functions and one `criterion(d)`, written against the
  brief's keys. `tools/assemble.py` splices it into the R, W-0 and W-1 skeletons in place of PC's placeholder
  criterion.
- **The private note adds:**
  - the exploited structure, in one sentence;
  - a **structure statistic**, a function of the brief's data keys only, with its direction and null value;
  - its value in the source's setting, with a quote, or "source states none" and a proposed value with its reason.

  A statistic that is fixed by the brief's sizes (for example a number of features) is marked "set by the brief".

### 2.2 The reference world (arm R)

- **Who writes it.** A fresh structure author (Sonnet line, as PC's criterion authors) writes `reference.py`. It reads
  only what `STRUCTURE_AUTHOR_D.md` lists:
  - the brief and the private note;
  - the source passage;
  - PC's fixed rule for `minus`;
  - its instructions.
- **What it may not do.** It does not see the criteria. It runs no analysis that could serve as a criterion. It may
  check shapes and the structure statistic.
- **What it writes.**
  - a `plus` world (claim true) and a `minus` world (claim false), each with the structure at the note's value;
  - at least one control, under PC's world-instruction rule 4;
  - exactly the brief's keys, shapes and dtypes.
- **Mechanical checks, before V1** (`tools/validity_check.py`):
  - `structure_stat` on 200 `plus` and 200 `minus` samples lies within ±20% of the note's value in both worlds, and is
    equal between the two worlds within sampling error;
  - the gate's `minus_check` record shows that `minus` changes keys the fixed criterion reads.

### 2.3 Validity checks

The **designer** runs `tools/validity_check.py`. Its samples come from seed 20261117 (not `Budget.base_seed`), on
streams the gate never uses: `validity:minus`, `validity:plus` and `validity:noise` for V1 and V2, and
`structure:plus` and `structure:minus` for the structure statistic. Nobody computes a gate stream of a Phase D file
before the case freeze.

Every run is appended to `validity_log.jsonl`: the SHA-256 of the inputs, the seeds and the counts. A run missing from
the log is a protocol breach.

- **V1, the error manifests.** On 1000 reference `minus` samples:
  - the faulty criterion holds in at least 0.25;
  - and more often than the fixed criterion, with a one-sided Fisher exact p below 0.01.

  A V1 failure is labelled by the faulty rate:
  - **V1a** "error does not change decisions at this size": the faulty rate is below `kstar/200`. `kstar` is the
    smallest count of 200 that the gate would flag for that study: the smallest k with
    `wilson_lower(k, 200, alpha_family/(2m)) > size`, where m is the gate's `count_comparisons` for the study;
  - **V1b** "manifests below the V1 bar (excluded by design)": every other V1 failure.
- **V2, the fixed criterion is clean.** It holds in:
  - at most 0.065 of 1000 reference `minus` samples;
  - at most 0.065 of 1000 noise-probe samples;
  - at least 0.70 of 1000 reference `plus` samples.
- **V3, single difference.** The two bodies are compared line by line against the mapping in `CASE.md`.
  `tools/assemble.py` confirms, for every arm, that the assembled faulty and fixed study files differ only inside the
  criterion body. Fidelity audit part A confirms that the difference is the documented error.
- **Structure statistic.** `structure_stat` must be computable on the reference worlds. A statistic that cannot be
  computed makes the pair invalid.

### 2.4 Repair and drop (decision table, applied by the designer)

| Failure | Action |
|---|---|
| V1 | Raise the size once, to the smaller of the source's size and the cap. If it is already there, drop the pair. |
| V2 | Drop. |
| V3 or a mechanical check of 2.2 | One repair of the criterion bodies or of `reference.py` by the same author; then drop. |
| Fidelity part A "no" | One repair by the same author; then drop. |

A repair never changes:
- the claim, its statistic, its threshold or the model;
- the brief (briefs are never rewritten).

Dropped pairs are replaced from the reserve; the reserve pair goes through the same checks. Every run, repair, drop and
substitution is frozen in `FREEZE_VALIDITY.json` before any world author starts. The drop rates by subtype, tag and
label (V1a, V1b, V2, V3, fidelity) are reported.

## 3. Roles and order of work

Each role has a frozen instruction file that states exactly what it reads. Only the designer and the fidelity auditor
read this document. A role sees the rules of sections 2.3 and 2.4 only where its instruction file quotes them.

0. **Start conditions** (before any agent sees anything), as PC §4 item 0, from tag `v0.5.1`, used throughout (agent
   documents, `pkg/`, `validity_check.py`, the run).
   - The designer records that `truth_gate/` and `kapi/` differ between `v0.5.0` and `v0.5.1` only in:
     - `external.py` (R-28: which path starts a `command` program);
     - the version strings.
     Neither touches the engine, the probes or the statistics.
   - **The document set** excludes everything that reports Phase B, Phase C or the validity audit:
     `evaluation/validity_audit_b2b3/`, the reports, `docs/EVALUATION.md`, `CHANGELOG.md`, and every README sentence on
     results.
   - **The scan list** adds "validity audit", "case-world", "case-size", "case-fixed", "sub-threshold", "attributable",
     and the subtype and mechanism-tag names.
   - **Sandbox.** Every agent works in a sandbox folder holding copies of its allowed files only.
     - It fetches nothing from the project's repository or its published evaluation material, and logs every URL it
       reads; the designer checks each URL log against the repository's host and paths.
     - No context-mode indexing or cross-agent search: no `ctx_index`, no `ctx_batch_execute`, and `ctx_search` only
       with a source filter naming the agent's own labels.
     - No session scratchpad.
     - Every transcript is checked for these points with the designer's transcript tools.
1. **Allocation.** The designer fixes `ALLOCATION_D.json` (subtypes, tags, decoys, reserve order, tag-to-PC map) and
   `SOURCES_D.md`.
2. **Brief authors** (Sonnet line, `BRIEF_AUTHOR_D.md`) read the sources and write the briefs and private notes:
   - two fresh agents per class, each writing half of the class's pairs and reserves, from disjoint source lists fixed in
     `ALLOCATION_D.json`;
   - one fresh agent for the decoys.

   `tools/term_check.py`, the "what a brief may state" check and a designer check of the within-class difference rule
   across both halves follow, as PC.
3. **Criterion authors** (`CRITERION_AUTHOR_D.md`) write the two bodies from the briefs, the private notes and the
   sources. There is one fresh agent per class half (Sonnet line), and none of them wrote briefs. They never run the
   faulty body.
4. **Structure authors** (`STRUCTURE_AUTHOR_D.md`) write `reference.py` for the pairs of one class half (section 2.2).
   There is one fresh agent per class half (Sonnet line), distinct from that half's criterion author.
5. **Validity**, by the designer (sections 2.3 and 2.4).
6. **Fidelity audit part A** (a fresh agent; `FIDELITY_AUDIT_D.md`). Before any world author, it checks:
   - the mapping to the source, the single difference, the estimand line and the brief rules;
   - the validity log;
   - the reference world: `minus` sets only the claim's quantity to null; no key or dependence is read only by the
     faulty criterion unless the documented error needs it; the stated structure value matches its quote, or, when the
     source states none, the proposed value is justified (the auditor approves it).

   Repair and replacement follow section 2.4.
7. **Freeze of validity** (`FREEZE_VALIDITY.json`).
8. **World authors**, arms W-0 and W-1. Each writes the worlds and controls from the brief only (claim, data keys,
   sizes).
   - Both arms get PC's world instructions with the size limits of section 2.1 in place of rules 6 and 8. W-1 also gets
     the checklist of section 4.
   - The private files are `WORLD_INSTRUCTIONS_D0.md` and `WORLD_INSTRUCTIONS_D1.md`, and each is given to its agents as
     `WORLD_INSTRUCTIONS_D.md`. They differ only in the checklist section and its two rows in the difference table.
     Neither names the arms or the other file; the difference is recorded here.
   - The agents are fresh, of PC's world-author line (Fable), and disjoint between arms.
   - There is one shuffle of all briefs, decoys included. Batch k of W-0 and batch k of W-1 hold the same briefs in the
     same order, and the batches of the two arms alternate in time.
   - PC §4 item 3 (identification, invalid batch, stops) applies to every world-author agent. A redo in one arm is
     logged next to its counterpart.
   - `tools/check_skeletons_d.py` checks every skeleton: keys, shapes, dtypes and the section 2.1 limits.
9. **Timing per arm.** After the skeleton check, t and g are measured in each arm with PB §2's formula. A skeleton whose
   estimate is above 30 minutes goes back once to a fresh agent of that arm.
10. **Fidelity audit part B** (after item 8): no world file leaks the error. There is no replacement; a "no" counts as in
    section 6, "Attrition".
11. **Case freeze and public push** with the author's approval, as PC §5. The runner refuses to start unless the freeze
    verifies and the named public commit holds it (protocol rule 17).
12. **Run** (section 5). Then the designer's recomputation and a blind post-run audit in the independent session
    (section 7).

**Compute budget.** The estimate sums the per-check timing estimates over 288 checks: 48 pairs × 2 twins × 3 arms. If
it exceeds 72 hours, arm R is run last and may be cut, since it is descriptive. The cut is logged.

Pre-freeze review: round 2 reviews this draft with the instruction files and the tools; round 3 is a targeted look at
the fixes.

## 4. The checklist of arm W-1 (fixed text)

> Before you write the worlds, list for each data key how the units in a real dataset of this kind can depend on each
> other:
> - order in time;
> - groups, sites, or repeated measurements of the same unit;
> - components shared between variables (a common factor, a common total, a common denominator, a common measurement);
> - many variables relative to the number of units.
>
> Give each dependence a realistic size and say where the size comes from. Keep every dependence in **both** the `plus`
> and the `minus` world: only the claimed effect differs between them. Write this list in `CHECKLIST_LOG.md`, not in
> `WORLD_LOG.md`.

The checklist names the kinds of dependence that B-2 and B-3 errors exploit, and tells the world author to keep them in
`minus`. It is given for every brief of arm W-1, decoys included. The claims wording of section 8 names it.

## 5. Run and scoring

- **Run.** Truth_Gate at tag `v0.5.1`, full mode, default settings, one check at a time. For every pair, both twins run
  in arm R (the reference worlds), arm W-0 and arm W-1. Infrastructure failures are handled as PC §6.
- **Expected flags** as PC §6. They are enumerated per pair and per arm at the case freeze (`EXPECTED_FLAGS_D.json`).
- **Rate flags and their streams:**

  | Flag | Stream |
  |---|---|
  | `K2_HIGH_SIZE`, `K2_FAILS_UNREACHABLE` | `world:minus` |
  | `K4_CONTROL_ALSO_HOLDS`, `HIGH_RATE:control:<id>` | any listed control stream |
  | `K5_HOLDS_ON_NOISE`, `HIGH_RATE:probe:noise` | `probe:noise` |
  | `K5_HOLDS_ON_NULL`, `HIGH_RATE:world:null` | `world:null` |
  | `K5_HOLDS_ON_SHUFFLE`, `HIGH_RATE:probe:shuffle:*` | the shuffle streams |

  `K2_NO_SEPARATION` alone is not a rate flag.
- **Attributable detection** of a pair in an arm (`tools/attributable.py`). The faulty study's verdict is
  NOT_FALSIFIABLE, and at least one of its expected rate flags, on a stream s, meets both conditions:
  - **(a)** the fixed study of the same arm carries no rate flag on s;
  - **(b)** the faulty count on s exceeds the fixed count, with a one-sided Fisher exact p < 0.05.

  If the fixed study has no counts for s (a load error or a hard UNDEFINED), the detection is not attributable through
  s, and it is listed.

  The twins share seeds, so their counts on a stream come from the same samples. The certificates hold only counts, so
  a paired test is not available. Fisher's test treats the counts as independent, which is conservative here.
- **Generic and declared.** An attributable detection is **generic** if `probe:noise` is among its qualifying streams,
  and **declared** if a qualifying stream other than `probe:noise` exists. A detection can be both. The noise probe
  draws N(0, 1) and Bernoulli arrays from the brief's keys, shapes and dtypes, so its distribution is the same in every
  arm.
- **Secondary scorings**, per arm, reported next to the primary:
  - PB-style detection (PB §6);
  - the draft-1 rule (a 20-count margin and Fisher);
  - the noise-only and declared-only baselines (PB §6).
- **Clean pass** as PB §6. Every failed clean pass is classified mechanically from the certificate:
  - **"fixed not clean in these worlds (correct flag)"**: the flagged stream's rate is above the flag threshold, and its
    95% Wilson interval excludes the declared size;
  - **"possible false alarm"**: the interval includes the declared size.
- **Structure in the declared worlds.** For each pair and arm, `tools/structure_stat.py` computes the statistic on 200
  `minus` samples, drawn from the disjoint seed stream. It reports the mean, and the share of samples at or beyond the
  half-way point `null_value + 0.5·(note_value − null_value)` in the stated direction. A statistic "set by the brief" gets no world label. Each miss gets one
  label:
  - **(a)** share below 0.5: "declared worlds lack the structure";
  - **(b)** structure present, and the faulty `minus` count at or below the flag threshold: "structure present, error
    did not change decisions in these worlds";
  - **(c)** faulty study flagged, but the detection is not attributable: "flagged, not attributable";
  - **(d)** faulty `minus` count above the flag threshold, but no flag: "gate".
- **Fixture of `attributable.py`.** On the Phase C certificates (0.5.0), the rule gives, as computed by the designer
  (`fixture_attributable_pc_output.txt`):

  | | Attributable | Not attributable |
  |---|---|---|
  | B-2 | B2-01, B2-02, B2-12 | B2-08, B2-09, B2-10, B2-11 |
  | B-3 | B3-01, B3-05, B3-06, B3-08, B3-09, B3-11; B3-04 (through `probe:noise` only) | B3-12 |

  The tool must reproduce this list. Under the declared-stream score of H-D3, B3-04 and B3-05 are not attributable.

## 6. Hypotheses, thresholds, power, attrition

- **H-D1 (B-2) and H-D2 (B-3), arm W-1.** Each class needs both of these, at the actual n:
  - the one-sided 95% Wilson lower bound of attributable detection is at least 0.6;
  - the same bound for clean pass is at least 0.6.

  That is 16 of 20, 15 of 19 or 18, 14 of 17, or 13 of 16. A class with fewer than 16 pairs is "insufficient cases" and
  has no verdict.
- **H-D3 (arms W-1 against W-0, B-2 and B-3 pooled).** An exact one-sided McNemar test on **declared** attributable
  detection, α = 0.05.
  - It is a pooled claim and does not support a checklist effect within one class.
  - The discordant counts per class are reported descriptively.
- **Clean-pass guard** (for the adoption rule of section 8; not a hypothesis). An exact one-sided McNemar test on clean
  pass, in the direction W-0 better than W-1.
- **Power.**
  - **H-D1 and H-D2.** With true rates p on both measures and n = 20:

    | p | Joint power |
    |---|---|
    | 0.80 | 0.40 |
    | 0.85 | 0.69 |
    | 0.90 | 0.92 |

    The planning value is 0.85, and it is argued, not given. In Phases B and C, the pairs the audit judged adequate gave
    21 of 22 PB-style detections and 22 of 22 clean passes, with worlds that happened to contain the structure. W-1
    worlds may not contain it, and the attributable rule is stricter. A FAILS at n = 20 is therefore compatible with a
    true rate of 0.80, and the intervals are the result.
  - **H-D3.** The power depends on the share s of pairs whose declared attribution is the same in both arms.

    | Discordant (W-1 only / W-0 only) | s = 0 | s = 0.3 | s = 0.5 |
    |---|---|---|---|
    | 0.25 / 0.05 | 0.69 | 0.49 | 0.31 |
    | 0.30 / 0.02 | 0.96 | 0.83 | 0.61 |

    The values are simulated (40 000 runs). The discordant rates among the non-fixed pairs are scaled by 1 − s.

    A non-significant H-D3 reads "not demonstrated", never "no effect".
- **Attrition.** These count as a miss and a failed clean pass in that arm, for H-D1 and H-D2 (intention to treat):
  - a skeleton that stays invalid;
  - a part-B "no";
  - a timeout;
  - a load error.

  For H-D3, a pair missing in one arm is "not comparable" and excluded; the exclusions are listed. H-D3 uses every pair
  that entered item 8 in both arms.
- **Descriptive.**
  - Arm W-0 with all scorings, against PB and PC. Briefs, sizes, validity and pairs differ, so this is not a test.
  - Arm R.
  - The decoys per arm.
  - The validity drop rates.
  - The structure statistics and the miss labels.
  - Awareness, as PC (P/C/N, two readers) on `WORLD_LOG.md` only, by readers who do not know the arm. A second reading
    for W-1 includes `CHECKLIST_LOG.md`.

## 7. After the run

As PC §7:
- the designer recomputes every number from the certificates with a separate script;
- a blind post-run audit is made by a fresh agent in the independent session;
- the thresholds, rules and expected flags never change after the run;
- a case found wrong after the run stays in the table, with the error reported next to it.

## 8. Interpretations fixed now

- **I-D1. V1 failures.** V1 failures are not evidence about the gate's detections or false alarms. They are reported by
  subtype and tag, with labels V1a and V1b.
  - **Reading 1.** The rate of V1a estimates how often a documented error, as built by these agents at these sizes,
    changes no decision. It describes the scope of any decision-level check.
  - **Reading 2.** This was the Phase B auditor's: an outcome-level check that cannot see an inflation below the
    threshold has a tool limit.
  - Both readings are reported. V1b pairs are excluded by design and counted.
- **I-D2. The single adoption rule.** The checklist is proposed for a later version of the methods protocol (with its
  own review) only if all of these hold:
  - H-D3 holds;
  - the clean-pass guard is not significant at 0.05;
  - the pooled W-1 minus W-0 clean-pass difference is at least −2 pairs;
  - the decoys' clean pass in W-1 is not lower than in W-0 by more than 1 pair.
- **I-D3. Outcome table** (H-D1, H-D2, H-D3):

  | H-D1 | H-D2 | H-D3 | Reading |
  |---|---|---|---|
  | holds | holds | holds | On valid pairs of both classes, the system with the checklist detects the error and passes the correction. The checklist raises declared detection. Adoption follows I-D2. |
  | holds | holds | fails | Both classes meet the bar with the checklist, but a checklist effect is not demonstrated: W-0 may do as well. Not adopted. |
  | holds | fails | holds | B-2 meets the bar with the checklist; B-3 does not. The pooled checklist effect is demonstrated, but not within a class. Adoption follows I-D2, with B-3 named as unresolved. |
  | fails | holds | holds | As the row above, with the classes exchanged. |
  | holds | fails | fails | B-2 meets the bar with the checklist; no effect demonstrated. Not adopted. |
  | fails | holds | fails | As the row above, with the classes exchanged. |
  | fails | fails | holds | The checklist raises declared detection, but neither class meets the bar. The world author's coverage, or the gate's flags at these sizes, still falls short; the miss labels of section 5 say which. Not adopted on this evidence alone. |
  | fails | fails | fails | Neither class meets the bar, and no checklist effect is demonstrated. The miss labels say whether the structure was missing (a), present without changing decisions (b), flagged without attribution (c), or present and unflagged (d, a gate finding). |

  "Insufficient cases" in a class replaces that class's entry with "no verdict".
- **I-D4. Arm R** is a consistency check: V1 and V2 select pairs in the reference worlds, with other seeds. A pair that
  passes V1 and V2 but is not attributable in arm R, or fails clean pass there, is listed and explained. It is not a
  ceiling.
- **I-D5. A clean pass in W-1 below W-0.** If W-1's clean pass falls below W-0's, the checklist adds dependence that the
  documented corrections do not handle. That is a limit of the checklist, not of the gate. The mechanical
  classification of section 5 separates correct flags from possible false alarms.
- **I-D6. Allowed claims.**
  - **W-1:** "what Truth_Gate 0.5.1 did on validated pairs carrying errors documented in the literature, with worlds
    declared by a model of a different Claude line that was not told the error, but was given a checklist naming the
    dependence kinds that B-2 and B-3 errors exploit (time order, grouped or repeated units, shared components including
    common denominators and totals, many variables) and told to keep them in the `minus` world."
  - **W-0:** the PC wording.
  - **Not allowed:** "unaware", "blind", "errors nobody anticipated", "independent of the gate's authors". W-1
    detections show what the gate does when the world author is prompted to keep the dependence kinds that these errors
    exploit.
- **I-D7. The reference world** is written by an agent that knew the error. Its only roles are validity and the
  consistency check.

## 9. Decisions (closed; recorded in the decision register)

- **The author (2026-11-17):** "Faz D yapılsın" (run Phase D).
- **The assistant, by delegation:**
  - 20 pairs per class;
  - the checklist arm, with decoys;
  - no tool-side dependence probes first;
  - arm R kept only as a consistency check;
  - V1 kept at 0.25, with labels V1a and V1b;
  - H-D3 on declared detection.

## 10. Tools (written by the coding subagent, reviewed in round 2)

- **`tools/validity_check.py`:** V1, V2, the mechanical checks of 2.2, the flag threshold from the study's family, and
  the log.
- **`tools/structure_stat.py`:** runs a private note's statistic on a world's samples, from the disjoint seed stream.
- **`tools/attributable.py`:** the section 5 rule from two certificates, with the generic and declared labels. Its
  acceptance test is the fixture of section 5.
- **`tools/assemble.py`:** splices the bodies into the skeletons.
- **`tools/check_skeletons_d.py`:** checks the keys, shapes and dtypes and the section 2.1 limits.

Each tool comes with tests. The Phase C fixtures are used for no Phase D number.
