# CASE D-031 (author-local id B3A-12)

## 1. Case
- Case id: D-031 (brief author's local id B3A-12)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-vs-denominator-proxy; statistic family: correlation; role reserve (KRO93)

## 2. Source and documenting passage
- Source key: KRO93
- Passage: 'Spurious correlation refers to the correlation between indices that have a common component.' (abstract, RePEc/IDEAS page, read through WebFetch excerpt); the abstract treats a single ratio as dependent variable in a multiple regression and recommends avoiding ratios.
- Read: Read by the brief author in the abstract (RePEc/IDEAS page, WebFetch excerpt). I fetched nothing online.

## 3. Brief
- Claim: Across cities, annual offences recorded and the median age of residents are associated after accounting for population: the partial correlation coefficient between offences and median age, given population, is at least 0.25 in absolute value.
- Data keys:
  - `offences` (cities,) float: total offences recorded in each city in one year
  - `median_age` (cities,) float: median age of the residents of each city, in years
  - `population` (cities,) float: population of each city, in thousands
- Sizes: {"cities": 500}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 61-62: `with np.errstate(divide='ignore', invalid='ignore'):` ... `a = off / pop`; line 67: `r = _corr(a, age)`
  - Pearson correlation between the per-capita rate offences/population and median_age, absolute value compared with 0.25 (`>=`). Parameters: none numeric in the source. Documented in KRO93 (a single ratio as dependent variable).
- **Fixed body, the correction** (`fixed_body.py`): line 61: `a = off`; line 66: `r = _partial_corr(a, age, pop)`
  - Partial correlation between offences and median_age given population (correlation of the residuals on an intercept and population), same 0.25 in absolute value. The source's correction.
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Partial correlation between total offences and median age at a given population.

## 5. Allowed-guard minimum
3 cities, non-finite values (a zero population gives a non-finite ratio in the faulty body), zero variance of the used offences quantity, of median age or of population.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-031 types ['bool'] max_time_s 0.00019`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
Minimum 3 cities instead of the note's 4 (partial correlation defined at 3). `_resid` and `_partial_corr` are present in the faulty file as well (same helper set), unused there.
