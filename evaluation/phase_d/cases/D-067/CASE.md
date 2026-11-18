# CASE D-067 (author-local id B3A-09)

## 1. Case
- Case id: D-067 (brief author's local id B3A-09)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-shared-denominator; statistic family: regression-slope; role pair (PEA97 pair 3 of 3)

## 2. Source and documenting passage
- Source key: PEA97
- Passage: 'The particular case that is likely to occur is when u and v are indices with the same denominator for the correlation of the indices seems at first sight a very plausible measure of organic correlation.' (abstract, OpenAlex OCR text)
- Read: Read by the brief author in the abstract (OpenAlex OCR text, `fetched/pea97.json`); the abstract is the whole readable text. I fetched nothing online.

## 3. Brief
- Claim: After accounting for body mass, kidney weight and heart weight are positively related: the standardised slope of kidney weight on heart weight is at least 0.25.
- Data keys:
  - `kidney_weight` (rats,) float: combined kidney weight of each rat, in g
  - `heart_weight` (rats,) float: heart weight of each rat, in g
  - `body_mass` (rats,) float: body mass of each rat, in g
- Sizes: {"rats": 60}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 32-34: `with np.errstate(divide='ignore', invalid='ignore'):` ... `x = heart / body`; line 39: `b = _std_coef(y, x.reshape(-1, 1), 0)`
  - Standardised slope of the index kidney/body on the index heart/body (simple regression; equals their correlation), compared with 0.25 (`>=`). Parameters: none numeric in the source. Documented in PEA97 (indices with the same denominator).
- **Fixed body, the correction** (`fixed_body.py`): line 32: `y = kid`; line 33: `x = heart`; line 38: `b = _std_coef(y, np.column_stack([x, body]), 0)`
  - Standardised coefficient of heart weight in the regression of kidney weight on heart weight and body mass (denominator as a covariate), compared with the same 0.25 (`>=`).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Standardised partial slope of kidney weight on heart weight at fixed body mass.

## 5. Allowed-guard minimum
3 rats, non-finite values, zero variance of the response, regressor or body mass used. Same as the note.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-067 types ['bool'] max_time_s 0.00013`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none.
