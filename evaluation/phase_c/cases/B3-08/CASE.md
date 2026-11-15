# CASE B3-08

## 1. Identity
Case id B3-08; world id C30; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key ARC81. Passage (as recorded in the part-1 private note): Abstract: 'Type 3, the most common type of mathematic coupling, is direct algebraic coupling between two variables, when one or more of the variables is derived and/or calculated ... The common problem in each type of mathematic coupling is that one variable either directly or indirectly contains the whole or components of the second variable.' (Europe PMC record, PMID 7212790; abstract only.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: In adults with hypertension, the fall in systolic pressure over a 12-week programme is larger in patients with a higher starting pressure: the correlation, across patients, between the fall (first baseline reading minus week-12 reading) and the second baseline reading is at least 0.3.
Data keys:
  * `sbp_baseline_first` (patients,) float: Systolic blood pressure, first reading at the baseline visit, in mmHg.
  * `sbp_baseline_second` (patients,) float: Systolic blood pressure, second reading at the baseline visit, in mmHg.
  * `sbp_week12` (patients,) float: Systolic blood pressure at the week-12 visit, in mmHg.
Sizes: patients = 120; sbp_baseline_first, sbp_baseline_second and sbp_week12 each have shape (120,).

## 4. Mapping
Documented error (note): Pearson correlation across patients between the fall (sbp_baseline_first minus sbp_week12) and sbp_baseline_first; claim holds when r >= 0.3. Documented parameter: the change contains the baseline reading it is related to; each reading has its own measurement error.
Documented correction (note): Pearson correlation between the fall (sbp_baseline_first minus sbp_week12) and sbp_baseline_second, the second reading at the same baseline visit; claim holds when r >= 0.3.
As implemented. Faulty: Pearson correlation across patients between the fall (sbp_baseline_first - sbp_week12) and sbp_baseline_first, holds when r >= 0.3. Fixed: Pearson correlation between the same fall and sbp_baseline_second, holds when >= 0.3.
Guards as coded: n >= 3 in both; zero variance -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: relation of the fall to the baseline level measured by a reading that does not enter the fall. Faulty: relation of the fall to the very reading it is computed from.
Mechanism tag change-vs-baseline, statistic family correlation (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 275/300, fails 25/300, None 0/300 (rate 0.917)
* minus: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control permute_second_baseline_across_patients: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 1/300, fails 299/300, None 0/300 (rate 0.003)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.039 ms, g = 0.028 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
The brief's claim names sbp_baseline_second; the faulty criterion deliberately uses sbp_baseline_first (the documented error), as the private note planned. No other deviation.
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): change-vs-baseline / correlation.
- Allowed-guard minimum (private note): 3 patients (smallest size at which a Pearson correlation is defined); zero variance of the fall or of the second reading -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
