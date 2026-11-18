# CASE D-038 (author-local id B3A-06)

## 1. Case
- Case id: D-038 (brief author's local id B3A-06)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-vs-denominator-proxy; statistic family: regression-slope; role pair (KRO93 pair 2 of 3)

## 2. Source and documenting passage
- Source key: KRO93
- Passage: 'Spurious correlation refers to the correlation between indices that have a common component.' (abstract, RePEc/IDEAS page, read through WebFetch excerpt). The abstract treats a single ratio used as a dependent or an independent variable in a multiple regression.
- Read: Read by the brief author in the abstract (RePEc/IDEAS page, WebFetch excerpt). I fetched nothing online.

## 3. Brief
- Claim: Across countries, annual lung-cancer deaths and annual cigarette sales are associated after accounting for population: the standardised slope of deaths on cigarette sales, with population accounted for, is at least 0.2 in absolute value.
- Data keys:
  - `lung_cancer_deaths` (countries,) float: total lung-cancer deaths in each country in one year, in thousands
  - `cigarettes_sold` (countries,) float: total cigarettes sold in each country in the same year, in millions
  - `population` (countries,) float: population of each country, in millions
- Sizes: {"countries": 150}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 35-36: `with np.errstate(divide='ignore', invalid='ignore'):` ... `x = sales / pop`; line 41: `b = _std_coef(y, x.reshape(-1, 1), 0)`
  - Standardised slope (slope times SD of regressor over SD of deaths) of deaths regressed on per-capita sales (sales / population) alone, absolute value compared with 0.2 (`>=`). Parameters: none numeric in the source. Documented in KRO93 (a single ratio as independent variable).
- **Fixed body, the correction** (`fixed_body.py`): line 35: `x = sales`; line 40: `b = _std_coef(y, np.column_stack([x, pop]), 0)`
  - Standardised coefficient of cigarettes_sold in the regression of deaths on cigarettes_sold and population (the denominator as a covariate), same 0.2 in absolute value. The source's correction.
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Association of deaths with total sales at a given population (standardised partial coefficient).

## 5. Allowed-guard minimum
3 countries, non-finite values (a zero population gives a non-finite ratio in the faulty body), zero variance of deaths, of the regressor or of population. Same as the note.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`. Estimator check: standardised coefficient on a known structure, true 0.1778, estimated 0.1766 (n = 100000).
- Smoke result (3 arrays): `D-038 types ['bool'] max_time_s 0.00011`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none. 'Zero population' is covered by the non-finite guard of the ratio in the faulty body (the fixed body does not divide).
