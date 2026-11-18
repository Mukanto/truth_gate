# CASE D-041 (B2A-R2)

## 1. Case
- Id: D-041 (author-local id B2A-R2); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.2 (pre-processing on training and test set), reserve; mechanism tag L1.2; statistic family: classification.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.2: "Using the entire dataset for any pre-processing steps, such as imputation or over/under sampling, results in leakage." Civil-war case study (Finding 1, Figure 3 caption): one study imputed training and test data together; the source also notes a test set with "only 11" onset instances (PMC10499856).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The country-year indicators in X identify the onset of civil war in new country-years: the area under the ROC curve of a ridge-penalised logistic regression (penalty 1.0 on standardised indicators) of the onset y on X is at least 0.75.
- Data keys:
- `X` float, (samples, features): 25 continuous country-year indicators; an indicator that was not recorded for a country-year is NaN
- `y` bool, (samples,): True where a civil war onset occurred in the country-year
- Sizes: {"samples": 1400, "features": 25}

## 4. Mapping
- Private note, faulty: Missing entries of X are replaced by the mean of that column within the same outcome class (y True or y False), computed over all 1400 rows; then 5-fold cross-validation (stratified, fold = rank within class mod 5) of ridge-penalised logistic regression (lambda 1.0, standardised, Newton iterations, 25 iterations); pooled AUC >= 0.75.
- Private note, fixed: In each fold the missing entries of training and held-out rows are replaced by the column mean of the training rows (no label used); the logistic model is fitted on the training rows; pooled AUC >= 0.75.
- Lines of `faulty_body.py` that carry the error: L93-96: missing entries replaced by the column mean within the same outcome class (y True or False), computed over all 1400 rows, before the stratified 5-fold loop (L97-99). Parameters: ridge penalty 1.0, 25 Newton iterations (helper `logit_fit`), AUC 0.75; the 30% missing rate is the note's proposal.
- Lines of `fixed_body.py` that carry the correction: L95: `Xc = fill(X, col_means(X, ~te))` inside the loop - missing entries of training and held-out rows are replaced by the column mean of the training rows; no label used.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the out-of-sample AUC for new country-years with the label unknown. (private note: Faulty: AUC of scores whose held-out inputs were filled with class-specific values, so that a missing entry reveals the class. Fixed: out-of-sample AUC for new country-years with the label unknown.)

## 5. Allowed-guard minimum used
1 onset and 1 non-onset; constant scores; non-finite scores (a column with no value in the class or fold); infinite values in X. NaN in X is data. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.012 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (two informative indicators, 30% NaN, 61 events), and guard checks (no guard run). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
Penalised logistic regression is written as: Newton iterations from zero, intercept unpenalised, penalty (lambda/2) times the sum of squared coefficients (gradient `+ lambda * w`) on columns standardised with the fitting rows; the note says only 'lambda 1.0, 25 iterations'. The score is the linear predictor (monotone in the probability).
Problems: none. Fixed-body revisions after the first run: 0.
