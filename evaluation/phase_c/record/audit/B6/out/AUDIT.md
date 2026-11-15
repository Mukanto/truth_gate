# Fidelity audit, Phase C, class B-6 (blind auditor)

Date 2026-11-15. Auditor: a fresh Claude agent, not an author of any B-6 case. Instructions: `AUDIT_PHASE_C.md`. Result:
**12 of 12 pairs pass** (all nine items "yes"); no repair requests. Per-pair reasons are in `AUDIT.json`.

No criterion was called on any data, no world was generated, and Truth_Gate was not run. There were two helper
computations, both run in isolation with `py -I` from `scratch\`:
* `scratch\brief_checks.py` reads only the twelve `ASSIGNMENT.json` briefs. It scans for the banned terms of PB §4,
  case-insensitively and with hyphen and space variants, lists every word that could state a null, and computes the
  value count of each array against the Phase C caps.
* `scratch\helper_check.py` extracts, as text, the numpy-only Student-t p-value helper (`lgam`, `betacf`, `p2t`) that
  every t-based twin shares. It is byte-identical across 21 files (B6-09 and the fixed twin of B6-12 have none). The
  script executes the helper alone on textbook two-sided 5% critical values (df 1, 2, 8, 10, 14, 18, 19, 28, 38, 78,
  158 and 1198). Every value returned p = 0.050000 (df 1198: 0.050001), with symmetry in t and correct limits at
  t = 0 and t → ∞.

## How each item was judged (common to the class)

* **(a), (b), (c), (g).** Eight pairs (B6-01, 02, 03, 04, 08, 09, 10, 11) are "unit" pairs. In each, the twins differ
  in exactly the two lines that build the analysed arrays: all lower-level values (`.ravel()`, or the dose repeated per
  subsample) in the faulty twin versus one value per experimental unit (`.mean(axis=1)`) in the fixed twin. Statistic,
  threshold, decision rule and helper are otherwise identical.
  Four pairs (B6-05, 06, 07, 12) are "significant here, not there" pairs. Inputs, summary step (change scores,
  per-subject slopes, region effects, group correlations) and the group-size and finiteness guards are identical. The
  faulty twin runs two separate tests and applies the pattern rule (first effect significant in the claimed direction,
  second p ≥ 0.05). The fixed twin runs the direct test of the difference: a two-sample t test of change scores, a
  two-sample t test of slopes, a paired t test of the difference, or a Fisher z test. In these pairs the statistic and
  decision rule differ only by the documented error, and the cost is comparable (all sub-millisecond).
* **(d).** Every comparison in `MECH_CHECK.json` was judged. Each is one of three things:
  * a group-size guard at the note's minimum (2 per group for t statistics, 3 for slope or correlation, 4 for the
    Fisher z test, 1 for the rank sum);
  * the convergence test `abs(de - 1.0) < 1e-14` inside the p-value helper's continued fraction, which looks at no
    input;
  * the claim's own decision rule (B6-07 fixed line 115, B6-09 line 70, B6-12 fixed line 61).

  The unlisted guards are non-finite checks, empty-selection checks (`r.shape[1] < 1`, `rt.shape[1] < 2`, size checks)
  and zero-variance checks (standard error, dose variance, residual variance, rank variance). No code inspects whether
  the input looks like noise, zeros or a shuffle.
  - B6-12's faulty twin uses the fixed twin's minimum of 4 per group, although its own Pearson t tests are defined
    from 3. I judged this "yes": 4 is the minimum of the claim's statistic as the note states it, and mirroring it
    keeps the twins identical outside the error. It is never reached in the skeleton and its chance on the noise probe
    is negligible (about 2e-8). A stricter reader could disagree; I record it.
  - B6-09's guard of 1 per group is lower than the note's 2. CASE.md explains why; a guard of 1 is an
    empty-selection guard and is allowed.
* **(e).** No banned term occurs in any claim, key meaning or size string, and MECH_CHECK reports no issue.
  "(false)" occurs only as the meaning of a bool value. No brief says what "claim false" means.
* **(f).** Every array is within 1000 per axis and 500 000 values; the largest is 1800 values, in B6-02. Source sizes
  are compared below.
* **(h).** Each brief states the sizes, the axes of each key, what each key measured, and the claim. The time-axis
  words ("sessions in order", "dates in order", "consecutive test days") are axis setting. "Drinking water supplied to
  the cage" in B6-04 says what a (cages,) key measured.
  Claims that name a derived quantity do so where the estimand line requires it: the difference of mean changes
  (B6-05), per-subject slopes (B6-06), the within-subject difference (B6-07), subject means (B6-11) and the difference
  of correlations (B6-12). No brief says that units share anything. No key name gives a variable's role in the error.
* **(i).** In every pair the claim is about the quantity the fixed criterion estimates, as the estimand lines in
  `PRIVATE.json` and `CASE.md` state. In the balanced unit pairs, the group difference (or slope) of unit means equals
  the lower-level point estimate, and only the replicate differs.
* **True exactly when the claim holds (no yes/no).** Every fixed criterion returns True exactly when the claimed
  direction holds and the claim's named test gives a two-sided p < 0.05. Where the claim names the variant, the test
  matches it: Welch in B6-04 and B6-08, pooled in B6-01, 05, 06 and 10, paired in B6-07, Fisher z in B6-12,
  Mann-Whitney in B6-09. B6-09 uses the normal approximation with tie and continuity corrections at 6 versus 6. That
  is a standard implementation (an exact test would also be standard) and the same in both twins.

## Source passages checked by the auditor (online)

* **LAZ18 (full text, Europe PMC).** Confirmed:
  * the offspring-of-treated-dams passage ("Animal experiments");
  * the cage passage (animals in a cage influence each other; housing 2 per cage maximises the number of cages);
  * the drinking-water passage (cages are the experimental units when treatment is applied cage-wise);
  * the cell-culture passage (treatment applied to all cells in a well);
  * the ex vivo passage (N is the number of animals, not the number of slices).

  The literature review reports no study sizes.
* **LAZ10 (full text).** Confirmed:
  * the rotarod example (ten rats, three consecutive days);
  * "observations within each rat are not independent and therefore all of the observations cannot be summed to give
    a total sample size";
  * IC = 0.83 for the example;
  * the inflation of the Type I error with the within-group correlation;
  * "Averaging dependent observations" as the remedy.
* **MAK19 (full text).** Confirmed the section "Interpreting comparisons between two effects without directly comparing
  them", with Figure 1A's two groups of 20 participants.
* **NIE11 (abstract record).** Confirmed "a comparison of two experimental effects requires a statistical test on their
  difference" and the significant / not significant procedure.
* **HUR84.** Not re-read: the PDF fetch returned binary data, and I did not download or extract it. The B6-08 and B6-09
  verdicts rest on the private notes' quotations, which match the paper's definitions of sacrificial and temporal
  pseudoreplication.
  - Remark on B6-09: HUR84 defines temporal pseudoreplication against one unit per treatment. With 6 plots per
    treatment, counting each plot-date sample as a replicate is also HUR84's sacrificial type ("samples ... taken from
    each experimental unit are treated as independent replicates"), so the documented error is present.

## Sizes (item (f)) and the P-2 listing

| Pair | Brief sizes | Compared with | Listing |
|---|---|---|---|
| B6-01 | 20 dams x 8 pups | LAZ18 states none; rodent litters of about 8 | not documented by the source |
| B6-02 | 12 wells x 150 cells | LAZ18 states none (microtitre plates) | not documented by the source |
| B6-03 | 12 x 4 x 25 | LAZ18 states none | not documented by the source |
| B6-04 | 40 cages x 2 | 2 per cage from LAZ18; cage count not stated | not documented by the source |
| B6-05 | 40 subjects | NIE11 abstract states none | not documented by the source |
| B6-06 | 30 x 8 sessions | NIE11 abstract states none | not documented by the source |
| B6-07 | 24 subjects | NIE11 abstract states none | not documented by the source |
| B6-08 | 8 tanks (4 per treatment) x 10 samples | HUR84 sacrificial examples twofold replicated (per the note); samples per unit not stated | not documented by the source |
| B6-09 | 12 plots x 12 dates | HUR84 states none for the setting | not documented by the source |
| B6-10 | 10 rats x 3 days | LAZ10 rotarod example: 10 rats, 3 days | source sizes |
| B6-11 | 16 subjects x 10 days | LAZ10 states none for a correlation | not documented by the source |
| B6-12 | 40 participants | MAK19 Figure 1A: two groups of 20 | source sizes |

No pair was reduced for timing (all estimates are 0.14 to 0.28 s) and none was reduced to the cap.

## Class and subtype remarks (PB §1)

All 12 pairs meet the B-6 rule: non-independent units counted as independent (B6-01 to 04 and 08 to 11), or a
difference claimed from "significant here, not there" (B6-05, 06, 07, 12). None uses a prediction score, so B-2 does
not apply; no selection step makes B-1 apply; no construction makes B-3 apply. The subtype is null. I have no
disagreement.

## Other observations (no verdict changes)

* None of the twelve `CASE.md` files carries the overlap mark or the size ratio that PREREG_PHASE_C §3 lists. The
  overlap mark is the designer's to add (§1); the size ratio is missing in every case and can be read from the table
  above.
* B6-02's faulty twin uses a Welch t test on cell-level 0/1 responses instead of the note's two-proportion z test.
  CASE.md reports this deviation; it keeps the error and its parameters.
* Per-source counts: LAZ18 4 (addendum source), NIE11 3, HUR84 2, LAZ10 2, MAK19 1. Independent read sources are NIE11,
  HUR84, LAZ10 and MAK19, so at least 3 are met. The new-source minimum is met with 4 LAZ18 pairs.
