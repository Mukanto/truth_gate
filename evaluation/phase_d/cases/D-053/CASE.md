# CASE D-053 (author-local id B3A-03)

## 1. Case
- Case id: D-053 (brief author's local id B3A-03)
- Class: B-3, coupling by construction (half A)
- Tag: change-vs-baseline; statistic family: correlation; role pair (CHI13 pair 1 of 2)

## 2. Source and documenting passage
- Source key: CHI13
- Passage: 'Because the initial value (Y1) and the change from initial value (Y2 - Y1) share a common variable, there is a mathematical coupling between Y1 and Y2 - Y1.' (Glossary, Europe PMC full text). Correction: 'one may assess the association between U2 - U1 and another measure obtained relatively close in time to U1 (16), e.g., a repeated measure U1bis.'
- Read: The brief author read it in the Europe PMC full-text XML (saved in `fetched/chi13.txt`); I re-read the 'Analyses' passage on the five methods there (random-effects, crude, Oldham, repeated measurement, Blomqvist). I fetched nothing online.

## 3. Brief
- Claim: Across children, BMI at baseline and the subsequent change in BMI are negatively correlated: the correlation between the BMI level at baseline and the change in BMI by follow-up is at most -0.25.
- Data keys:
  - `bmi_baseline` (children,) float: BMI of each child at the baseline visit, in kg/m2
  - `bmi_baseline_retest` (children,) float: a second BMI measurement of each child at the baseline visit, in kg/m2
  - `bmi_followup` (children,) float: BMI of each child at the follow-up visit five years after baseline, in kg/m2
- Sizes: {"children": 500}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 41: `x = u1`
  - Crude method: Pearson correlation of the observed baseline BMI with the change (follow-up minus baseline), compared with -0.25 (`<=`). Parameters: none numeric beyond the source's scenario (ICC 95% or 50% as the world's error size); documented in CHI13, Table 1 and Analyses (2) 'Crude method', and the Glossary on mathematical coupling.
- **Fixed body, the correction** (`fixed_body.py`): line 41: `x = u1b`
  - Repeated measurement method: Pearson correlation of the second baseline reading (U1bis) with the same change, compared with the same -0.25 (`<=`). Documented in CHI13 Table 1 and Analyses (4).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Correlation between the baseline level (measured by the second reading, whose error is not shared with the change) and the change.

## 5. Allowed-guard minimum
2 children, non-finite values, zero variance of the used baseline reading or of the change (inside `_corr`). Same as the note.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-053 types ['bool'] max_time_s 0.00006`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none.
