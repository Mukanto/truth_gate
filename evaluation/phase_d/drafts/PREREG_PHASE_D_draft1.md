# Phase D: leakage and coupling errors with validated pairs — pre-registration (DRAFT 1)

Status: **draft 1, 2026-11-17, not reviewed, not frozen.**
- Designer: Claude, under the author's delegation.
- Section 0.2 now rests on the post hoc validity audit of Phases B and C (`evaluation/validity_audit_b2b3/`).
  Draft 0 was written before that audit.
- No Phase D case exists when this text is written.
- "PB" is `evaluation/phase_b/PREREG_PHASE_B.md` and "PC" is `evaluation/phase_c/PREREG_PHASE_C.md`. "As PC §n" means
  the rule applies unchanged.

## 0. Why Phase D, and its questions

### 0.1 What Phases B and C measured

In both phases the classes B-2 (procedure-level leakage) and B-3 (coupling by construction) failed the bar: a one-sided
95% Wilson lower bound of at least 0.6 for both detection and clean pass.

| Class | Phase B (det / clean of n) | Phase C (det / clean of n) |
|---|---|---|
| B-2 | 7 / 11 of 12 | 7 / 8 of 12 |
| B-3 | 8 / 8 of 12 | 8 / 8 of 10 |

### 0.2 Why those verdicts do not isolate the gate (from the reports and their post-run audits)

- **D-1. The error did not show in the declared worlds.** Several misses have a faulty criterion that fails in `minus`
  at about the nominal rate (PB report 5.2; PC report 7.1). The declared worlds held too little of what the error
  exploits: time dependence, records of one unit on both sides of a split, many features, or a shared error term in a
  denominator. The brief's size or the model in both twins also left little room for the error.
  - Such a pair tests the world author's coverage, not the gate.
  - It is also not clear that its faulty criterion is faulty in any consequential sense at that size.
- **D-2. The "fixed" twin was not always clean.** Some fixed twins keep a claim threshold that chance reaches at the
  brief's size (PC 7.3: B2-08 to B2-11, B3-04). In others the skeleton defeats the correction (B3-05, B3-12; PB 5.3).
  - In these pairs the gate's flag on the fixed twin is correct, yet it counts as a failed clean pass.
  - The documented correction can also change the estimand (PB 5.3: B3-11, B3-12).
- **D-3. Some detections do not come from the error.** In Phase C the fixed twin carries the same expected flags at
  similar or somewhat lower rates in 4 of B-2's 7 detections and in 2 of B-3's 8. This is the post-run audit's strict
  reading, *post hoc* (PC report section 9).

- **The validity audit confirms D-1 to D-3** (post hoc, two fresh auditors, 46 pairs; `evaluation/validity_audit_b2b3/`):
  - Of 16 misses, 10 come from worlds without the structure, 5 from an error that raises the statistic but not past the
    claim's threshold at the brief's size, and 1 is mixed.
  - Of 11 failed clean passes, 10 come from fixed criteria that are not clean tests. The eleventh is a guard meeting
    0.4.0's K1 rule.
  - On the 22 pairs judged adequate the gate detected 21 errors and passed 22 corrections. This count is selected
    after the fact.
  - The auditors disagree on one label. An error that stays below the threshold is a tool limit for one and a size
    effect of the case for the other. This design measures it as a scope limit (I-D1).

So the B and C verdicts for these classes mix three things:
- the gate's behaviour;
- whether the world author covered the structure;
- whether each pair was valid.

Phase D separates them. It checks that each pair is valid before any gate run, scores only detections that the error
explains, and measures the structure in the declared worlds.

### 0.3 Questions

- **Main (confirmatory).** On pairs that are valid by the pre-run checks of section 2, does Truth_Gate 0.5.0 flag the
  faulty criterion and pass the fixed one?
  - The worlds are declared by a world author who is not told the error, the class or the source.
  - That author is given a generic dependence checklist (arm W-1, section 4).
  - Only detections attributable to the error count (section 5).
  - Asked separately for B-2 and for B-3.
- **Arm comparison (confirmatory).** Does the checklist raise attributable detection, against the same world author
  without it (arm W-0, the instructions of PC)?
- **Descriptive.**
  - The gate on the same criteria with the reference worlds (arm R, a ceiling).
  - Phase B/C-style scoring (PB §6 detection), for comparability.
  - Rates of pairs failing the validity checks, per subtype.
  - The measured structure in every declared world.
  - Awareness readings.

