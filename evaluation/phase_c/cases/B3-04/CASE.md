# CASE B3-04

## 1. Identity
Case id B3-04; world id C13; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key CUR13. Passage (as recorded in the part-1 private note): Abstract: 'In each situation, we want to control for differences in the denominator when the thing we really care about is the numerator ... If not, the ratio will misrepresent the true relationship between numerator and denominator.' Regression with the denominator (analysis of covariance) is the correction.
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: In adult mice, liver weight is positively related to kidney weight after accounting for body mass: the coefficient of kidney weight in a linear regression of liver weight on kidney weight and body mass is at least 0.25 (g of liver weight per g of kidney weight).
Data keys:
  * `liver_weight` (mice,) float: Wet liver weight of each mouse, in g.
  * `kidney_weight` (mice,) float: Combined wet weight of both kidneys of each mouse, in g.
  * `body_mass` (mice,) float: Body mass of each mouse, in g.
Sizes: mice = 150; liver_weight, kidney_weight and body_mass each have shape (150,).

## 4. Mapping
Documented error (note): Slope of the simple regression of liver weight divided by body mass on kidney weight divided by body mass (both organ weights standardised to body mass); claim holds when slope >= 0.25. Documented parameter: organ weights are not in direct proportion to body mass (non-zero intercepts); body mass varies widely across mice.
Documented correction (note): Coefficient of kidney weight in the OLS regression of liver weight on kidney weight and body mass; claim holds when coefficient >= 0.25.
As implemented. Faulty: slope of the simple regression of liver_weight / body_mass on kidney_weight / body_mass, holds when >= 0.25. Fixed: coefficient of kidney_weight in the OLS regression of liver_weight on kidney_weight and body_mass, holds when >= 0.25.
Guards as coded: Faulty n >= 3, fixed n >= 4; zero variance of the predictor (after removing the other columns) -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: change in liver weight per unit kidney weight at fixed body mass. Faulty: slope between the two mass-standardised variables, which includes the common body-mass term.
Mechanism tag ratio-shared-denominator, statistic family regression-slope (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 300/300, fails 0/300, None 0/300 (rate 1.000)
* minus: holds 48/300, fails 252/300, None 0/300 (rate 0.160)
* control permute_kidney_within_body_mass_blocks: holds 58/300, fails 242/300, None 0/300 (rate 0.193)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.033 ms, g = 0.019 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
The fixed criterion holds in 16% of minus samples and 19% of the control samples (see the pre-check). The claim's threshold (coefficient >= 0.25) has a sampling standard deviation of about 0.3 at 150 mice in these worlds, so the criterion is a weak test at this size. Not repaired, per AUTHOR_PHASE2_C.md; it stays in the table.
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): ratio-shared-denominator / regression-slope.
- Allowed-guard minimum (private note): 4 mice (3 parameters, 1 residual degree of freedom); zero variance of kidney_weight or collinearity making the coefficient undefined -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
