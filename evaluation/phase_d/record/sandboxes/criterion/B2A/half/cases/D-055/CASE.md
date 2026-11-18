# CASE D-055 (B2A-08)

## 1. Case
- Id: D-055 (author-local id B2A-08); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L3.1 (temporal leakage); mechanism tag L3.1; statistic family: correlation.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L3.1: "the test set should not contain any data from a date before the training set." (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The daily predictors X carry information about the daily outcome y on future days: the Pearson correlation between y and the prediction of a ridge regression of y on X (penalty 1.0 on standardised predictors, with an intercept), computed over future days, is at least 0.20.
- Data keys:
- `X` float, (days_in_order, features): 6 continuous daily predictor series, one value per predictor per day
- `y` float, (days_in_order,): continuous daily outcome
- Sizes: {"days_in_order": 1000, "features": 6}

## 4. Mapping
- Private note, faulty: Ridge regression (lambda 1.0, standardised, intercept) with 5-fold cross-validation in which days are assigned to folds by a fixed pseudo-random permutation (numpy default_rng(0)); Pearson correlation between pooled held-out predictions and y over all 1000 days >= 0.20.
- Private note, fixed: Forward chaining: days are cut into 6 consecutive blocks; for blocks 2 to 6 the model is fitted on all days of the earlier blocks except the last 5 days before the block, and predicts the block; Pearson correlation between the pooled forecasts and y over blocks 2 to 6 (days 168 to 999) >= 0.20.
- Lines of `faulty_body.py` that carry the error: L56-62: days assigned to 5 folds by a fixed pseudo-random permutation (`default_rng(0)`), ridge fitted on days around the held-out ones, correlation over all 1000 days (`ev` all True). Parameters from the claim and the private note; the autocorrelation (0.8) is the note's proposal, the source states none.
- Lines of `fixed_body.py` that carry the correction: L56-60: forward chaining - `np.array_split(np.arange(n), 6)[1:]` gives the blocks 2 to 6; the model is fitted on all days before the block except the last 5 (`blk[0] - 5`), predicts the block; correlation over blocks 2 to 6 only (`ev`).
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the correlation between forecasts and outcomes on days after all fitting days. (private note: Faulty: correlation between predictions and outcomes on days that lie between fitting days. Fixed: correlation between forecasts and outcomes on days after all fitting days.)

## 5. Allowed-guard minimum used
2 days; zero variance of the forecasts or y; non-finite values. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.001 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (slowly varying predictor), and guard checks (no guard run). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
Block sizes from `np.array_split` of 1000 into 6 are 167, 167, 167, 167, 166, 166, so the first forecast day is index 167 (the 168th day) and the last is index 999; the note's 'days 168 to 999' is read this way. Only the faulty body uses randomness (`default_rng(0)`); the fixed body has none.
Problems: none. Fixed-body revisions after the first run: 0.
