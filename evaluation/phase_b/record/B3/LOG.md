# B-3 phase 1 log

## Sources read
I read `PREREG_PHASE_B.md` (all) and `SOURCES.md` (all). I did NOT open the primary papers (PEA97, ARC81, KRO93)
in this phase: the passages and parameters in PRIVATE.json rest on the SOURCES.md descriptions (abstract-level,
"content checked") and my background knowledge of the papers (Pearson's index-correlation formula, about 0.5 with
equal coefficients of variation; Archie's VO2/DO2 Fick example; Kronmal's ratio-standard critique). PRIVATE passages
are therefore located/paraphrased, not verbatim, except the ARC81 phrase quoted in SOURCES.md. Public docs were not read.

## Briefs written (12, none abandoned in the final set)
ARC81: B3-01 (Pearson, VO2/DO2, n=40), B3-02 (Spearman, SVR vs CO, n=100), B3-03 (standardised slope, RV EDV vs EF, n=30),
B3-04 (R squared of change scores, n=24, 2 time points).
PEA97: B3-05 (Pearson, skeletal indices, n=120), B3-06 (Spearman, per-capita emissions/GDP, n=150), B3-07 (standardised
slope, per-area yield/fertilizer, n=90), B3-08 (R squared, per-kg VO2max/power, n=30).
KRO93: B3-09 (slope, ratio outcome, hospitals, n=100), B3-10 (slope, ratio predictor, rats, n=60), B3-11 (Spearman, ratio
outcome, buildings, n=150), B3-12 (R squared, ratio outcome, firms, n=250).

## Drafts abandoned during planning (not written to files)
* Oxygen extraction ratio vs DO2: abandoned; any fixed version still shares DO2 as denominator, so no clean correction.
* "Relative heart/brain weight falls with body weight" with the ratio regressed on its own denominator: abandoned; the
  natural null (isometry) removes the coupling, so the claim would not exercise the error.
* Waist-to-hip ratio as predictor of insulin: abandoned; the null for a ratio predictor is unclear.
* Profit margin vs advertising: abandoned; the sign produced by the construction contradicts a positive claim.
* Change in pressure vs baseline pressure (change score against baseline): not used; its source is OLD62, not counted.
  (ARC81 change-score case B3-04 uses paired changes of two Fick-derived quantities instead.)

## Checks and known risks
* Banned-term scan of BRIEFS.json run after writing (see final message).
* Encoding: no integer codes; B3-04 uses a time axis of length 2; no bool arrays needed.
* Sizes all at most 300 units, at most 5 features.
* Risk (B3-05, B3-06 and the ratio-outcome cases): a world author may set the null at the ratio level (ratios independent),
  which removes the coupling; the briefs name the raw quantities as data keys but cannot prescribe the null. Not bent.
* Risk (ARC81 cases): the coupling in the null world comes through measurement error of the shared terms; its size depends
  on the error the world author declares.

## Update after coordinator request: what I read (replaces the 'Sources read' paragraph above)
* PEA97: read the full text via the archive.org OCR copy of Proc R Soc 60:489-498 (item paper-doi-10_1098_rspl_1896_0076).
  The suggested Zenodo file is a different paper (Brown, Greenwood and Wood 1914, J R Stat Soc 77) and the Royal Society
  PDF link returned an HTML page; neither was used. Documented: the x/y, z/y example and, for femur/humerus and
  tibia/humerus, a correlation 'of about 0.4 to 0.5' at equal coefficients of variation; Proposition III.
* ARC81: abstract on Europe PMC (PMID 7212790), read in full. Full text not read.
* KRO93: abstract on IDEAS/RePEc, read in full. Full text (JSTOR) not read.
* Changes: PRIVATE.json passages replaced by quotes/locations; notes now mark which details are recall (settings such as
  VO2/DO2, per-capita, per-area, body-mass cases are applications, not in the sources); B3-05 faulty text now cites the
  documented 0.4-0.5. Source difference logged for B3-05 (Pearson's denominator is the humerus; brief uses vertebral
  column). No brief was changed: no source contradicts any; BRIEFS.json untouched. The two reported risks are kept.

