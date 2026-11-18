# CASE D-005 (B2A-01)

## 1. Case
- Id: D-005 (author-local id B2A-01); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.1 (no test set); mechanism tag L1.1; statistic family: R-squared.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.1: "Using the same dataset for training and testing the model is a textbook example of overfitting" (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; as returned by the fetch tool, the rest of the sentence not verified verbatim).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The measurements in X carry information about the outcome y: the R-squared (coefficient of determination) of a ridge regression of y on X (penalty 1.0 on standardised measurements, with an intercept), evaluated on new samples, is at least 0.10.
- Data keys:
- `X` float, (samples, features): panel of 150 continuous biomarker measurements for each sample
- `y` float, (samples,): continuous clinical score of each sample
- Sizes: {"samples": 100, "features": 150}

## 4. Mapping
- Private note, faulty: Ridge regression (lambda 1.0 on standardised X, centred y, intercept) is fitted on all 100 rows; R-squared = 1 - SSE/SST of its fitted values on the same 100 rows; holds iff >= 0.10. No held-out rows.
- Private note, fixed: 5-fold cross-validation, fold of row i = i mod 5; ridge (lambda 1.0, standardisation fitted on the training folds) fitted on 80 rows, predicts the 20 held-out rows; pooled R-squared = 1 - SSE/SST over all 100 held-out predictions (SST around the pooled mean of y); holds iff >= 0.10.
- Lines of `faulty_body.py` that carry the error: L44: `pred = ridge_predict(ridge_fit(X, y, 1.0), X)` - the model is fitted on all 100 rows and scored on the same rows (R-squared of the fitted values). Parameters: ridge penalty 1.0, standardised measurements, intercept (all in the claim); 100 x 150 from the brief; the source states no sample size or feature count (private note: `sizes_note`).
- Lines of `fixed_body.py` that carry the correction: L44-48: 5-fold cross-validation, fold of row i = i mod 5, one ridge fit per fold (standardisation fitted inside `ridge_fit` on the training rows), pooled held-out predictions; the R-squared lines after it (SST around the mean of y over all rows) are identical in both files.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: expected out-of-sample R-squared of the ridge model fitted on 80 samples and applied to new samples (the private note's fixed estimand). (private note: Faulty: the apparent (resubstitution) R-squared of a model fitted to all 100 samples. Fixed: the expected out-of-sample R-squared of the same model fitted on 80 samples and applied to new samples.)

## 5. Allowed-guard minimum used
2 rows; zero variance of y; non-finite values in X or y. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.001 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (150 features, 10 informative), and guard checks (NaN in X, constant y). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
none
Problems: none. Fixed-body revisions after the first run: 0.
