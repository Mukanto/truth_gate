# CASE B3-12

## 1. Identity
Case id B3-12; world id C25; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key KRO93. Passage (as recorded in the part-1 private note): Abstract (EconPapers/RePEc record of doi:10.2307/2983064): 'It is shown that the use of ratios in regression analyses can lead to incorrect or misleading inferences. A recommendation is made that the use of ratios in regression analyses be avoided.' (secondary: a 2026 open paper, PMC13633979, cites KRO93 for regression with the denominator as a covariate in place of a ratio.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: Over a ten-year record, monthly hospital admissions rose after accounting for catchment population: in a linear regression of monthly admissions on time and catchment population, the coefficient of time is positive and significant at the one-sided 5% level (t test).
Data keys:
  * `admissions` (months,) float: Number of hospital admissions in each month.
  * `population` (months,) float: Catchment population in each month, in thousands.
  * `time_years` (months,) float: Time of each month in years since the start of the record.
Sizes: months = 120; admissions, population and time_years each have shape (120,).

## 4. Mapping
Documented error (note): OLS regression of admissions divided by population on time_years; one-sided t test of the time coefficient, claim holds when the time coefficient is positive and one-sided p < 0.05. Documented parameter: a ratio used as the dependent variable of a regression whose predictor varies with the denominator.
Documented correction (note): OLS regression of admissions on time_years and population; claim holds when the coefficient of time_years is positive and one-sided p < 0.05.
As implemented. Faulty: OLS of admissions / population on time_years, one-sided t test of the time coefficient (positive and p < 0.05). Fixed: OLS of admissions on time_years and population, same one-sided t test of the time coefficient.
Guards as coded: Faulty residual df >= 1 (n >= 3), fixed n >= 4; zero variance of time_years (after removing population) or perfect fit -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: yearly change in admissions at fixed catchment population. Faulty: yearly change in the per-population admission rate, which also reflects how population itself changes over the record.
Mechanism tag ratio-vs-denominator-proxy, statistic family regression-slope (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 286/300, fails 14/300, None 0/300 (rate 0.953)
* minus: holds 35/300, fails 265/300, None 0/300 (rate 0.117)
* control permute_time_across_months: holds 14/300, fails 286/300, None 0/300 (rate 0.047)
* control reverse_time: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 14/300, fails 286/300, None 0/300 (rate 0.047)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.237 ms, g = 0.065 ms, S = 6 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.8 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
The fixed criterion holds in 11.7% of minus samples (nominal 5%): the skeleton's months carry autocorrelated variation, which the ordinary one-sided t test of the fixed criterion (the rule in the claim) does not model. Not bent; it stays in the table.
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B3-09.
- Mechanism tag / statistic family (private note): ratio-vs-denominator-proxy / regression-slope.
- Allowed-guard minimum (private note): 4 months (3 parameters, 1 residual degree of freedom); zero variance of time_years or collinearity -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
