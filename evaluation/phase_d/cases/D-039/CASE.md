# CASE D-039 (B2A-R5)

## 1. Case
- Id: D-039 (author-local id B2A-R5); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L3.1 (temporal leakage), reserve; mechanism tag L3.1; statistic family: regression-slope.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L3.1: "the test set should not contain any data from a date before the training set." (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: On future months, the monthly forecasts of a ridge regression of y on the three predictors X (penalty 1.0 on standardised predictors, with an intercept) are informative about the monthly outcome: the slope of the ordinary least squares regression of observed y on the forecast, computed over future months, is at least 0.5.
- Data keys:
- `X` float, (months_in_order, features): 3 continuous monthly predictor series, one value per predictor per month
- `y` float, (months_in_order,): continuous monthly outcome
- Sizes: {"months_in_order": 400, "features": 3}

## 4. Mapping
- Private note, faulty: Ridge (lambda 1.0, standardised, intercept) with 5-fold cross-validation, months assigned to folds by a fixed pseudo-random permutation (default_rng(0)); slope of the OLS regression of observed y on the pooled held-out forecasts over all 400 months >= 0.5.
- Private note, fixed: Forward chaining: the model is fitted on months 1 to 200, forecasts months 201 to 240; then on months 1 to 240 (less a 3-month gap), forecasts 241 to 280, and so on up to 400 (5 blocks of 40); slope of observed y on the pooled forecasts over months 201 to 400 >= 0.5.
- Lines of `faulty_body.py` that carry the error: L56-62: months assigned to 5 folds by a fixed permutation (`default_rng(0)`), ridge cross-validation, slope of observed y on the pooled held-out forecasts over all 400 months (`ev` all True). Parameters from the claim; the 0.9 lag-1 autocorrelation is the note's proposal.
- Lines of `fixed_body.py` that carry the correction: L56-63: forward chaining in 5 blocks of 40 months starting at month 201 (`first = n // 2`, `size = n // 10`); the first block is fitted on months 1 to 200, each later block on all earlier months except the last 3 (`s - 3`); slope over months 201 to 400.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the calibration slope of forecasts for months after all fitting months. (private note: Faulty: calibration slope of forecasts for months lying between fitting months. Fixed: calibration slope of forecasts for months after all fitting months.)

## 5. Allowed-guard minimum used
2 forecast months; zero variance of the forecasts (helper `slope` returns None); non-finite values. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.000 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (slowly varying predictor), and guard checks (constant X (the forecasts still differ between blocks through the training mean, so the result is a bool, not None)). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
The note reads 'fitted on months 1 to 200 ... then on months 1 to 240 (less a 3-month gap)'. The 3-month gap is applied from the second block on, as written; the first block has no gap. Applying the gap to the first block too would change only 3 of 200 fitting months. Only the faulty body uses randomness.
Problems: none. Fixed-body revisions after the first run: 0.
