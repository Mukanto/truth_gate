# CASE D-017 (author-local id B3A-02)

## 1. Case
- Case id: D-017 (brief author's local id B3A-02)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-vs-denominator-proxy; statistic family: mean; role pair (KRO93 pair 1 of 3)

## 2. Source and documenting passage
- Source key: KRO93
- Passage: 'Spurious correlation refers to the correlation between indices that have a common component.' (abstract, RePEc/IDEAS page, read through WebFetch excerpt). The abstract further says that a single ratio used as dependent or independent variable in a multiple regression can give misleading inferences, and recommends avoiding ratios in regression analyses.
- Read: Read by the brief author in the abstract (RePEc/IDEAS page, WebFetch excerpt). I fetched nothing online.

## 3. Brief
- Claim: At a given height, the mean forced vital capacity of smokers and of non-smokers differs by at least 0.2 L: the difference between the two group means, after accounting for height, is at least 0.2 L in absolute value.
- Data keys:
  - `fvc` (subjects,) float: forced vital capacity of each subject, in litres
  - `height` (subjects,) float: standing height of each subject, in cm
  - `smoker` (subjects,) bool: True if the subject is a current smoker
- Sizes: {"subjects": 600}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 31-32: `with np.errstate(divide='ignore', invalid='ignore'):` ... `ratio = fvc / height`; line 35: `stat = abs((np.mean(ratio[smoker]) - np.mean(ratio[~smoker])) * np.mean(height))`
  - Ratio standard: difference between the group means of fvc/height, rescaled to litres at the overall mean height, in absolute value, compared with 0.2 L (`>=`). Parameters: none numeric in the source (abstract states none); the private note gives the rescaling 'at the mean height', here the mean height of all subjects. Documented in KRO93 (passage above: ratios as dependent variable).
- **Fixed body, the correction** (`fixed_body.py`): line 31: `A = np.column_stack([np.ones(n), smoker.astype(float), height])`; line 32: `coef = np.linalg.lstsq(A, fvc, rcond=None)[0]`; line 33: `stat = abs(float(coef[1]))`
  - Analysis of covariance: least-squares fit of fvc on intercept, smoker (0/1) and height; the smoker coefficient (the mean difference at equal height) in absolute value, compared with the same 0.2 (`>=`). This is the source's correction (deflator as a covariate).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Difference between the group mean fvc at equal height (adjusted mean difference, litres).

## 5. Allowed-guard minimum
3 subjects, both groups non-empty, non-finite values, zero variance of height. Same as the private note (a fit with three parameters is defined at 3).

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-017 types ['bool'] max_time_s 0.00016`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none. (The choice of the mean height of all subjects for the rescaling is mine; the note leaves it open: 'rescaled to litres at the mean height, or tested at the claim's 0.2 L size'.)
