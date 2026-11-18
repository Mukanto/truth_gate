# CASE D-054 (B2A-05)

## 1. Case
- Id: D-054 (author-local id B2A-05); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.3 (feature selection on training and test set); mechanism tag L1.3; statistic family: classification.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.3: "Feature selection on the entire dataset results in using information about which feature performs well" (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; the sentence is cut by the fetch tool). The reference list also cites a paper on inflated accuracy from feature selection in neuropsychiatric biomarkers (ref. 34), not described in the text.
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: Gene-expression features discriminate cases from controls in new subjects: the area under the ROC curve of a linear classifier (ridge regression on the diagnosis coded as plus or minus one, penalty 10 on standardised features) that uses 20 of the 1000 expression features to recover the diagnosis y is at least 0.65.
- Data keys:
- `X` float, (samples, features): expression level of each of 1000 genes for each subject
- `y` bool, (samples,): True where the subject has the diagnosis, False for a control
- Sizes: {"samples": 80, "features": 1000}

## 4. Mapping
- Private note, faulty: The 20 features with the largest absolute two-sample t statistic between y True and y False are chosen on all 80 rows; then 5-fold cross-validation (stratified: fold = rank of the row within its class mod 5) of a ridge classifier (ridge regression on y coded +1/-1, lambda 10, standardised, on the 20 chosen features); pooled AUC over all 80 held-out scores >= 0.65.
- Private note, fixed: In each fold the 20 features are chosen from the 64 training rows only, the ridge classifier is fitted on them, scores the 16 held-out rows; pooled AUC >= 0.65.
- Lines of `faulty_body.py` that carry the error: L88: `sel = top_t(X, y, 20)` - the 20 features with the largest absolute Welch t statistic are chosen on all 80 rows, before the 5-fold loop (L89-91) that fits the ridge classifier on them. Parameters: 20 features, penalty 10, +/-1 coding from the claim; stratified folds from the private note.
- Lines of `fixed_body.py` that carry the correction: L90: `sel = top_t(X[~te], y[~te], 20)` inside the fold loop - the choice uses the training rows only.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the out-of-sample AUC of the whole pipeline (feature choice plus classifier) for new subjects. (private note: Faulty: AUC of a classifier whose features were chosen with the held-out labels. Fixed: the out-of-sample AUC of the whole pipeline (feature choice plus classifier) for new subjects.)

## 5. Allowed-guard minimum used
1 case and 1 control; constant scores (zero variance); non-finite X. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.002 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (20 shifted features), and guard checks (a single class). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
The private note says 'two-sample t statistic'; the Welch form is used (pooled-variance form would pick nearly the same features). Ties in the t ranking are broken by column index (stable sort).
Problems: none. Fixed-body revisions after the first run: 0.
