# Phase D: leakage and coupling errors with validated pairs — pre-registration (DRAFT 3)

## Status

- **Draft 3, 2026-11-17, not frozen.** Designer: Claude, under the author's delegation.
- Draft 1 had a blind review (2 blocking, 15 major, 7 minor). Draft 2 had a second review (0 blocking, 21 major,
  15 minor; "freezable after fixes"). Every finding is addressed; `REVISIONS_D.md` maps each one to its change.
- "PB" is `evaluation/phase_b/PREREG_PHASE_B.md` and "PC" is `evaluation/phase_c/PREREG_PHASE_C.md`. "As PC §n" means
  the rule applies unchanged.
- No Phase D case exists when this text is written.

**Frozen with this text** (`FREEZE_PREREG_D.json`):
- this file, `REVISIONS_D.md`, and the reviews `REVIEW1.md`, `REVIEW2.md` and `REVIEW3.md`;
- `ALLOCATION_D.json`, `SOURCES_D.md`, and `P2_READING_D.md` (PC's `P2_READING.md` with the Phase D cap);
- the instruction files `BRIEF_AUTHOR_D.md`, `CRITERION_AUTHOR_D.md`, `STRUCTURE_AUTHOR_D.md`, `WORLD_INSTRUCTIONS_D0.md`,
  `WORLD_INSTRUCTIONS_D1.md`, `FIDELITY_AUDIT_D.md` and `AWARENESS_RULE_D.md`, and the `TASK.json` content rule
  (section 3 item 2);
- the tool specifications `TOOLS_SPEC_D.md` and `TOOLS_SPEC_D_round2.md`;
- the tools in `tools/`, with their tests: `validity_check.py`, `structure_stat.py`, `attributable.py`, `assemble.py`,
  `check_skeletons_d.py`, `mech_check_bodies.py`, `clean_pass_class.py`, `miss_label.py`, `expected_flags_d.py`,
  `shuffle_d.py`, `scan_docs_d.py` and `term_check_d.py`;
- the acceptance set `tests/acceptance_d/`, with the designer's hand-written `EXPECTED.md` and the output of the
  independent recomputation (section 5).

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
- **D-3.** In Phase C, six detections would also occur with the fixed criterion. Section 5's rule asks a different
  question, so it counts five of them as not attributable.

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
(section 5). It measures the structure in every declared world after the run (section 5).

### 0.3 Questions

- **Main (confirmatory, H-D1 for B-2, H-D2 for B-3).** Take the pairs that pass the pre-run checks of section 2, with
  worlds declared by a world author who is not told the error, the class or the source but is given the dependence
  checklist of section 4 (arm W-1). Does the system of Truth_Gate 0.5.1 and that world author flag the faulty criterion
  with a detection attributable to the error, and pass the fixed criterion? Two shares are reported separately:
  - the share of attributable detections that needs no declared world (the noise probe);
  - the share that the declared streams carry.
- **Arm comparison (confirmatory, H-D3).** Does the checklist raise attributable detection on the declared streams,
  against the same world-author model without it (arm W-0, PC's instructions)?
- **Descriptive.**
  - Arm R: the gate on the reference worlds, as a consistency check.
  - The decoy pairs in both arms (section 1). They mix the batches and show detection and clean pass under the
    checklist in classes whose mechanisms the checklist partly names.
  - Phase B/C-style scoring.
  - Validity drop rates by subtype and tag, with their causes.
  - The structure statistics, the miss labels and the clean-pass classes.
  - Awareness readings.

## 1. Classes, subtypes, tags, sources, decoys, reserve

- **B-2**, 20 pairs. Subtypes as PC §1 (L1.1, L1.2, L1.3, L1.4, L3.1, L3.2), allocated 4, 4, 3, 3, 3, 3.
- **B-3**, 20 pairs, tagged with PC's closed `mechanism_tag` list for B-3, with its definitions and precedence
  (`AUTHOR_PHASE1_C.md`). The allocation is 5 pairs each for `ratio-shared-denominator`, `ratio-vs-denominator-proxy`,
  `change-vs-baseline` and `shared-measured-component`. `target-from-labels` is not allocated. Because the tags are
  PC's, the overlap key applies directly.
- **Decoys**, 8 pairs: 4 B-1 and 4 B-6.
  - Their mechanisms are partly named by the checklist: B-6 `units-not-independent`, B-1 `extreme-group-change` and
    `select-then-test-same-data`.
  - They are written and validated like the others. Where no structure statistic applies, the private note sets it to
    null, and validity runs with `--no-structure` (section 2.3).
  - They go to both world-author arms and are reported descriptively (detection and clean pass, per arm and per
    mechanism). They are excluded from H-D1 to H-D3.
- **Sources** as PC §1, with the caps scaled to 20 pairs:
  - at most 6 pairs per source per class (KAP23 at most 10 B-2 pairs);
  - at least 4 independent read sources per class;
  - within a class, every pair differs from every other as PB §4.
  - The pairs and reserves allotted to a source never exceed the number of distinct settings its readable text
    describes, as listed in `SOURCES_D.md`.

  The sources and the allocation are in `SOURCES_D.md` and `ALLOCATION_D.json`.
- **Overlap**, as PC §1. A pair overlaps a Phase B or C pair when source, mechanism tag and statistic family agree; the
  designer marks it mechanically after the briefs.
  - Each brief author's `TASK.json` lists the (mechanism tag, statistic family) combinations that Phases B and C used
    for its sources. The author prefers other families where the source allows. This exposure of earlier tags is
    accepted, as PC §1 accepted its vocabulary.
  - If strictly more than half of a class's pairs overlap, the report says that the class result "largely repeats Phase
    B and C settings".
  - Every table is also given without the overlapping pairs.
- **Reserve.** 10 reserve slots per class and 2 per decoy class, all written with the main set (section 3).
  - A drop is replaced first from its own half's reserve list for that subtype or tag, then from the other half's list.
  - A reserve whose use would break a source cap is skipped.
  - Minima: for B-2, PC's (L1.1 ≥ 1, L1.3 ≥ 1, L1.4 ≥ 2, L3.1 ≥ 2, L3.2 ≥ 2); for B-3, at least 3 per tag. A class
    below a minimum is reported as "minimum not met", and its verdict stands.

## 2. The case, the reference world, and validity (all before any world author starts)

### 2.1 The case

As PC §2 (one criterion, the imports, the allowed guards, the estimand rule, what a brief may state, the banned terms),
with these changes:

- **Sizes.** At most 2000 units along any axis and at most 2 000 000 values in any array. The timing limit is 30 minutes
  per check, by PB §2's formula (sections 2.3 and 3 item 9).
- **Model.** Where the source names a model family, both twins use it. Otherwise the private note names the family and
  the reason. The model never changes after the brief.
- **Criteria are bodies.** Each twin is a file holding only `import numpy as np` and function definitions at module
  level, one of which is `criterion(d)`. It is written against the brief's keys. `tools/assemble.py` splices it into
  the R, W-0 and W-1 skeletons in place of PC's placeholder criterion.
- **The private note adds:**
  - the exploited structure, in one sentence;
  - a **structure statistic**: a function of the brief's data keys only, with its direction and null value. It is
    computed from parts of the data that the `minus` rule leaves unchanged, so that its expected value is the same in
    `plus` and `minus`. Examples: the autocorrelation of a predictor; the coefficient of variation of a denominator;
    the correlation between repeated records of one unit;
  - its value in the source's setting, with a quote, or "source states none" and a proposed value with its reason.

  A statistic that is fixed by the brief's sizes is marked "set by the brief". The brief author may run the statistic
  on arrays it generates with the brief's shapes, to check that it returns a finite float, and logs those runs.
- **Case files.** After the brief checks, the designer builds each case folder:
  - it gives each brief a neutral id (section 3 item 2);
  - it writes `brief.json` with that id and, per data key, `dims` (the shape as integers, from the brief's sizes);
  - it writes `PRIVATE.json` from the brief author's note. `local_id` becomes the neutral `id`. `mechanism_tag` and
    `subtype` become `subtype_or_tag`. `class` comes from the allocation, and `approved_value` from part A0. The
    approved value is also written into `structure_statistic.note_value`, which the tools read. Every other field is
    copied unchanged.

  The map from neutral id to class, half, source and subtype or tag stays with the designer.

### 2.2 The reference world (arm R)

- **Who writes it.** A fresh structure author (Sonnet line) writes `reference.py`. It reads only what
  `STRUCTURE_AUTHOR_D.md` lists:
  - the brief;
  - these fields of the private note: source, passage, estimand, exploited_structure, structure_statistic, sizes_note,
    and the approved structure value;
  - the source passages in `SOURCES_D.md`;
  - the sources online (URLs logged);
  - `agent_docs/` and `pkg/`;
  - its instructions.

  It does not read the descriptions of the faulty and fixed analyses.
- **What it may not do.** It does not see the criteria. It runs no analysis that could serve as a criterion, and it does
  not estimate the effect from samples. It sets the effect through the generator's parameters and states them in its
  log. It may check shapes, dtypes and the structure statistic.
- **What it writes.**
  - a `plus` world (claim true) and a `minus` world (claim false), each with the structure at the approved value;
  - at least one control, under PC's world-instruction rule 4;
  - exactly the brief's keys, with shapes equal to `dims`.
- **Mechanical checks, before V1** (`tools/validity_check.py`):
  - **(a)** `structure_stat` on 200 `plus` and 200 `minus` samples meets
    `|mean − note_value| ≤ 0.2·|note_value − null_value|` in both worlds, and is equal between the two worlds within
    sampling error;
  - **(b)** the gate's `minus_check` record shows that `minus` changes keys the fixed criterion reads.

### 2.3 Validity checks

The **designer** runs `tools/validity_check.py`. Its samples come from seed 20261117 (not `Budget.base_seed`), on
streams the gate never uses:
- `validity:minus`, `validity:plus` and `validity:noise` for V1 and V2;
- `structure:plus` and `structure:minus` for the structure statistic;
- `timing:plus` for the timing.

Nobody computes a gate stream of a Phase D file before the case freeze.

**Which run counts.** Only runs with `--samples 1000 --seed 20261117` are validity runs. The first such run on a given
set of input hashes decides. Every run is appended to `validity_log.jsonl` with the SHA-256 of its inputs. Any other run
on a case folder is refused by the tool. A run missing from the log is a protocol breach.

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
- **V3, single difference.**
  - The two bodies are compared line by line against the mapping in `CASE.md`.
  - `tools/mech_check_bodies.py` checks the module-level rule and the banned names in the bodies, lists every
    comparison of a computed summary with a constant (`MECH_CHECK.json`), and confirms the default Budget and Targets.
  - `tools/assemble.py` confirms, for every arm, that the assembled faulty and fixed study files differ only inside the
    criterion body.
  - Fidelity audit part A confirms that the difference is the documented error.
- **Timing.** The fixed criterion on 20 reference `plus` samples gives t; their generation gives g. S is the reference
  study's stream count. The estimate `2·200·(S+1)·(t+g)` must be at most 1800 seconds; otherwise the pair is dropped as
  "timing infeasible".
- **Structure statistic.** It must be computable on the reference worlds. A decoy whose statistic is null runs with
  `--no-structure`, which skips mechanical check (a) and is logged.

### 2.4 Repair and drop (decision table, applied by the designer)

| Failure | Action |
|---|---|
| V1 (V1a or V1b) | Drop, with the label. |
| V2 | Drop. |
| Timing above 1800 s | Drop ("timing infeasible"). |
| An error in V1, V2 or timing (an exception, a bad return or a failed generation) | One repair, by the author of the failing file; then drop. |
| V3, `mech_check_bodies.py`, or mechanical check (b) | One repair of the bodies by the criterion author; then drop. |
| Mechanical check (a), or a structure statistic that cannot be computed | One repair: of `reference.py` by the structure author, or of the statistic by the brief author; then drop. |
| Fidelity A: (a), (b), (c), (d), (g) | One repair of the bodies; then drop. |
| Fidelity A: (j), (k), (p) | One repair of `reference.py`; then drop. |
| Fidelity A: (m) | One repair of the statistic by the brief author; then drop. |
| The designer's log check: a validity result without its logged run | The run is repeated with the required settings and logged, or the pair is dropped. |
| Fidelity A: (e), (f), (h), (i) (the brief) | Drop. |

- **Repair requests.** A repair request names the file and quotes only the failing item, or the script's error list. It
  never contains a count, a rate or a p value from `validity_check.py`. The author changes only that file, logs the
  change, and confirms that it saw no rate.
- **"The same author"** is the same agent, resumed. If it cannot be resumed, a fresh agent of the same role reads its
  predecessor's log and does the repair. Either way is logged.
- A repair never changes the claim, its statistic, its threshold, the model, the brief or the sizes.
- **Reserves.** Dropped pairs are replaced from the reserve, following section 1, and the reserve pair goes through the
  same checks. Every run, repair, drop and substitution is frozen in `FREEZE_VALIDITY.json` before any world author
  starts. The drop rates are reported by subtype, tag and label (V1a, V1b, V2, timing, V3, fidelity).

## 3. Roles and order of work

Each role has a frozen instruction file that states exactly what it reads. Only the designer and the fidelity auditor
read this document. A role sees the rules of sections 2.3 and 2.4 only where its instruction file quotes them.

0. **Start conditions** (before any agent sees anything), as PC §4 item 0, from tag `v0.5.1`. The tag is used
   throughout: the agent documents, `pkg/`, the tools and the run.
   - The designer records that `truth_gate/` and `kapi/` differ between `v0.5.0` and `v0.5.1` only in `external.py`
     (R-28) and in the version strings. Neither touches the engine, the probes or the statistics.
   - **The document set** excludes everything that reports Phase B, Phase C or the validity audit:
     `evaluation/validity_audit_b2b3/`, the reports, `docs/EVALUATION.md`, `CHANGELOG.md`, and every README sentence on
     results. `tools/scan_docs_d.py` scans it with the added vocabulary.
   - **Sandbox.** Every agent works in a sandbox folder holding copies of its allowed files only.
     - It fetches nothing from the project's repository or its published evaluation material, and logs every URL it
       reads; the designer checks each URL log against the repository's host and paths.
     - No context-mode indexing or cross-agent search, and no session scratchpad.
     - Every transcript is checked for these points with the designer's transcript tools.
1. **Allocation.** `ALLOCATION_D.json` and `SOURCES_D.md` are frozen with this text.
2. **Brief authors** (Sonnet line, `BRIEF_AUTHOR_D.md`) write all briefs and private notes, reserves included:
   - two fresh agents per class (B-2, B-3), one per half, each with the sources of its half;
   - one fresh agent for the decoys.

   Each gets a `TASK.json` holding: class, half, the counts of pairs and reserves per subtype or tag and source (from
   `ALLOCATION_D.json`), the sources, and the (tag, family) combinations of Phases B and C for those sources.
   Afterwards:
   - the designer runs `tools/term_check_d.py`, the "what a brief may state" check, a check of PB §1's class rules, and
     a check of the within-class difference rule across both halves;
   - `tools/shuffle_d.py` assigns the neutral ids, with its seed derived from `FREEZE_PREREG_D.json`;
   - the designer builds the case folders (section 2.1).
3. **Fidelity audit part A0** (one fresh auditor per class: B-2, B-3, decoys; item (l)). For each structure value, the
   auditor sees only the brief, the private note and the source passage. It approves a "source states none" value as
   realistic, or checks a quoted value against its quote. A rejected value gets one revision by the brief author; if it
   is rejected again, the pair is dropped. The approved values are frozen before item 5.
4. **Criterion authors** (`CRITERION_AUTHOR_D.md`) write the two bodies of every pair and reserve. There is one fresh
   agent per class half and one for the decoys (Sonnet line), and none of them wrote briefs. They never run the faulty
   body.
5. **Structure authors** (`STRUCTURE_AUTHOR_D.md`) write `reference.py` for every pair and reserve (section 2.2). There is
   one fresh agent per class half and one for the decoys (Sonnet line), distinct from the criterion authors.
6. **Validity**, by the designer (sections 2.3 and 2.4).
7. **Fidelity audit part A** (one fresh auditor per class: B-2, B-3, decoys; `FIDELITY_AUDIT_D.md`), with items (a) to
   (k), (m) and (p). The auditor does not see any validity result. The designer checks mechanically that every validity
   result has its logged run, with the required settings and matching input hashes. Repair and replacement follow
   section 2.4.
8. **Freeze of validity** (`FREEZE_VALIDITY.json`).
9. **World authors**, arms W-0 and W-1. Each writes the worlds and controls from the brief only (claim, data keys,
   sizes).
   - Both arms get PC's world instructions with the limits of section 2.1 in place of rules 6 and 8. A world or control
     call must take at most 250 ms. The check script rejects a call above 1000 ms.
   - W-1 also gets the checklist of section 4.
   - The private files are `WORLD_INSTRUCTIONS_D0.md` and `WORLD_INSTRUCTIONS_D1.md`. Each is given to its agents as
     `WORLD_INSTRUCTIONS_D.md`. They differ only in the checklist section and its rows in the difference table. Neither
     names the arms or the other file.
   - The agents are fresh, of PC's world-author line (Fable), and disjoint between arms.
   - `tools/shuffle_d.py` writes batches of 12 consecutive neutral ids (the last one shorter). W-0 and W-1 use the same
     batch files. Their batches alternate in time.
   - PC §4 item 3 (identification, invalid batch, stops) applies to every world-author agent. A redo in one arm is
     logged next to its counterpart.
   - `tools/check_skeletons_d.py` checks every skeleton: keys, shapes equal to `dims`, dtypes, identical shapes across
     the arms, and the section 2.1 limits. A rejected skeleton goes back once.
10. **Timing per arm.** After the skeleton check, t and g are measured on each arm's skeleton (fixed criterion, 20
    `plus` samples of stream `timing:plus`, seed 20261117, outcomes not recorded). A skeleton whose estimate is above
    30 minutes goes back once to a fresh agent of that arm. After the redo it runs anyway; a check beyond 60 minutes
    counts as attrition (section 6).
11. **Fidelity audit part B** (after item 9), with item (o). The auditor gets the two skeletons of a pair under random
    labels (X and Y); the designer keeps the map. There is no replacement; a "no" counts as in section 6.
12. **Expected flags.** `tools/expected_flags_d.py` writes `EXPECTED_FLAGS_D.json`, per pair and arm.
13. **Case freeze and public push** with the author's approval, as PC §5. The runner refuses to start unless the freeze
    verifies and the named public commit holds it (protocol rule 17).
14. **Run** (section 5). Then the designer's recomputation and a blind post-run audit in the independent session
    (section 7).

**Compute budget.** The estimate sums the per-check timing estimates over 288 checks (48 pairs × 2 twins × 3 arms).
- If it exceeds 72 hours, arm R is cut.
- If W-0 and W-1 alone exceed 120 hours, both W arms are still run, interleaved by pair, and the time is reported.

Pre-freeze review: round 3 is a targeted look at the round-2 fixes, the new tools and the acceptance set.

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
> `WORLD_LOG.md`, and do not refer to this list in `WORLD_LOG.md`.

The checklist names the kinds of dependence that B-2 and B-3 errors exploit, and tells the world author to keep them in
`minus`. It is given for every brief of arm W-1, decoys included. The claims wording of section 8 names it.

## 5. Run and scoring

- **Run.** Truth_Gate at tag `v0.5.1`, full mode, default settings, one check at a time. For every pair, both twins run
  in arm R (the reference worlds), arm W-0 and arm W-1. Infrastructure failures are handled as PC §6. A check beyond 60
  minutes is a timeout.
- **Expected flags** as PC §6, from `EXPECTED_FLAGS_D.json`.
- **Rate flags and their streams:**

  | Flag | Stream |
  |---|---|
  | `K2_HIGH_SIZE`, `K2_FAILS_UNREACHABLE` | `world:minus` |
  | `HIGH_RATE:control:<id>` | that control's stream |
  | `K4_CONTROL_ALSO_HOLDS` | each control stream s with `bounds[s].upper ≥ bounds[world:plus].lower` (the gate's rule) |
  | `K5_HOLDS_ON_NOISE`, `HIGH_RATE:probe:noise` | `probe:noise` |
  | `K5_HOLDS_ON_NULL`, `HIGH_RATE:world:null` | `world:null` |
  | `HIGH_RATE:probe:shuffle:<a>,<b>` | that shuffle stream |
  | `K5_HOLDS_ON_SHUFFLE` | each shuffle stream s with `bounds[s].upper ≥ bounds[world:plus].lower` |

  `K2_NO_SEPARATION` alone is not a rate flag.
- **Attributable detection** of a pair in an arm (`tools/attributable.py`). The faulty study's verdict is
  NOT_FALSIFIABLE, and at least one of its expected rate flags, on a stream s, meets both conditions:
  - **(a)** the fixed study of the same arm carries no rate flag on s;
  - **(b)** the faulty count on s exceeds the fixed count, with a one-sided Fisher exact p < 0.05.

  A stream does not qualify if the fixed study has a load error or a hard UNDEFINED on s (`hard_undefined > 0`), or
  has no count on s. A faulty load error is not a detection. Each such case is listed.

  Precisions:
  - "Its expected rate flags" are the flags of the faulty certificate that are both expected and in the table above.
  - In (a), every rate flag of the fixed certificate counts, expected or not.
  - `K4_CONTROL_ALSO_HOLDS` and `K5_HOLDS_ON_SHUFFLE` are mapped to streams with the bounds of the certificate that
    carries the flag.
  - A count is `holds` out of `n`.

  The rule asks whether some expected flag is explained by the error on its stream. That differs from D-3's question,
  whether the faulty verdict would occur with the fixed criterion: B3-04 is attributable under the rule, generic only,
  and counted by D-3.

  The twins share seeds, so their counts on a stream come from the same samples. The certificates hold only counts, so
  a paired test is not available. Fisher's test treats the counts as independent, which is conservative here.
- **Generic and declared.** An attributable detection is **generic** if `probe:noise` is among its qualifying streams,
  and **declared** if a qualifying stream other than `probe:noise` exists. A detection can be both. The noise probe
  draws N(0, 1) and Bernoulli arrays from the brief's keys, shapes and dtypes, which are identical in every arm, so its
  distribution is the same in every arm.
- **Secondary scorings**, per arm, reported next to the primary:
  - PB-style detection (PB §6);
  - the draft-1 rule (a 20-count margin and Fisher);
  - the noise-only and declared-only baselines (PB §6);
  - clean pass without the noise stream.
- **Clean pass** as PB §6. After the run, `tools/clean_pass_class.py` classifies every failed clean pass. The first class
  that applies is used:
  - **(e) attrition or no verdict**, with the cause;
  - **(1) fixed not clean in these worlds**: 1000 fresh samples of a flagged rate stream (seed 20261117, stream
    `classify:<stream>`) give a rate whose 95% Wilson interval lies above the declared size;
  - **(2) possible false alarm**: no flagged rate stream has a fresh interval above the size (each interval includes
    the size or lies below it; the relation is recorded per stream);
  - **(3) fixed weak in plus**: the failure comes only from `K2_NO_SEPARATION`, `K2_HOLDS_UNREACHABLE`, `K2_LOW_POWER`,
    or a relative flag (`K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_*`) whose stream carries no rate flag. `K4_NO_CONTROL`
    is not a relative flag and falls under (4);
  - **(4) other.**
- **Miss labels.** After the run, `tools/miss_label.py` labels every miss per pair and arm. The first label that
  applies is used:
  - **(e) attrition or no verdict**, with the cause;
  - **(c) PB-detected but not attributable**;
  - **(a) "declared worlds lack the structure"**: the share of 200 `minus` samples (stream `structure:minus`) at or beyond
    the half-way point `null_value + 0.5·(note_value − null_value)` is below 0.5. This label is not used when the
    statistic is "set by the brief" or null. "Structure not computable" replaces (a) when the statistic fails on that
    world;
  - **(b) "structure present, error did not change decisions in these worlds"**: the faulty `minus` count is below that
    arm's `kstar`, computed from the arm's own study;
  - **(d) "other: examined as a possible gate finding"**.
- **Acceptance of `attributable.py`.** The tool must pass both of these.
  - **(i) The Phase C fixture**, computed by the designer (`fixture_attributable_pc_output.txt`):

    | | Attributable | Not attributable |
    |---|---|---|
    | B-2 | B2-01, B2-02, B2-12 | B2-08, B2-09, B2-10, B2-11 |
    | B-3 | B3-01, B3-06, B3-08, B3-09, B3-11; B3-04 and B3-05 (through `probe:noise` only) | B3-12 |

    Under the declared-stream score of H-D3, B3-04 and B3-05 are not attributable.
  - **(ii) The synthetic acceptance set** `tests/acceptance_d/`, one pair per path of the rule. The expected outcomes
    were written by the designer from this text (`EXPECTED.md`), and the set was also scored by an independent
    recomputation, written by a fresh agent from this section alone without seeing the tool. Both must agree with the
    tool.

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
  pass, in the direction W-0 better than W-1, on the B-2 and B-3 pairs entering H-D3. Decoys are excluded.
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
  - **H-D3.** The power depends on the share s of pairs whose declared attribution is the same in both arms, and on the
    number of comparable pairs. Values are exact:

    | Discordant (W-1 only / W-0 only) | n = 40: s = 0 / 0.3 / 0.5 | n = 32: s = 0 / 0.3 / 0.5 |
    |---|---|---|
    | 0.25 / 0.05 | 0.69 / 0.49 / 0.31 | 0.56 / 0.37 / 0.21 |
    | 0.30 / 0.02 | 0.96 / 0.83 / 0.61 | 0.89 / 0.69 / 0.44 |

    A non-significant H-D3 reads "not demonstrated", never "no effect".
- **Attrition.**
  - A skeleton that stays invalid, or a part-B "no", counts as a miss and a failed clean pass in that arm.
  - A timeout or a load error counts as a miss for the faulty twin and as a failed clean pass for the fixed twin.
  - For H-D3, a pair is "not comparable" when either arm has a skeleton that stays invalid, a part-B "no", or a timeout
    or load error of the faulty twin. The exclusions are listed by arm and cause. H-D3 is also reported with them
    counted as non-detections, as a sensitivity analysis.
- **Known before the run** (PROTOCOL 1.2):
  - arm R's `K2_HIGH_SIZE` on the faulty twin, which V1 selects;
  - the fixed twin's noise-probe rate in every arm, which V2 selects.

  For this reason, clean pass is also reported without the noise stream.
- **Descriptive.**
  - Arm W-0 with all scorings, against PB and PC. Briefs, sizes, validity and pairs differ, so this is not a test.
  - Arm R.
  - The decoys per arm and per mechanism.
  - The validity drop rates.
  - The structure statistics, the miss labels and the clean-pass classes.
  - Awareness: P/C/N as PC, with two readers, on `WORLD_LOG.md` only, by readers who do not know the arm (rule in
    `AWARENESS_RULE_D.md`). The second reading for W-1, which includes `CHECKLIST_LOG.md`, is made by other readers after
    the first is frozen.

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
  - at least one of H-D1 and H-D2 holds;
  - H-D3 holds;
  - the clean-pass guard is not significant at 0.05;
  - the pooled W-1 minus W-0 clean-pass difference is at least −2 pairs;
  - the decoys' clean pass in W-1 is not lower than in W-0 by more than 1 pair. This is a guard on clean pass in these
    decoys, not a test of the checklist's genericity.
- **I-D3. Outcome table** (H-D1, H-D2, H-D3). "No verdict" in a class is read as "fails" in this table, and adoption
  follows I-D2 alone.

  | H-D1 | H-D2 | H-D3 | Reading |
  |---|---|---|---|
  | holds | holds | holds | On these pairs of both classes, the system with the checklist detects the error and passes the correction. The checklist raises declared detection. Adoption follows I-D2. |
  | holds | holds | fails | Both classes meet the bar with the checklist, but a checklist effect is not demonstrated: W-0 may do as well. Not adopted. |
  | holds | fails | holds | B-2 meets the bar with the checklist; B-3 does not. The pooled checklist effect is demonstrated, but not within a class. Adoption follows I-D2, with B-3 named as unresolved. |
  | fails | holds | holds | As the row above, with the classes exchanged. |
  | holds | fails | fails | B-2 meets the bar with the checklist; no effect demonstrated. Not adopted. |
  | fails | holds | fails | As the row above, with the classes exchanged. |
  | fails | fails | holds | The checklist raises declared detection, but neither class meets the bar. Not adopted (I-D2). The miss labels and clean-pass classes of section 5 say where the shortfall lies. |
  | fails | fails | fails | Neither class meets the bar, and no checklist effect is demonstrated. The miss labels say whether the structure was missing (a), present without changing decisions (b), flagged without attribution (c), or something else to examine as a possible gate finding (d). |
- **I-D4. Arm R** is a consistency check: V1 and V2 select pairs in the reference worlds, with other seeds. A pair that
  passes V1 and V2 but is not attributable in arm R, or fails clean pass there, is listed and explained. It is not a
  ceiling.
- **I-D5. A clean pass in W-1 below W-0.** Two readings are reported, separated by the clean-pass classes:
  - **Reading 1.** The checklist adds dependence that the documented corrections do not handle (class 1). That is a
    limit of the checklist and of the corrections, not of the gate.
  - **Reading 2.** Stronger dependence lowers the fixed criterion's power in `plus`, so the gate's relative rules fire
    (class 3).
  - Class 2 (possible false alarm) is the gate's own share.
- **I-D6. Allowed claims.**
  - **W-1:** "what Truth_Gate 0.5.1 did on pairs carrying errors documented in the literature, whose error made the
    faulty criterion hold in at least a quarter of the samples of a reference world without the effect, built by an
    agent told the error, and whose correction was clean there, with worlds declared by a model of a different Claude
    line that was not told the error, but was given a checklist naming the dependence kinds that B-2 and B-3 errors
    exploit (time order, grouped or repeated units, shared components including common denominators and totals, many
    variables) and told to keep them in the `minus` world."
  - **W-0:** the same, with PC's wording for the world author.
  - **Not allowed:** "validated" without that qualification; "unaware"; "blind"; "errors nobody anticipated";
    "independent of the gate's authors". W-1 detections show what the gate does when the world author is prompted to
    keep the dependence kinds that these errors exploit.
- **I-D7. The reference world** is written by an agent that knew the error. Its only roles are validity and the
  consistency check.

## 9. Decisions (closed; recorded in the decision register)

- **The author (2026-11-17):** "Faz D yapılsın" (run Phase D).
- **The assistant, by delegation:**
  - 20 pairs per class;
  - the checklist arm, with decoys;
  - no tool-side dependence probes first;
  - arm R kept only as a consistency check;
  - V1 kept at 0.25, with labels V1a and V1b, and no V1 repair;
  - H-D3 on declared detection;
  - the decoys described as partly named by the checklist;
  - "source states none" values approved before the structure authors start (part A0);
  - PC's overlap rule (not a cap).

## 10. Tools

| Tool | What it does | Spec |
|---|---|---|
| `validity_check.py` | V1, V2, timing, the mechanical checks, the flag threshold, the log | 1, 2 |
| `structure_stat.py` | the private note's statistic on a world's samples | 1 |
| `attributable.py` | the section 5 rule, with the generic and declared labels | 1, 2 |
| `assemble.py` | splices the bodies into the skeletons; the per-arm single-difference check | 1, 2 |
| `check_skeletons_d.py` | keys, shapes against `dims`, dtypes, cross-arm shapes, limits | 1, 2 |
| `mech_check_bodies.py` | the body rule, the banned names, `MECH_CHECK.json`, default Budget and Targets | 2 |
| `clean_pass_class.py` | the clean-pass classes of section 5 (after the run) | 2 |
| `miss_label.py` | the miss labels of section 5 (after the run) | 2 |
| `expected_flags_d.py` | `EXPECTED_FLAGS_D.json` per pair and arm | 2 |
| `shuffle_d.py` | neutral ids, batches of 12, the private map | 2 |
| `scan_docs_d.py` | PC's script, with the added vocabulary | 2 |
| `term_check_d.py` | PC's script, unchanged terms | 2 |

Spec 1 is `TOOLS_SPEC_D.md`; spec 2 is `TOOLS_SPEC_D_round2.md`. The round-3 changes to `clean_pass_class.py`,
`mech_check_bodies.py`, `assemble.py` and `miss_label.py` are recorded in `REVISIONS_D.md` (Round 3).

Each tool comes with tests. The Phase C fixtures and the synthetic acceptance set are used for no Phase D number.
