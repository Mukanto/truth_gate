# D-026 (B3B-11, reserve)

## 1. Identity
- Case id: D-026 (local id B3B-11 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `ratio-shared-denominator`. Statistic family: `other`. Subtype: None.

## 2. Source and documenting passage
- Source key: ATC76.
- Passage: 'Multivariate statistical procedures such as principal components analysis are greatly affected when the data upon which the analyses are based include ratios or proportions. In this case, there is often an inflation of the first eigenvalue together with large changes in the magnitude and direction of the coefficients on the various principal components.' (abstract, via OpenAlex).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Among 400 adult beetles measured on six skeletal dimensions, the dimensions share a common shape pattern beyond body length: after removing the linear effect of body length from each of the six dimensions, the first principal component of their covariance matrix explains at least 40% of the total variance.
- Data keys:
  - `skeletal` (specimens, dimensions) float: six linear skeletal dimensions of each specimen, in mm
  - `body_length` (specimens,) float: body length of each specimen, in mm
- Sizes: specimens = 400, dimensions = 6.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Line 29: the six dimensions are divided by body_length (ratios); the first-component share of variance of their covariance matrix is the statistic (shared helper `first_share`).
- **Fixed, `fixed_body.py`.** Lines 29-32: each dimension is regressed on body_length (intercept) and the residuals form the matrix; the same `first_share` helper and threshold 0.40 follow.
- Error lines: faulty 29; correction lines: fixed 29-32. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): First-component share of variance among the dimensions after the linear effect of body length is removed.

## 5. Allowed guards used (minimum: 3)
- Minimum size: faulty line(s) 25; fixed line(s) 25. The minimum is 3 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 27, 30; fixed line(s) 27, 33 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) -; fixed line(s) 29.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.8 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- none
