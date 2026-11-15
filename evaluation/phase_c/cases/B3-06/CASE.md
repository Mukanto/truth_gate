# CASE B3-06

## 1. Identity
Case id B3-06; world id C09; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key PEA97. Passage (as recorded in the part-1 private note): Section (1): 'it was convenient to divide the errors made by three observers in estimating a variable quantity by the actual value of the quantity. As a result there appeared a high degree of correlation between three series of absolutely independent judgments.' (OCR text, p. 490.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: Across trials of an estimation task, the estimates of the three observers are positively associated after accounting for the true value of the quantity: the mean, over the three pairs of observers, of the partial correlation between the two observers' estimates given the true value is at least 0.2.
Data keys:
  * `true_value` (trials,) float: Actual value of the quantity presented on each trial, in arbitrary units.
  * `estimates` (trials, observers) float: Estimate of the quantity made by each observer on each trial, in the same units as true_value.
Sizes: trials = 200, observers = 3; true_value has shape (200,); estimates has shape (200, 3).

## 4. Mapping
Documented error (note): Relative error of each observer on each trial: (estimate minus true value) divided by true value; mean over the three observer pairs of the Pearson correlation of relative errors across trials; claim holds when the mean >= 0.2. Documented parameter: three observers, true value varies from trial to trial.
Documented correction (note): For each of the three observer pairs, the partial correlation of the two observers' estimates given true_value across trials; the mean over the three pairs; claim holds when mean >= 0.2.
As implemented. Faulty: relative error (estimate - true_value) / true_value of each observer; mean over the three observer pairs of the Pearson correlation of the relative errors across trials, holds when the mean >= 0.2. Fixed: for each observer pair the partial correlation of the two estimates given true_value, mean over pairs, holds when >= 0.2. Pairs are formed from the columns of estimates.
Guards as coded: Faulty n >= 3, fixed n >= 4 per pair; fewer than 2 observers -> None; zero variance of any residual -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: mean association between observers' estimates after removing the true value (shared judgement tendencies). Faulty: mean correlation of the observers' errors expressed relative to the common true value.
Mechanism tag ratio-shared-denominator, statistic family correlation (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 300/300, fails 0/300, None 0/300 (rate 1.000)
* minus: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control decouple_observers_within_true_value_blocks: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.123 ms, g = 0.032 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.4 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B3-05.
- Mechanism tag / statistic family (private note): ratio-shared-denominator / correlation.
- Allowed-guard minimum (private note): 4 trials (partial correlation with 1 covariate); fewer than 2 observers -> None; zero variance of any residual -> None; non-finite -> None.
- Size ratio (brief size to source size): observers 3/3 = 1.0; trials: source states none.
- The estimand line is in item 4 (criterion author).
