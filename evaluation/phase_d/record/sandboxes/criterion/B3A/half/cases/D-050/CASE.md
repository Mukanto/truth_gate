# CASE D-050 (author-local id B3A-10)

## 1. Case
- Case id: D-050 (brief author's local id B3A-10)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-vs-denominator-proxy; statistic family: R-squared; role pair (KRO93 pair 3 of 3)

## 2. Source and documenting passage
- Source key: KRO93
- Passage: 'Spurious correlation refers to the correlation between indices that have a common component.' (abstract, RePEc/IDEAS page, read through WebFetch excerpt); the abstract treats a single ratio as dependent variable in a multiple regression and recommends avoiding ratios.
- Read: Read by the brief author in the abstract (RePEc/IDEAS page, WebFetch excerpt). I fetched nothing online.

## 3. Brief
- Claim: Age explains at least 10% of the variance in liver mass beyond what body mass explains: the increase in R-squared when age is added to a regression of liver mass on body mass is at least 0.10.
- Data keys:
  - `liver_mass` (rats,) float: liver mass of each rat, in g
  - `age_days` (rats,) float: age of each rat, in days
  - `body_mass` (rats,) float: body mass of each rat, in g
- Sizes: {"rats": 80}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 39-40: `with np.errstate(divide='ignore', invalid='ignore'):` ... `y = liver / body`; line 45: `stat = _r2(y, age.reshape(-1, 1))`
  - R-squared of the regression of the ratio liver_mass/body_mass on age_days, compared with 0.10 (`>=`). Parameters: none numeric in the source. Documented in KRO93 (a single ratio as dependent variable).
- **Fixed body, the correction** (`fixed_body.py`): line 39: `y = liver`; line 44: `stat = _r2(y, np.column_stack([body, age])) - _r2(y, body.reshape(-1, 1))`
  - Increase in R-squared when age_days is added to the regression of liver_mass on body_mass, compared with the same 0.10 (`>=`). The source's correction (denominator as a covariate).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Variance of liver mass explained by age beyond body mass.

## 5. Allowed-guard minimum
3 rats, non-finite values, zero variance of the response, age or body mass used. Same as the note.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-050 types ['bool'] max_time_s 0.00016`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none.