## 1. Classes, subtypes, sources

- **B-2 procedure-level leakage**, 20 pairs, subtypes as PC §1 (L1.1, L1.2, L1.3, L1.4, L3.1, L3.2). Allocation: 4,
  4, 3, 3, 3, 3. The designer fixes the order of the subtypes before any brief.
- **B-3 coupling by construction**, 20 pairs, over at least three mechanism tags with at least 5 pairs each:
  - ratios sharing a denominator, or a normalisation by a shared total;
  - a change score against its own baseline (x versus y − x);
  - a variable correlated with a sum or composite that contains it.

  The designer fixes the tags and the allocation before any brief.
- **Sources.** Those of PB and PC, and new ones listed in `SOURCES_D.md` before any brief.
  - No Phase D brief may copy a Phase B or C brief (same source, mechanism and statistic family *and* the same claim
    wording).
  - Overlap is reported as in PC §1.
- **Reserve.** 6 reserve slots per class, used in a fixed order only to replace pairs dropped by section 2.4. Every
  replacement is reported by id and cause.

## 2. What a case is, and the validity checks (before any gate run)

### 2.1 The case

As PC §2 (one criterion, imports, the allowed guards, the estimand rule, what a brief may state, banned terms), with
these changes:
- **Sizes.** At most 2000 units along any axis and at most 2 000 000 values in any array. The timing limit is 30 minutes
  per check with the fixed criterion (PC: 1000 and 500 000, 15 minutes). The brief uses the source's sizes where these
  limits allow.
- **Model.** Where the source names a model family, both twins use it. Otherwise the brief's private note gives the
  family and the reason.
- **The private note** adds the exploited structure as one sentence, and a **structure statistic**: a computable number
  on a dataset (for example a lag-1 autocorrelation, an intra-unit correlation, a number of features per unit, the
  correlation induced by a shared term). It also gives the statistic's value in the source's setting, with a quote, or
  "source states none" and a stated realistic value.

### 2.2 The reference world (arm R)

A fresh **structure author** is told the error, the source and the private note. It writes `reference.py`: a `plus`
world (claim true) and a `minus` world (claim false), each with the structure at the value in the private note.

The reference world is used for:
- the validity checks;
- the descriptive arm R.

The world authors of arms W-0 and W-1 never see it.

### 2.3 Validity checks (frozen script `tools/validity_check.py`, 200 samples per stream, fixed seeds)

- **V1, the error manifests.** In the reference `minus` world:
  - the faulty criterion holds in at least 0.25 of the samples;
  - it holds at least 0.15 more often than the fixed criterion, with a one-sided Fisher exact p below 0.01.
- **V2, the fixed criterion is clean.** It holds in:
  - at most 0.0808 of reference `minus` samples;
  - at most 0.0808 of the gate's noise-probe samples;
  - at least 0.70 of reference `plus` samples.
- **V3, single difference.** `tools/mech_check_twins.py` (as PC) confirms that the twins differ only in the mapped lines.
  The fidelity auditor confirms that the difference is the documented error.

### 2.4 Repair and drop

The criterion author runs V1–V3. A pair that fails gets **one** repair:
- the size is raised within the limits; or
- the model is moved to the source's family; or
- the brief is rewritten with the same claim type.

The fixed criterion is never given a rule that the claim does not state, and the claim's threshold is never moved to
make V2 pass. A pair that still fails is dropped and replaced from the reserve. The drop is reported by subtype with its
cause:
- "error does not manifest at a feasible size" (V1);
- "no clean correction at a feasible size" (V2);
- "not a single difference" (V3).

## 3. Roles and order of work

0. **Start conditions, as PC §4 item 0, from tag `v0.5.1`.** The designer builds the agent document set, the package
   copy, the smoke test and the Fable pre-flight. Additions:
   - The document set excludes everything that reports Phase B, Phase C or the validity audit. That covers
     `evaluation/validity_audit_b2b3/`, the reports, `docs/EVALUATION.md`, `CHANGELOG.md` and any README sentence on
     results.
   - The scan list adds the audit's vocabulary: "validity audit", "case-world", "case-size", "case-fixed",
     "sub-threshold", "attributable", and the subtype and tag names of section 1.
   - No agent except the structure author and the fidelity auditor may read this document's sections 0.1 to 0.2, 2.2 to
     2.4 or 4. The world authors of W-1 see only the checklist text of section 4, inside their instructions.
