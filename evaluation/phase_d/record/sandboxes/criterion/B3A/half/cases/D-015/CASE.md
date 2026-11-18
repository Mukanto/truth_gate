# CASE D-015 (author-local id B3A-14)

## 1. Case
- Case id: D-015 (brief author's local id B3A-14)
- Class: B-3, coupling by construction (half A)
- Tag: change-vs-baseline; statistic family: R-squared; role reserve (CHI13, 2 of 2)

## 2. Source and documenting passage
- Source key: CHI13
- Passage: 'The corresponding correlation r Blomqvist was estimated.' with b_Blomqvist = (b_crude + k)/(1 - k), k = variance of measurement error / total variance = 1 - ICC between (short-term) repeated measurements (Analyses, Europe PMC full text)
- Read: The brief author read it in the Europe PMC full-text XML (saved in `fetched/chi13.txt`); I re-read the 'Analyses' passage on the five methods there (random-effects, crude, Oldham, repeated measurement, Blomqvist). I fetched nothing online.

## 3. Brief
- Claim: Baseline BMI explains at least 10% of the variance in the change in BMI between baseline and follow-up (R-squared of at least 0.10).
- Data keys:
  - `bmi_baseline` (children,) float: BMI of each child at the baseline visit, in kg/m2
  - `bmi_baseline_retest` (children,) float: a second BMI measurement of each child at the baseline visit, in kg/m2
  - `bmi_followup` (children,) float: BMI of each child at the follow-up visit five years after baseline, in kg/m2
- Sizes: {"children": 500}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 66: `k = 0.0`
  - R-squared of the crude regression of change on baseline (squared crude correlation, the share of variance of observed change explained by observed baseline) compared with 0.10 (`>=`); the error-variance share is ignored (`k = 0` in the shared helper `_change_stats`). Parameters: none numeric in the source. Documented in CHI13 (Analyses (2)).
- **Fixed body, the correction** (`fixed_body.py`): lines 66-69: `icc = _corr(u1, u1b)` ... `k = 1.0 - icc`
  - Squared Blomqvist-adjusted correlation: k = 1 - corr(bmi_baseline, bmi_baseline_retest) (the source's k = 1 - ICC between short-term repeated measurements), adjusted slope (b_crude + k)/(1 - k), converted to a correlation with the SD of the true baseline (SD of baseline times sqrt(1 - k)) and the SD of the true change (variance of the observed change minus 2 k times the baseline variance, equal error variance at both visits); squared and compared with the same 0.10 (`>=`). Documented in CHI13 Analyses (5).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Share of the variance of the true change explained by the true baseline level (r_Blomqvist squared).

## 5. Allowed-guard minimum
2 children, non-finite values, zero variance of the baseline, of the change or of the retest reading, adjusted correlation not finite (k = 1, or a true-change variance estimate that is not positive).

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`. Estimator check (n = 200000, known truth): true corr(level, change) -0.6270, crude -0.6542, adjusted -0.6287 (k 0.4994). On the independent random smoke arrays the result was None in some draws (k >= 1 or non-positive true-change variance) and bool in others.
- Smoke result (3 arrays): `D-015 types ['NoneType', 'bool'] max_time_s 0.00013`
- Fixed-body revisions: 1 revision of the fixed body after its first run (the shared helper `_change_stats` returned None whenever the correlation was not finite; it now returns both numbers and each caller checks the one it uses; the criterion's docstring was extended). Both files changed alike.

## 7. Deviations from the private note, and problems
The source says only 'the corresponding correlation r Blomqvist was estimated'; the conversion to a correlation follows the private note ('with the SDs of the true baseline and change') and the derivation above, which is mine. Verified on my own large array that it recovers the known value (see runs). A non-positive estimated true-change variance (undefined correlation) returns None as a non-finite result.
