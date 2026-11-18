# D-019 (B3B-06, case)

## 1. Identity
- Case id: D-019 (local id B3B-06 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `change-vs-baseline`. Statistic family: `regression-slope`. Subtype: None.

## 2. Source and documenting passage
- Source key: BLO77.
- Passage: 'Assuming that the observations deviate in a random manner from the true values, straightforward regression computations will yield biased results.' 'It is shown that, in the case of the normal distribution, the maximum likelihood (ML) estimates of the second-order moments of the true slope and the true initial value are obtained by simple adjustments of the corresponding moments of the estimated quantities.' (abstract, OpenAlex).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: In 400 adults with systolic blood pressure measured at five annual visits, those with a higher initial blood pressure have a lower yearly rate of change: the regression slope of an individual's underlying yearly rate of change in systolic blood pressure on the individual's underlying initial systolic blood pressure is at most -0.03 mmHg per year per mmHg.
- Data keys:
  - `systolic_bp` (individuals, occasions) float: systolic blood pressure of each individual at each of five annual visits, with the visits in time order, in mmHg
- Sizes: individuals = 400, occasions = 5.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Line 25: the regressor is the observed first reading x[:, 0]; the regressand is the least-squares slope b_i of each individual (computed in lines 20-24 of both files); the slope is cov(u, b) / var(u) with ddof 1 (shared lines). The naive regression of estimated rate of change on observed initial value is the error (BLO77: "straightforward regression computations will yield biased results").
- **Fixed, `fixed_body.py`.** Lines 25-26 and 32-35: the regressor is the fitted level at the first visit a_i (intercept of the individual line, time 0); the pooled residual variance s2 = SSR / (n (m - 2)) is estimated from residuals about each individual's own line; Var(a) is reduced by s2 (1/m + tbar^2 / Sxx) and Cov(a, b) is increased by s2 tbar / Sxx (the covariance of the estimated intercept and slope is -s2 tbar / Sxx). The slope is adjusted Cov / adjusted Var(a) (the shared lines compute cc / v). Times are 0, 1, ..., m - 1 (annual visits, in time order).
- Error lines: faulty 25; correction lines: fixed 25-26 and 32-35. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Slope of the true rate of change on the true initial value (second-order moments adjusted for measurement error).

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 16; fixed line(s) 16. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 18, 34; fixed line(s) 18, 39 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 26, 31; fixed line(s) 27, 36.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result None (corrected variance not positive: pure noise), type bool or None; a repeat on a copy gave the same result; time 0.2 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The private note does not say what happens when the adjusted variance of the true initial value is not positive; the fixed body returns None then (line `if not v > 0.0`, shared with the faulty body, where it is the zero-variance guard). I read it as the same guard as in the note of B3B-13 and request confirmation (it extends "zero variance" to "variance not positive after correction"). The fitted intercept (level at time 0 of the individual line), not the raw first reading, is the corrected initial value, as the note says.
