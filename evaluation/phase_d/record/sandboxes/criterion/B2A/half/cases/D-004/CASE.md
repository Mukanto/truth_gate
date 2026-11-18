# CASE D-004 (B2A-09)

## 1. Case
- Id: D-004 (author-local id B2A-09); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L3.1 (temporal leakage); mechanism tag L3.1; statistic family: other.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L3.1: "the test set should not contain any data from a date before the training set." (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: On future days, a ridge regression forecast of the outcome y from the day's five predictors X (penalty 1.0 on standardised predictors, with an intercept, one model for all stations) has a squared error at least 5% below that of the persistence forecast (the previous day's outcome at the same station), with squared errors pooled over stations: 1 - MSE(model) / MSE(persistence) >= 0.05.
- Data keys:
- `X` float, (stations, days_in_order, features): 5 continuous daily predictors recorded at each station on each day
- `y` float, (stations, days_in_order): continuous daily outcome measured at each station
- Sizes: {"stations": 40, "days_in_order": 250, "features": 5}

## 4. Mapping
- Private note, faulty: All 10,000 station-days pooled; ridge (lambda 1.0, standardised, intercept, one model for all stations) with 5-fold cross-validation, station-days assigned to folds by a fixed pseudo-random permutation (default_rng(0)); skill = 1 - MSE(model)/MSE(persistence) over the station-days from day 2 on, persistence being y of the previous day at the same station; holds iff >= 0.05.
- Private note, fixed: Ridge fitted on all stations for days 1 to 175 (first 70% of days); forecasts days 176 to 250; MSE of model and of persistence (y of day t-1, same station; for day 176 the day-175 value) over those 40 x 75 = 3000 station-days; skill >= 0.05.
- Lines of `faulty_body.py` that carry the error: L48-54 and L56: the 10,000 station-days are pooled, assigned to 5 folds by a fixed permutation (`default_rng(0)`), ridge cross-validation; skill over days 2 to T (`ev[:, 1:]`). Parameters: penalty 1.0, 5% skill, persistence baseline from the claim; the source states no autocorrelation.
- Lines of `fixed_body.py` that carry the correction: L48-51 and L53: ridge fitted on all stations for the first `(7 * T) // 10` = 175 days, forecasts the remaining 75 days (`ev[:, cut:]`); persistence = y of the previous day (for the first forecast day the last fitting day's y).
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: skill on days after every fitting day. (private note: Faulty: skill versus persistence on station-days that lie between fitting days at the same and other stations. Fixed: skill on days after every fitting day.)

## 5. Allowed-guard minimum used
a forecast day must exist (`ev.any()`); zero MSE of the persistence forecast; non-finite values. Private-note `guard_minimum`: 1.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.001 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (y driven by X1), and guard checks (constant y). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
The 70% split is computed as `(7 * T) // 10` = 175 days for T = 250 (integer arithmetic). Only the faulty body uses randomness.
Problems: none. Fixed-body revisions after the first run: 0.