## Phase 2 (criterion bodies), written by the continuing criterion author
Read: AUTHOR_PHASE2.md, PREREG_PHASE_B.md, SOURCES.md, this class folder (PRIVATE.json, LOG.md, BRIEFS.json via ASSIGNMENT.json,
src/pea.txt for the Pearson quotes), the 12 skeletons, and docs\GATE.md (grep for the probe descriptions only). Nothing else.
All 12 cases were untouched at start (no CASE.md, faulty/fixed identical to skeleton). Bodies were spliced in by work/splice.py
(text replacement of the single `raise NotImplementedError` line); work/check_identity.py confirms the twins equal the skeleton
outside the body (24/24). faulty.py files were only syntax-checked (ast.parse); they were never imported or run.

Design choices common to all cases (made before any pre-check): raw scale as in the faulty ratio; Spearman statistics via ranks
(ties by average rank) and, for the fixed partial Spearman, partial correlation of the ranks; no logs (logs of noise-probe values
would make the fixed criterion UNDEFINED under the probe, which would cap its verdict); guards only for non-finite values and zero
variance (None). Helpers are defined inside the body; no module-level names other than np are read.

Pre-checks (fixed only; 200 plus, 200 minus, 200 control, 200 noise, 5 zeros per case; work/precheck_fixed.py), share of True:
| case | plus | minus | control | noise | revisions |
|---|---|---|---|---|---|
| B3-01 | 0.950 | 0.000 | 0.000 | 0.000 | 0 |
| B3-02 | 0.990 | 0.000 | 0.000 | 0.000 | 1 |
| B3-03 | 0.850 | 0.005 | 0.010 | 0.005 | 1 |
| B3-04 | 0.900 | 0.010 | 0.015 | 0.010 | 0 |
| B3-05 | 1.000 | 0.170 | 0.000 | 0.000 | 1 |
| B3-06 | 1.000 | 0.000 | 0.000 | 0.000 | 1 |
| B3-07 | 0.725 | 0.155 | 0.065 | 0.000 | 1 |
| B3-08 | 0.565 | 0.015 | 0.015 | 0.000 | 1 |
| B3-09 | 0.495 | 0.165 | 0.000 | 0.000 | 1 |
| B3-10 | 1.000 | 0.025 | 0.035 | 0.015 | 1 |
| B3-11 | 0.005 | 0.000 | 0.000 | 0.000 | 1 |
| B3-12 | 0.005 | 0.035 | 0.000 | 0.000 | 1 |
Zeros probe: UNDEFINED (None) 5/5 in every case. Determinism: yes in every case.

The single revision (cases with a division, B3-02, 03, 05-12): the first pre-check of B3-02 showed a RuntimeWarning (0/0 on the zeros
probe); the ratio lines were wrapped in `np.errstate(divide="ignore", invalid="ignore")` in both twins and all cases were re-spliced
from the skeleton. No value or decision changed (B3-02, 03 rates identical before and after). It is counted as one revision for each
case that contains a division.

Problems (recorded, not bent; no skeleton request filed):
* B3-11 and B3-12: the fixed criterion practically never holds in plus (0.005 each). B3-11: the direct occupant effect leaves a
  partial rank correlation of about -0.125 against a -0.3 threshold. B3-12: in the skeleton payroll carries no information about
  leavers beyond headcount (partial R squared mean 0.012), so the claim is true in plus only through the denominator.
* B3-09 (plus 0.495, minus 0.165) and B3-07 (plus 0.725, minus 0.155): collinear covariates and a noisy recorded denominator make the
  fixed coefficient variable. B3-08: plus 0.565 because the planted partial r squared is about equal to the threshold. B3-05: minus
  0.170 because a shared body-size factor and a noisy shared denominator leave a residual partial correlation of about 0.32.
Details and numbers in each CASE.md; descriptive statistics in work/estimates_fixed_stats.py.

Timing: all estimates below 1 s (S = 5; t at most 0.21 ms, g at most 0.08 ms).
