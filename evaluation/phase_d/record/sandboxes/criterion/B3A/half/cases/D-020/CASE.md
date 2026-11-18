# CASE D-020 (author-local id B3A-11)

## 1. Case
- Case id: D-020 (brief author's local id B3A-11)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-shared-denominator; statistic family: R-squared; role reserve (PEA97)

## 2. Source and documenting passage
- Source key: PEA97
- Passage: 'The particular case that is likely to occur is when u and v are indices with the same denominator for the correlation of the indices seems at first sight a very plausible measure of organic correlation.' (abstract, OpenAlex OCR text)
- Read: Read by the brief author in the abstract (OpenAlex OCR text, `fetched/pea97.json`); the abstract is the whole readable text. I fetched nothing online.

## 3. Brief
- Claim: Heart weight accounts for at least 10% of the variance in liver weight beyond what body mass accounts for: the increase in R-squared when heart weight is added to a regression of liver weight on body mass is at least 0.10.
- Data keys:
  - `liver_weight` (mice,) float: liver weight of each mouse, in g
  - `heart_weight` (mice,) float: heart weight of each mouse, in g
  - `body_mass` (mice,) float: body mass of each mouse, in g
- Sizes: {"mice": 1500}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 40-42: `with np.errstate(divide='ignore', invalid='ignore'):` ... `x = heart / body`; line 47: `stat = _r2(y, x.reshape(-1, 1))`
  - R-squared of the regression of the index liver_weight/body_mass on the index heart_weight/body_mass (squared correlation of the two indices), compared with 0.10 (`>=`). Parameters: none numeric in the source. Documented in PEA97 (indices with the same denominator).
- **Fixed body, the correction** (`fixed_body.py`): line 40: `y = liver`; line 41: `x = heart`; line 46: `stat = _r2(y, np.column_stack([body, x])) - _r2(y, body.reshape(-1, 1))`
  - Increase in R-squared when heart_weight is added to the regression of liver_weight on body_mass, compared with the same 0.10 (`>=`).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Variance of liver weight explained by heart weight beyond body mass.

## 5. Allowed-guard minimum
3 mice, non-finite values, zero variance of the response, heart quantity or body mass used. Same as the note.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-020 types ['bool'] max_time_s 0.00032`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none.