1. The designer fixes the allocation, sources, tags and reserve order (`ALLOCATION_D.json`, frozen with this text).
2. A **brief author** (a fresh agent per pair) reads the source and writes the brief and the private note.
3. A **criterion author** (a fresh agent per pair) writes `faulty.py` and `fixed.py`, without worlds, from the brief and
   the mapping.
4. A **structure author** (a fresh agent per pair, told the error) writes `reference.py`.
5. The criterion author runs the validity checks (section 2.3) and the one repair (section 2.4). Logs go to `CASE.md`.
6. **World authors** write the worlds and controls from the brief only (claim, data keys, sizes), never from the error,
   class, source, private note or reference world:
   - **W-0** gets PC's world instructions unchanged;
   - **W-1** gets the same instructions plus the checklist of section 4;
   - each arm uses fresh agents of the PC model line, the briefs are shuffled, and the agents of the two arms are
     disjoint.
7. A **fidelity auditor** (a fresh agent) checks: the mapping to the source, the single difference, the estimand line,
   the brief rules, the validity logs, and that no world file leaks the error (PC §5 items).
8. **Case freeze.** Then the gate runs.
9. After the run: the designer's recomputation, and a blind post-run audit in the independent session.

Pre-freeze review of this text: three rounds by fresh agents in the independent session, as for Phase C.

## 4. The checklist of arm W-1 (fixed text)

> Before you write the worlds, list for each data key how the units in a real dataset of this kind can depend on each
> other:
> - order in time;
> - groups, sites, or repeated measurements of the same unit;
> - components shared between variables (a common factor, a common total, a common denominator, a common measurement);
> - many variables relative to the number of units.
>
> Give each dependence a realistic size and say where the size comes from. Keep every dependence in **both** the `plus`
> and the `minus` world: only the claimed effect differs between them.

The checklist names kinds of dependence, not errors. It is the same for every class and is given for every brief of
both classes. It is a candidate rule for the methods protocol; it is adopted only if H-D3 holds (section 8).

## 5. Run and scoring

- **Run.** Truth_Gate at tag `v0.5.0`, full mode, default settings, one check at a time. The studies are:
  - each pair with the W-0 worlds;
  - each pair with the W-1 worlds;
  - each pair with the reference worlds.

  Infrastructure failures as PC §6.
- **Expected flags** as PB §6.
- **Attributable detection** of a pair in an arm. The faulty study's verdict is NOT_FALSIFIABLE, and at least one of its
  expected flags is a rate flag on a stream s where both of these hold:
  - the faulty criterion holds at least 20 more times out of 200 than the fixed criterion of the same arm;
  - the difference has a one-sided Fisher exact p below 0.05.

  Rate flags are `K2_HIGH_SIZE` (stream `minus`), `K4_CONTROL_ALSO_HOLDS` and `HIGH_RATE:control:<id>` (that control),
  `K5_HOLDS_ON_NOISE` and `HIGH_RATE:probe:noise`, `HIGH_RATE:world:null`, `K5_HOLDS_ON_SHUFFLE` and
  `HIGH_RATE:probe:shuffle:*`. A detection whose expected flags are only `K2_NO_SEPARATION` or `K2_FAILS_UNREACHABLE`
  is not attributable. The rule is computed mechanically from the two certificates.
- **PB-style detection** (PB §6) is reported next to it for every arm.
- **Clean pass** as PB §6.
- **Structure measured in the declared worlds.** For each pair and arm, `tools/structure_stat.py` computes the private
  note's structure statistic on 200 `minus` samples. It is reported as the mean and as the share of samples at or above
  half the source value. Each miss gets a mechanical label:
  - "declared worlds lack the structure" when that share is below 0.5;
  - otherwise "structure present, not flagged".

## 6. Hypotheses, thresholds, power

- **H-D1 (B-2) and H-D2 (B-3), arm W-1.** Every non-dropped pair counts (20 per class). Each class needs both of these:
  - the one-sided 95% Wilson lower bound of attributable detection is at least 0.6;
  - the same bound for clean pass is at least 0.6.

  That is at least 16 of 20 on both. Power: at true rates of 0.85 on both, the class passes with probability 0.69; at
  0.90, with 0.92.
