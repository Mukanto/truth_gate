# CASE D-066 (B2A-R4)

## 1. Case
- Id: D-066 (author-local id B2A-R4); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.4 (duplicates; oversampling by copying, under the task's tie-break), reserve; mechanism tag L1.4; statistic family: classification.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.2 text: "...pre-processing steps, such as imputation or over/under sampling, results in leakage." Under the task's tie-break, oversampling by copying rows is L1.4; L1.4: "If a dataset with duplicates is used for the purposes of training and evaluating an ML model," [...] (PMC10499856).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65.
- Data keys:
- `X` float, (samples, features): 15 continuous clinical measurements for each patient
- `y` bool, (samples,): True where the patient has the rare outcome
- Sizes: {"samples": 1000, "features": 15}

## 4. Mapping
- Private note, faulty: Rows with y True are copied (sampling with replacement, default_rng(0)) until the two classes have equal size, on all 1000 rows, before the data are cut; 5-fold cross-validation (fold = i mod 5 over the enlarged table) of 1-nearest-neighbour classification (Euclidean, standardised); balanced accuracy over the held-out rows of the enlarged table >= 0.65.
- Private note, fixed: 5-fold cross-validation on the original 1000 rows (stratified, fold = rank within class mod 5); copies of the True rows are made only among the training rows of each fold; balanced accuracy on the untouched held-out original rows >= 0.65.
- Lines of `faulty_body.py` that carry the error: L50-55 and L58-59: the True rows are copied (`rng.choice(..., replace=True)` with `default_rng(0)`) until the classes are equal, on all 1000 rows, before the cut; folds = i mod 5 over the enlarged table; balanced accuracy over its held-out rows (`ya`, `pred`). Parameters: one neighbour, 0.65 from the claim; the 8% minority share is the note's proposal.
- Lines of `fixed_body.py` that carry the correction: L50-51 and L54-59: stratified folds on the original rows, copies made inside each fold among the training rows only, held-out rows untouched; balanced accuracy over the original rows.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: balanced accuracy for new patients drawn with the original class balance. (private note: Faulty: balanced accuracy on held-out rows that include copies of rows in the fitting set. Fixed: balanced accuracy for new patients drawn with the original class balance.)

## 5. Allowed-guard minimum used
at least 2 rows in each class (covers 'a class absent in a held-out pool'); non-finite X. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.010 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (2 informative columns of 15, 69 positives; it returned False), and guard checks (a single positive; the separate script `work\sanity_d066.py` then ran a clustered rare class (103 positives; True) and noise (False)). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
The note says rows with y True are copied; if True were the majority the copy count is 0 (`max(..., 0)`) and nothing is copied. On the planted-signal array of `sanity_fixed.py` (signal in 2 of 15 columns) the fixed body returned False; this is a property of one-nearest-neighbour in 15 dimensions with noise columns, not an error in the code; a clustered rare class returned True in `sanity_d066.py`.
Problems: none. Fixed-body revisions after the first run: 0.
