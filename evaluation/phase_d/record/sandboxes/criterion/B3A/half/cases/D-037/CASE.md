# CASE D-037 (author-local id B3A-13)

## 1. Case
- Case id: D-037 (brief author's local id B3A-13)
- Class: B-3, coupling by construction (half A)
- Tag: change-vs-baseline; statistic family: regression-slope; role reserve (CHI13, 1 of 2)

## 2. Source and documenting passage
- Source key: CHI13
- Passage: 'Blomqvist proposed another method which consists in adjusting the estimated regression coefficient of change on baseline value accounting directly for measurement error [...] adjusted regression coefficient = (crude regression coefficient + k)/(1 - k), with k = variance of measurement error/total variance.' (Europe PMC full text)
- Read: The brief author read it in the Europe PMC full-text XML (saved in `fetched/chi13.txt`); I re-read the 'Analyses' passage on the five methods there (random-effects, crude, Oldham, repeated measurement, Blomqvist). I fetched nothing online.

## 3. Brief
- Claim: The expected change in BMI between baseline and follow-up is smaller for children with a higher baseline BMI: each additional 1 kg/m2 of baseline BMI goes with a change in BMI that is at least 0.2 kg/m2 smaller (slope of at most -0.2).
- Data keys:
  - `bmi_baseline` (children,) float: BMI of each child at the baseline visit, in kg/m2
  - `bmi_followup` (children,) float: BMI of each child at the follow-up visit five years after baseline, in kg/m2
  - `bmi_retest` (retest_children, retest_sessions) float: BMI of each child of a test-retest sample at two sessions a few days apart, in kg/m2
- Sizes: {"children": 500, "retest_children": 100, "retest_sessions": 2}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 55: `k = 0.0`
  - Crude regression of change (follow-up minus baseline) on baseline BMI, slope compared with -0.2 (`<=`); the error-variance share is ignored, which is `k = 0` in the shared helper `_change_stats` (adjusted slope (b_crude + k)/(1 - k) with k = 0 is b_crude). Parameters: none numeric in the source. Documented in CHI13 (Analyses (2) and (5): b_crude).
- **Fixed body, the correction** (`fixed_body.py`): line 55: `k = float(np.mean(np.var(rt, axis=1, ddof=1)) / np.var(u1, ddof=1))`
  - Blomqvist's adjusted slope (b_crude + k)/(1 - k), with k = error variance / total variance; the error variance is the mean within-child variance of the retest sample (half the mean squared difference for two sessions) and the total variance is the variance of bmi_baseline. Same -0.2 (`<=`). Documented in CHI13 Methods and Analyses (5).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Slope of the true change on the true baseline level.

## 5. Allowed-guard minimum
2 children in the main sample and in the retest sample, 2 sessions, non-finite values, zero variance of the baseline (or of the change), non-finite adjusted slope (k = 1).

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`. Estimator check (n = 200000, known truth): true slope -0.5019, crude -0.7521, adjusted -0.5048; k from a retest sample 0.5016 (true 0.4999).
- Smoke result (3 arrays): `D-037 types ['bool'] max_time_s 0.00011`
- Fixed-body revisions: 1 revision of the fixed body after its first run (same helper change as D-015: the first version returned None when the correlation was not finite although this claim uses only the slope; D-037 returned None on some independent random arrays for this reason). Both files changed alike.

## 7. Deviations from the private note, and problems
none. The faulty body passes the literal `k = 0.0` so that the helper, identical in both files, reduces to the crude slope; the retest array is read and checked for finite values in both files but only used in the fixed one.