- **H-D3, arms W-1 against W-0, both classes pooled (40 pairs).** An exact one-sided McNemar test on attributable
  detection, α = 0.05. Power (simulated):

  | Discordant pairs (W-1 only / W-0 only) | Power |
  |---|---|
  | 0.25 / 0.05 | 0.69 |
  | 0.30 / 0.02 | 0.96 |
  | 0.20 / 0.05 | 0.49 |

  A non-significant result reads "not demonstrated", never "no effect".
- **Descriptive.** Arm W-0 with both scorings, against PB and PC (different briefs, sizes and pairs; not a test). Arm R
  (the ceiling). The validity drop rates per subtype and tag. The structure statistics. Awareness as PC (P/C/N, two
  readers).

## 7. After the run

As PC §7:
- the designer recomputes every number from the certificates with a separate script;
- a blind post-run audit is made by a fresh agent in the independent session;
- thresholds, rules and expected flags never change after the run;
- a case found wrong stays in the table with the error reported next to it.

## 8. Interpretations fixed now

- **I-D1.** Phase D measures the gate on pairs whose error manifests and whose correction is clean at the brief's size,
  in a reference world written by an agent that knew the error.
  - A pair that fails V1 has an error that never makes its criterion hold where the claim is false at that size. A
    check of decisions, which the gate is, cannot detect such an error by design. These pairs measure the size of that
    scope limit. Their rate per subtype is reported as a limit of the gate, not as passes or misses.
  - A pair that fails V2 has no clean correction at that size and says nothing about the gate's false alarms.
- **I-D2.** If H-D1 or H-D2 holds and H-D3 holds, then on valid pairs of that class the gate detects the error and
  passes the correction when the world author is given the dependence checklist. The checklist then goes into the
  methods protocol, and into the gate's documentation and its `suggest` template, in a later version with its own
  review.
- **I-D3.** The four outcome patterns:
  - arm R near the ceiling but W-1 failing: the world author's coverage stays the bottleneck even with the checklist. A
    tool-side remedy (probes that inject dependence, such as the deferred mutations `copy` and `stale`) is the next
    question, for a later spec.
  - arm R itself failing: the gate does not flag these criteria even when the structure is present. This is a
    machinery finding for the next release.
  - clean-pass failures on pairs that passed V2: genuine false alarms of the gate, each reported with its flags.
  - W-0 against PB/PC: different briefs, sizes and validity rules; such a difference isolates none of them (as PC I-6).
- **I-D4. Allowed claims.**
  - Allowed: what the gate did on validated pairs carrying errors documented in the literature, with worlds declared by
    a model of a different Claude line that was not told the error, with or without a checklist of dependence kinds.
  - Not allowed: "unaware", "blind", "errors nobody anticipated", "independent of the gate's authors". The W-1 claims
    always name the checklist.
- **I-D5. Awareness.** The checklist names kinds of dependence that B-2 and B-3 errors exploit. W-1 detections show what
  the gate does when the world author is prompted to model dependence, not when it anticipates a specific error. The
  awareness readings are reported per arm.
- **I-D6. Reference world.** Arm R is written by an agent that knew the error. Its detections are a ceiling, not a
  result about users.

## 9. Open decisions (for the author; Claude decides under delegation if not answered)

1. Run Phase D at all. It needs about 40 pairs × 6 roles of agent work, plus three review rounds. **Claude's
   recommendation: yes, after the validity audit confirms D-1 to D-3.**
2. The pair count: 20 per class (joint power 0.69 at 0.85) or 16 (0.62). **Recommendation: 20.**
3. The checklist arm. It tests a protocol change, not only the gate. **Recommendation: keep it; it is the remedy that
   can be adopted without a new spec.**
4. The alternative of building tool-side dependence probes (spec 0.8) first and evaluating them. **Recommendation: not
   first. Phase D's arm R against W-1 shows whether they are needed.**

## 10. Files to be written before review 1 (by the coding subagent, specified by the designer)

- `tools/validity_check.py` (V1, V2; uses the gate's noise probe).
- `tools/structure_stat.py` (runs a private note's statistic on a world's samples).
- `tools/attributable.py` (the section 5 rule from two certificates).
- Each tool comes with tests on Phase C pairs as fixtures. These are not used for any Phase D number; for example,
  `attributable.py` must reproduce the strict reading of PC section 9 on B2-08 to B2-11.
