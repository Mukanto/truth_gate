# CASE D-014 (B2A-03)

## 1. Case
- Id: D-014 (author-local id B2A-03); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.2 (pre-processing on training and test set); mechanism tag L1.2; statistic family: R-squared.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.2: "Using the entire dataset for any pre-processing steps, such as imputation or over/under sampling, results in leakage." (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The laboratory values in X predict the outcome y for new patients: the R-squared of a ridge regression of y on the 20 laboratory values (penalty 1.0 on standardised values, with an intercept) is at least 0.10.
- Data keys:
- `X` float, (samples, features): 20 laboratory values per patient; a value that was not measured for a patient is NaN
- `y` float, (samples,): continuous clinical outcome of each patient
- Sizes: {"samples": 250, "features": 20}

## 4. Mapping
- Private note, faulty: Missing entries of X are filled by iterative regression imputation (5 sweeps; each incomplete column regressed by ridge, lambda 1.0, on y and all other columns, fitted on rows where the column is observed, applied to rows where it is missing; start from column means) run once on all 250 rows, using y of every row including rows later held out. Then 5-fold cross-validation (fold = i mod 5) of ridge (lambda 1.0, standardised) on the completed X; pooled R-squared = 1 - SSE/SST; holds iff >= 0.10.
- Private note, fixed: Inside each fold the imputer (same 5-sweep ridge scheme, but on the columns of X only, y not used) is fitted on the 200 training rows and applied to the training and the 50 held-out rows; then ridge is fitted on the 200 completed training rows and predicts the held-out rows; pooled R-squared; holds iff >= 0.10.
- Lines of `faulty_body.py` that carry the error: L71: `Xc = impute(X, np.ones(n, dtype=bool), y[:, None])` - the iterative ridge imputation (helper `impute`, 5 sweeps = default `sweeps=5`, ridge penalty 1.0, start from column means) is run once on all 250 rows with y as an extra regressor, before the 5-fold loop (L72-74) that runs ridge on the completed X. Parameters (5 sweeps, penalty 1.0, y used) from the private note; the proposed 25% missing rate is the note's, not a source value.
- Lines of `fixed_body.py` that carry the correction: L73: `Xc = impute(X, ~te, np.empty((n, 0)))` inside the fold loop - regressions fitted on the training rows only, no y (empty auxiliary block), applied to training and held-out rows; column means from the training rows.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the out-of-sample R-squared for new patients whose outcome is unknown when their missing values are filled. (private note: Faulty: R-squared of predictions whose held-out feature values were completed using the held-out outcome. Fixed: the out-of-sample R-squared for new patients whose outcome is unknown when their missing values are filled.)

## 5. Allowed-guard minimum used
2 rows; zero variance of y; infinite values in X or non-finite y; a column with no observed value in the fitting rows gives non-finite predictions, so R-squared is non-finite and None is returned. NaN in X is data (missing values), not a guard. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.034 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (5 informative columns, 25% NaN), and guard checks (a fully missing column (returns None, with numpy RuntimeWarnings from empty means)). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
Columns are updated in ascending order within a sweep, each regression seeing the current filled values (Gauss-Seidel); the private note does not fix the order. In the faulty body the held-out rows are the same rows as the fitting rows, as the note says (imputation once on all rows).
Problems: none. Fixed-body revisions after the first run: 0.
