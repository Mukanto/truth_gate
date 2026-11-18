# CASE D-006 (author-local id B3A-07)

## 1. Case
- Case id: D-006 (brief author's local id B3A-07)
- Class: B-3, coupling by construction (half A)
- Tag: change-vs-baseline; statistic family: correlation; role pair (CHI13 pair 2 of 2)

## 2. Source and documenting passage
- Source key: CHI13
- Passage: 'Because the initial value (Y1) and the change from initial value (Y2 - Y1) share a common variable, there is a mathematical coupling between Y1 and Y2 - Y1.' (Glossary, Europe PMC full text). With more than two waves: 'the linear random effects model or individual growth curve modeling [...] is a standard method to assess the relationship between change in a continuous variable and its correlates, including the baseline level'.
- Read: The brief author read it in the Europe PMC full-text XML (saved in `fetched/chi13.txt`); I re-read the 'Analyses' passage on the five methods there (random-effects, crude, Oldham, repeated measurement, Blomqvist). I fetched nothing online.

## 3. Brief
- Claim: Across children, BMI at age 5 and the yearly rate of change in BMI between ages 5 and 10 are negatively correlated: the correlation between the two is at most -0.25.
- Data keys:
  - `bmi` (children, annual_visits) float: BMI of each child at the annual visits at ages 5, 6, 7, 8, 9 and 10 (visits in age order), in kg/m2
- Sizes: {"children": 500, "annual_visits": 6}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 38: `r = _corr(bmi[:, 0], bmi[:, -1] - bmi[:, 0])`
  - Crude two-wave analysis: Pearson correlation of the first-visit BMI with the change between the last and first visits, compared with -0.25 (`<=`). Parameters: none numeric beyond the source's scenario. Documented in CHI13 (Analyses (2), and the Glossary on mathematical coupling).
- **Fixed body, the correction** (`fixed_body.py`): lines 38-46: `X = np.column_stack([np.ones(m), np.arange(m, dtype=float)])` ... `r = float(G[0, 1] / np.sqrt(G[0, 0] * G[1, 1]))`
  - Linear random-effects model of BMI on age with all visits, correlation between the random intercept (at the first visit) and the random slope, compared with the same -0.25 (`<=`). Implemented in closed form for the balanced design: per-child least-squares intercept and slope, and the covariance matrix of the random coefficients as the covariance of those estimates minus sigma^2 (X'X)^-1, with sigma^2 the pooled residual variance (the moment/REML solution when it is positive definite). The source's r_random (CHI13 Analyses (1)).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Correlation between a child's true level at the first visit and the true yearly rate of change.

## 5. Allowed-guard minimum
2 children, 3 visits (needed for the error variance), non-finite values, zero variance of the first-visit BMI or of the change (faulty, inside `_corr`); fixed: the estimated variance of the random intercept or slope not positive (correlation undefined) returns None.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`. Estimator check (`work/check_estimators.py`, n = 200000, known truth): true corr(b0, b1) -0.6270, corrected estimator -0.6289, uncorrected per-child OLS -0.6857. On the independent random smoke arrays the result was None in some draws (estimated slope variance not positive) and bool in others.
- Smoke result (3 arrays): `D-006 types ['NoneType', 'bool'] max_time_s 0.00026`
- Fixed-body revisions: 1 revision after its first run, docstring only (the None condition of the fitted model was added to the docstring). Both files changed alike.

## 7. Deviations from the private note, and problems
The note calls for the correction 'for the error variance estimated from the residuals'; I used the balanced-data moment solution of the random-effects model rather than an iterative REML routine (numpy only). I treat an estimated variance component <= 0 (boundary solution; the correlation is then undefined, not finite) as the zero-variance guard. On independent random arrays this guard fires in some draws (see runs), so it may return None on data without a trend; I flag this for review under the rule that None comes only from the allowed guards.
