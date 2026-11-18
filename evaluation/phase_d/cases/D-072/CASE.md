# D-072 (B3B-12, reserve)

## 1. Identity
- Case id: D-072 (local id B3B-12 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `ratio-vs-denominator-proxy`. Statistic family: `mean`. Subtype: None.

## 2. Source and documenting passage
- Source key: CUR13.
- Passage: 'As researchers, we compute a ratio-a numerator divided by a denominator-to compute a proportion for some biological response or to derive some standardized variable.' 'only if the relationship between numerator and denominator is a straight line through the origin will the ratio be meaningful' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: In 30 subjects each studied in a vehicle session and in a drug session, the drug raises muscle force: the mean paired difference in force between the drug and the vehicle session, adjusted for the muscle cross-sectional area measured in each session by analysis of covariance, is positive with a two-sided p-value below 0.05.
- Data keys:
  - `force_vehicle` (subjects,) float: peak voluntary knee-extension force of each subject in the vehicle session, in N
  - `force_drug` (subjects,) float: peak voluntary knee-extension force of each subject in the drug session, in N
  - `area_vehicle` (subjects,) float: quadriceps cross-sectional area of each subject measured in the vehicle session, in cm2
  - `area_drug` (subjects,) float: quadriceps cross-sectional area of each subject measured in the drug session, in cm2
- Sizes: subjects = 30.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 105-106: the response is the paired difference of the ratios force_drug / area_drug - force_vehicle / area_vehicle and the design is the intercept alone; the intercept t test (n-1 df) is the paired t test. Error named by CUR13.
- **Fixed, `fixed_body.py`.** Lines 105-108: the response is force_drug - force_vehicle and the design is intercept + (area_drug - area_vehicle) (paired analysis of covariance); the intercept coefficient and its two-sided t test (n-2 df) are taken. The decision line (intercept > 0 and p < 0.05) and the helper are shared.
- Error lines: faulty 105-106; correction lines: fixed 105-108. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Mean paired difference in force at equal area.

## 5. Allowed guards used (minimum: 3)
- Minimum size: faulty line(s) 101; fixed line(s) 101. The minimum is 3 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 103, 107; fixed line(s) 103, 109 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 109; fixed line(s) 105, 111.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.2 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Helper check (scratch): the t and F tail-probability helpers of this file, run on a grid of (statistic, df) pairs, agree with scipy.stats to a worst relative error of 1.1e-13 (`work\verify_fixed.py`).
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- Same numpy-only t p-value as B3B-03. Problems: none.
