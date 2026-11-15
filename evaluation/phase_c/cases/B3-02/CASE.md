# CASE B3-02

## 1. Identity
Case id B3-02; world id C53; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key CUR13. Passage (as recorded in the part-1 private note): Abstract: 'In each situation, we want to control for differences in the denominator when the thing we really care about is the numerator. But there is peril lurking in a ratio: only if the relationship between numerator and denominator is a straight line through the origin will the ratio be meaningful.' Correction: regression including analysis of covariance.
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: Among adults, 24-hour urinary albumin excretion increases with age after accounting for 24-hour urinary creatinine excretion: the partial correlation between albumin excretion and age, given creatinine excretion, is at least 0.15.
Data keys:
  * `albumin_excretion` (participants,) float: Urinary albumin excreted over 24 hours, in mg per 24 h, for each participant.
  * `creatinine_excretion` (participants,) float: Urinary creatinine excreted over 24 hours, in mg per 24 h, for each participant.
  * `age` (participants,) float: Age of each participant, in years.
Sizes: participants = 800; albumin_excretion, creatinine_excretion and age each have shape (800,).

## 4. Mapping
Documented error (note): Pearson correlation across participants between age and the albumin-to-creatinine quotient (albumin excretion divided by creatinine excretion); claim holds when r >= 0.15. Documented parameter: numerator-denominator relation not through the origin (albumin excretion has a positive intercept against creatinine excretion), and the denominator varies with age (creatinine excretion falls with age).
Documented correction (note): Partial correlation of albumin excretion and age given creatinine excretion (residuals of each on creatinine excretion, then Pearson r); claim holds when partial r >= 0.15.
As implemented. Faulty: Pearson correlation of age with albumin_excretion / creatinine_excretion, holds when r >= 0.15. Fixed: partial correlation of albumin_excretion and age given creatinine_excretion (residuals on an intercept and creatinine, then Pearson r), holds when >= 0.15. One routine, with an empty covariate list in the faulty version.
Guards as coded: Faulty n >= 3 (Pearson), fixed n >= 4 (one covariate), as the note; zero variance of a variable or residual -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: the correlation between albumin excretion and age at fixed creatinine excretion. Faulty: the correlation between age and the albumin-to-creatinine quotient, which also reflects how creatinine excretion changes with age.
Mechanism tag ratio-vs-denominator-proxy, statistic family correlation (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 300/300, fails 0/300, None 0/300 (rate 1.000)
* minus: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control permute_age_across_participants: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.059 ms, g = 0.065 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.3 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): ratio-vs-denominator-proxy / correlation.
- Allowed-guard minimum (private note): 4 participants (partial correlation with one covariate has 1 residual degree of freedom at n = 4; n = 3 gives a perfect fit); zero variance of any variable or of a residual -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
