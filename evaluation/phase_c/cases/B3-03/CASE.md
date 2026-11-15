# CASE B3-03

## 1. Identity
Case id B3-03; world id C39; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key CUR13. Passage (as recorded in the part-1 private note): Abstract: 'we compute a ratio-a numerator divided by a denominator-to compute a proportion for some biological response or to derive some standardized variable ... regression techniques-these include analysis of covariance-are versatile.' (Europe PMC record, PMID 24022766.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: In patients attending a hypertension clinic, left ventricular mass adds explanatory power for systolic blood pressure beyond body surface area: the gain in R-squared when left ventricular mass is added to a linear regression of systolic pressure on body surface area is at least 0.05.
Data keys:
  * `lv_mass` (patients,) float: Left ventricular mass of each patient from echocardiography, in g.
  * `body_surface_area` (patients,) float: Body surface area of each patient, in square metres.
  * `systolic_bp` (patients,) float: Resting systolic blood pressure of each patient, in mmHg.
Sizes: patients = 300; lv_mass, body_surface_area and systolic_bp each have shape (300,).

## 4. Mapping
Documented error (note): R-squared of the simple regression of systolic pressure on left ventricular mass divided by body surface area (the standardised variable as the only predictor); claim holds when R-squared >= 0.05. Documented parameter: numerator-denominator relation not through the origin (LV mass has a non-zero intercept against body surface area), outcome varies with the denominator.
Documented correction (note): Gain in R-squared when left ventricular mass is added to the regression of systolic pressure on body surface area (R2 of the 2-predictor model minus R2 of the 1-predictor model); claim holds when gain >= 0.05.
As implemented. Faulty: R-squared of systolic_bp regressed on the quotient lv_mass / body_surface_area, holds when >= 0.05. Fixed: R-squared of systolic_bp on body_surface_area and lv_mass minus R-squared on body_surface_area alone, holds when the gain >= 0.05.
Guards as coded: Faulty n >= 3, fixed n >= 4 (2 predictors plus intercept, 1 residual df); zero variance of a variable entering the statistic -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: extra variance of systolic pressure explained by left ventricular mass once body surface area is in the model. Faulty: variance of systolic pressure explained by the mass-to-surface-area quotient alone, which carries information about body surface area.
Mechanism tag ratio-vs-denominator-proxy, statistic family R-squared (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 298/300, fails 2/300, None 0/300 (rate 0.993)
* minus: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control permute_lv_mass: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control permute_lv_mass_residual: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.081 ms, g = 0.035 ms, S = 6 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.3 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): ratio-vs-denominator-proxy / R-squared.
- Allowed-guard minimum (private note): 4 patients (2 predictors plus intercept: 1 residual degree of freedom; the R-squared gain is defined from n = 4); zero variance of any variable -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
