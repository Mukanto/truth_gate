# CASE D-060 (B2A-R3)

## 1. Case
- Id: D-060 (author-local id B2A-R3); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.3 (feature selection on training and test set), reserve; mechanism tag L1.3; statistic family: R-squared.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.3: "Feature selection on the entire dataset results in using information about which feature performs well" (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; sentence cut by the fetch tool).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The 500 features in X predict the outcome y for new samples: the R-squared of a ridge-penalised linear regression of y that uses 20 of the 500 features (penalty 10 on standardised features, with an intercept) is at least 0.10.
- Data keys:
- `X` float, (samples, features): 500 continuous imaging-derived features for each sample
- `y` float, (samples,): continuous symptom score of each sample
- Sizes: {"samples": 100, "features": 500}

## 4. Mapping
- Private note, faulty: The 20 features with the largest absolute Pearson correlation with y are chosen on all 100 rows; then 5-fold cross-validation (fold = i mod 5) of ridge (lambda 10, standardised, intercept) on the 20 chosen features; pooled R-squared = 1 - SSE/SST >= 0.10.
- Private note, fixed: In each fold the 20 features are chosen from the 80 training rows only; ridge fitted on them predicts the 20 held-out rows; pooled R-squared >= 0.10.
- Lines of `faulty_body.py` that carry the error: L57: `sel = top_corr(X, y, 20)` - the 20 features with the largest absolute Pearson correlation with y chosen on all 100 rows, before the fold loop; ridge penalty 10 on them. Parameters from the claim.
- Lines of `fixed_body.py` that carry the correction: L59: `sel = top_corr(X[~te], y[~te], 20)` inside the fold loop (training rows only).
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the out-of-sample R-squared of the whole pipeline (choice plus ridge) for new samples. (private note: Faulty: R-squared of a model whose features were chosen with the held-out outcomes. Fixed: out-of-sample R-squared of the whole pipeline (choice plus ridge) for new samples.)

## 5. Allowed-guard minimum used
2 rows; zero variance of y; non-finite values. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.002 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (20 informative features of 500), and guard checks (no guard run). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
none
Problems: none. Fixed-body revisions after the first run: 0.
