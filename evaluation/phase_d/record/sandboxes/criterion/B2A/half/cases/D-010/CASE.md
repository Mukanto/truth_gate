# CASE D-010 (B2A-04)

## 1. Case
- Id: D-010 (author-local id B2A-04); class B-2 (procedure-level leakage), half A.
- Subtype / tag: L1.2 (pre-processing on training and test set; target encoding, from the task's subtype list); mechanism tag L1.2; statistic family: correlation.

## 2. Source and documenting passage
- Source key: KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): L1.2: "Using the entire dataset for any pre-processing steps, such as imputation or over/under sampling, results in leakage." (Results, 'Toward a solution: A taxonomy of data leakage', PMC10499856). Target encoding is the subtype's listed example in the task's closed list, not a phrase of the quoted sentence.
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25.
- Data keys:
- `category` bool, (samples, categories): True where the patient's home postal district is the district of that column
- `covariates` float, (samples, features): three continuous covariates per patient (age, body-mass index, systolic pressure)
- `y` float, (samples,): continuous health outcome of each patient
- Sizes: {"samples": 1200, "categories": 150, "features": 3}

## 4. Mapping
- Private note, faulty: Each of the 150 districts is encoded by the mean of y over all rows of that district, using all 1200 rows (a district with no row gets the grand mean); ordinary least squares of y on [encoded value, 3 covariates, intercept] with 5-fold cross-validation (fold = i mod 5), the encoding of a held-out row being the all-rows district mean; pooled Pearson correlation between predictions and y >= 0.25.
- Private note, fixed: In each fold the district means are computed from the 960 training rows only; training rows use their own training mean and held-out rows use the training mean of their district (grand training mean if the district is absent); OLS fitted on the training rows, predicts the held-out rows; pooled Pearson correlation >= 0.25.
- Lines of `faulty_body.py` that carry the error: L54-55: `enc = Cf @ district_means(C, y, all rows)` and the design matrix are built once from the district means of all 1200 rows, before the 5-fold loop; a held-out row's encoding therefore contains its own outcome. Parameters (about 8 rows per district, 150 districts) from the brief's sizes; the source states none.
- Lines of `fixed_body.py` that carry the correction: L56-57 inside the loop: `enc = Cf @ district_means(C, y, ~te)` and the design matrix from the training rows only (training rows use their own training mean, held-out rows the training mean of their district, the training grand mean if the district is absent).
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: the out-of-sample correlation for new patients, whose outcome is unknown when the district is encoded. (private note: Faulty: the correlation of predictions whose encoded feature contains the held-out row's own outcome (about 8 rows per district). Fixed: the out-of-sample correlation for new patients, whose outcome is unknown when the district is encoded.)

## 5. Allowed-guard minimum used
2 rows; zero variance of predictions or y; non-finite covariates or y. Private-note `guard_minimum`: 2.

## 6. Runs of the fixed body
`work\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on the same array agreed, time per call 0.002 s. `work\sanity_fixed.py`: 1 call on an array with a strong planted signal (district effect + one covariate), and guard checks (no guard run). `work\test_helpers.py`: unit checks of the helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.

## 7. Deviations from the private note, and problems
Source-basis caveat as in the private note: KAP23's quoted sentence names imputation and over/under sampling; target encoding comes from the subtype definition. A row with no True in `category` would get encoding 0 (not expected under the brief's meaning).
Problems: none. Fixed-body revisions after the first run: 0.
