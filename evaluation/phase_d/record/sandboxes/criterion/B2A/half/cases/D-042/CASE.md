# CASE D-042 (B2A-07)

## 1. Case
- Id: D-042 (author-local id B2A-07); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.4 (duplicates); mechanism tag L1.4; statistic family: correlation.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.4: "If a dataset with duplicates is used for the purposes of training and evaluating an ML model," [the rest: the same data could exist in the training set and the test set] (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856; sentence cut by the fetch tool).
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30.
- Data keys:
- `X` float, (records, features): 20 continuous molecular descriptors recorded for each compound record
- `y` float, (records,): continuous activity response measured for each compound record
- Sizes: {"records": 1200, "features": 20}

## 4. Mapping
- Private note, faulty: 1-nearest-neighbour regression (Euclidean distance on X standardised with the training mean and sd) under 5-fold cross-validation (fold = i mod 5) on all 1200 records as given; Pearson correlation between the pooled held-out predictions and y >= 0.30.
- Private note, fixed: Records whose standardised X rows lie closer than 0.1 times the median pairwise distance are linked (single linkage, connected components); every component is placed whole into one fold (component id mod 5 after ordering by first member); the same 5-fold evaluation; Pearson correlation >= 0.30.
- Lines of `faulty_body.py` that carry the error: L74: `fold = np.arange(n) % 5` - records are assigned to folds without regard to near copies, so a held-out record can have a near copy among the fitting records. Parameters: one neighbour, correlation 0.30 from the claim; near-copy share proposed by the note (0.3), source states none.
- Lines of `fixed_body.py` that carry the correction: L74: `fold = link_components(X, 0.1) % 5` - single-linkage components of records closer than 0.1 times the median pairwise standardised distance are placed whole into one fold (component number by first member, mod 5); helper `link_components`, checked against an independent union-find on a random array and on a planted chain of near copies.
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the correlation for new compounds that have no near-identical record among those used to fit. (private note: Faulty: correlation on held-out records many of which have a near-identical record among the fitting records. Fixed: correlation for new compounds that have no near-identical record among those used to fit.)

## 5. Allowed-guard minimum used
2 records; zero variance of predictions or y; non-finite values. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.042 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (y = X1 + noise), and guard checks (no guard run). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
none
Problems: none. Fixed-body revisions after the first run: 0.
