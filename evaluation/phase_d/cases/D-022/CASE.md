# CASE D-022 (B2A-02)

## 1. Case
- Id: D-022 (author-local id B2A-02); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.1 (no test set); mechanism tag L1.1; statistic family: correlation.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.1: "Using the same dataset for training and testing the model is a textbook example of overfitting" (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; as returned by the fetch tool).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30.
- Data keys:
- `X` float, (samples, features): 10 continuous process readings recorded for each production run
- `y` float, (samples,): continuous quality score of each production run
- Sizes: {"samples": 300, "features": 10}

## 4. Mapping
- Private note, faulty: Second-order polynomial regression (intercept, 10 linear terms, 10 squares, 45 pairwise products = 66 coefficients, standardised X, ordinary least squares) fitted on all 300 rows; Pearson correlation between its fitted values and y on the same 300 rows; holds iff >= 0.30.
- Private note, fixed: 5-fold cross-validation, fold of row i = i mod 5; the same regression fitted on 240 rows predicts the 60 held-out rows; Pearson correlation between the pooled held-out predictions and y over all 300 rows; holds iff >= 0.30.
- Lines of `faulty_body.py` that carry the error: L55: `pred = poly_predict(poly_fit(X, y), X)` - second-order polynomial OLS (66 coefficients: intercept, 10 linear, 10 squares, 45 products; helper `poly_features` returns 66 columns for 10 readings, checked) fitted on all 300 rows, correlation of its fitted values with y on the same rows. Model and size from the claim and the brief; the source states none.
- Lines of `fixed_body.py` that carry the correction: L55-59: 5-fold cross-validation (fold = i mod 5) with the same polynomial fit per fold; the Pearson correlation of the pooled held-out predictions with y over all 300 rows (the post-lines are identical in both files).
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the correlation between out-of-sample predictions and observed outcomes for new runs. (private note: Faulty: the in-sample correlation between fitted and observed outcome (multiple correlation, positive even with no effect). Fixed: the correlation between out-of-sample predictions and observed outcomes for new runs.)

## 5. Allowed-guard minimum used
2 rows; zero variance of the predictions or of y; non-finite values. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.012 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (quadratic term in two readings), and guard checks (constant y). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
none
Problems: none. Fixed-body revisions after the first run: 0.
