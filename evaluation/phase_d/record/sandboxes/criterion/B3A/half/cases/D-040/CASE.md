# CASE D-040 (author-local id B3A-01)

## 1. Case
- Case id: D-040 (brief author's local id B3A-01)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-shared-denominator; statistic family: correlation; role pair (PEA97 pair 1 of 3)

## 2. Source and documenting passage
- Source key: PEA97
- Passage: 'The particular case that is likely to occur is when u and v are indices with the same denominator for the correlation of the indices seems at first sight a very plausible measure of organic correlation.' (abstract, OpenAlex OCR text; the abstract also states that u = f1(x,y), v = f2(x,y) correlate although x, y, z are selected at random with no correlation.)
- Read: Read by the brief author in the abstract (OpenAlex OCR text, `fetched/pea97.json`); the abstract is the whole readable text. I fetched nothing online.

## 3. Brief
- Claim: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2.
- Data keys:
  - `breadth` (skulls,) float: maximum cranial breadth of each skull, in mm
  - `height` (skulls,) float: cranial height of each skull, in mm
  - `length` (skulls,) float: maximum cranial length of each skull, in mm
- Sizes: {"skulls": 300}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 61-62: `a = x / z` ... `b = y / z`; line 67: `r = _corr(a, b)`
  - The two indices breadth/length and height/length (common denominator = length) are formed and their Pearson correlation is compared with 0.2 (`>=`). Parameters: none numeric in the source (the abstract names the case, indices with the same denominator, and states no numbers); the threshold 0.2 is the claim's. Documented in PEA97 (passage above).
- **Fixed body, the correction** (`fixed_body.py`): line 60: `a = x`; line 61: `b = y`; line 66: `r = _partial_corr(a, b, z)`
  - Partial correlation of breadth and height given length (correlation of the residuals of each on an intercept and length, `_partial_corr`), compared with the same 0.2, same `>=`.
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Association between breadth and height net of length (partial correlation given length).

## 5. Allowed-guard minimum
3 skulls (below 3 returns None), non-finite values, zero variance of the used breadth/height quantities or of length. The partial correlation is defined from 3 observations (the residual space is one-dimensional); the private note says 4.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`. Estimator check: partial correlation on a known structure, true 0.5000, estimated 0.5021 (n = 100000).
- Smoke result (3 arrays): `D-040 types ['bool'] max_time_s 0.00014`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
Minimum 3 skulls instead of the note's 4 (the statistic is defined at 3; the rule caps the guard at the smallest defined size). Zero-variance guard is applied to the quantities that enter the statistic (the two ratios in the faulty body, breadth and height in the fixed one) and to length, plus a numerical-zero residual variance guard inside `_partial_corr` (residual variance <= 1e-24 of the total). `_resid` and `_partial_corr` are present in the faulty file as well (same helper set), unused there.
