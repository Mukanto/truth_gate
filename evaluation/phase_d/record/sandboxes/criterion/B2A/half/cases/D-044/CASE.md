# CASE D-044 (B2A-10)

## 1. Case
- Id: D-044 (author-local id B2A-10); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L3.2 (non-independence between training and test samples); mechanism tag L3.2; statistic family: other.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L3.2: "Nonindependence between training and test samples constitutes leakage, unless the scientific claim" [concerns a distribution with the same dependence structure]; example: "uses different observations of the same patient in the training and test sets" (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; sentences cut by the fetch tool).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: For new subjects, a ridge regression of the trial-level outcome y on the features X (penalty 1.0 on standardised features, with an intercept) has a mean absolute error at least 5% below that of predicting the mean outcome: 1 - MAE(model) / MAE(mean predictor) >= 0.05.
- Data keys:
- `X` float, (subjects, trials, features): 25 continuous features computed for each trial of each subject
- `y` float, (subjects, trials): continuous outcome of each trial of each subject
- Sizes: {"subjects": 60, "trials": 30, "features": 25}

## 4. Mapping
- Private note, faulty: The 1800 subject-trial rows are pooled; ridge (lambda 1.0, standardised, intercept) with 5-fold cross-validation, rows assigned to folds by a fixed pseudo-random permutation (default_rng(0)); pooled MAE of held-out predictions; skill = 1 - MAE(model)/MAE(training-fold mean predictor); holds iff >= 0.05.
- Private note, fixed: 5-fold cross-validation by subject (subject index mod 5, all 30 trials of a subject in the same fold; 48 subjects fitted, 12 held out per fold); same ridge and skill; holds iff >= 0.05.
- Lines of `faulty_body.py` that carry the error: L58-60: the 1800 subject-trial rows are pooled and assigned to 5 folds by a fixed permutation (`default_rng(0)`), so trials of one subject appear on both sides. Parameters: penalty 1.0, 5% MAE skill from the claim; the source states no subject or trial counts.
- Lines of `fixed_body.py` that carry the correction: L58: `fold = np.repeat(np.arange(S) % 5, T)` - all trials of a subject in the same fold (subject index mod 5); the rest (ridge, mean predictor of the training folds, MAE skill) is the same code.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: skill for trials of new subjects. (private note: Faulty: skill on trials of subjects that also supplied fitting trials. Fixed: skill for trials of new subjects.)

## 5. Allowed-guard minimum used
at least 2 rows in all, i.e. 1 held-out trial (S*T >= 2); zero MAE of the mean predictor; non-finite values. Private-note `guard_minimum`: 1.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.003 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (y driven by one feature), and guard checks (constant y). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
none
Problems: none. Fixed-body revisions after the first run: 0.
