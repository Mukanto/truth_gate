# CASE D-029 (B2A-06)

## 1. Case
- Id: D-029 (author-local id B2A-06); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.4 (duplicates); mechanism tag L1.4; statistic family: other.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.4: "If a dataset with duplicates is used for the purposes of training and evaluating an ML model," [the rest: the same data could exist in the training set and the test set] (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; sentence cut by the fetch tool).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised measurements) of the value y on the measurements X predicts y for new entries with a mean absolute error at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10.
- Data keys:
- `X` float, (rows, features): 8 continuous property measurements recorded for each registry entry
- `y` float, (rows,): continuous target value recorded for each registry entry
- Sizes: {"rows": 600, "features": 8}

## 4. Mapping
- Private note, faulty: 1-nearest-neighbour regression (Euclidean distance on X standardised with the training mean and sd) under 5-fold cross-validation (fold = i mod 5) on all 600 rows as given; pooled mean absolute error of the held-out predictions; skill = 1 - MAE(model)/MAE(training-fold mean predictor); holds iff skill >= 0.10.
- Private note, fixed: Rows with an identical X vector (standardised distance < 1e-8) are reduced to the first of each group (later rows dropped) before the same 5-fold cross-validation on the remaining rows; skill >= 0.10.
- Lines of `faulty_body.py` that carry the error: L54-63 (the common post block, identical in the fixed file apart from the reduction inserted before it): `fold = np.arange(n) % 5`, `cv_nn` and the skill on all 600 rows as given, repeated records kept. The error is the absence of any reduction of repeated records before the cut. Parameters: one neighbour, standardised distance, 10% MAE skill from the claim; the share of exact repeats is the world author's (the note's 0.3 is proposed; the source states none).
- Lines of `fixed_body.py` that carry the correction: L54-62: rows with an identical X vector (squared standardised distance < 1e-16, i.e. distance < 1e-8, computed by direct differences so identical rows give exactly 0) are reduced to the first of each group; then n is recomputed and the same cross-validation runs on the remaining rows.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: skill for new distinct entries. (private note: Faulty: skill on held-out rows many of which have an identical record in the fitting rows. Fixed: skill for new distinct entries.)

## 5. Allowed-guard minimum used
2 rows (before and after the reduction; one-nearest-neighbour cross-validation needs a held-out and a fitting row, so 2 rather than the note's 1 held-out row); zero MAE of the mean predictor; non-finite values. Private-note `guard_minimum`: 1.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.014 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (X1 squared plus X2 (array also contains 180 exact repeats)), and guard checks (constant y). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
Guard minimum 2 rows instead of 1 (see item 5); the guard_minimum 1 of the note counts held-out rows.
Problems: none. Fixed-body revisions after the first run: 0.
