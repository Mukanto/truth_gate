# CASE D-027 (B2A-R1)

## 1. Case
- Id: D-027 (author-local id B2A-R1); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.1 (no test set), reserve; mechanism tag L1.1; statistic family: other.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.1: "Using the same dataset for training and testing the model is a textbook example of overfitting" (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; as returned by the fetch tool).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The 25 measurements in X predict the outcome y for new samples: the mean absolute error of an ordinary least squares regression of y on X (with an intercept) is at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10.
- Data keys:
- `X` float, (samples, features): 25 continuous measurements for each sample
- `y` float, (samples,): continuous outcome of each sample
- Sizes: {"samples": 60, "features": 25}

## 4. Mapping
- Private note, faulty: Ordinary least squares (intercept, 25 features) fitted on all 60 rows; skill = 1 - MAE(fitted values)/MAE(mean predictor) on the same 60 rows; holds iff >= 0.10.
- Private note, fixed: 5-fold cross-validation (fold = i mod 5), OLS fitted on 48 rows predicts 12; pooled MAE against the training-fold mean predictor; skill >= 0.10.
- Lines of `faulty_body.py` that carry the error: L39-41: OLS (intercept + 25 features, numpy lstsq) fitted on all 60 rows and evaluated on the same rows; baseline = mean of y over the same rows. Parameters: 25 features, 60 samples from the brief; 10% skill from the claim.
- Lines of `fixed_body.py` that carry the correction: L39-44: 5-fold cross-validation (fold = i mod 5), OLS fitted on 48 rows predicts 12; pooled MAE against the training-fold mean predictor (`fold_mean_baseline`).
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: expected out-of-sample MAE skill. (private note: Faulty: apparent MAE skill of a model fitted to all 60 samples. Fixed: expected out-of-sample MAE skill.)

## 5. Allowed-guard minimum used
zero MAE of the mean predictor; at least 2 samples; non-finite values. Private-note `guard_minimum`: 1.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.001 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (3 informative features), and guard checks (no guard run). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
none
Problems: none. Fixed-body revisions after the first run: 0.
