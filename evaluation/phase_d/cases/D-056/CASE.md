# D-056 (B3B-04, case)

## 1. Identity
- Case id: D-056 (local id B3B-04 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `ratio-vs-denominator-proxy`. Statistic family: `mean`. Subtype: None.

## 2. Source and documenting passage
- Source key: CUR13.
- Passage: 'we want to control for differences in the denominator when the thing we really care about is the numerator'; regression techniques 'these include analysis of covariance' are versatile when a ratio is useless (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05.
- Data keys:
  - `oxygen_uptake` (groups, animals) float: resting oxygen uptake of each rat in each group, in mL O2 per min
  - `body_mass` (groups, animals) float: body mass of each rat in each group, in g
- Sizes: groups = 3, animals = 25.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 113-115: the response is the ratio oxygen_uptake / body_mass; the F test compares group means (X1 = intercept + group dummies) with the grand mean (X0 = intercept): one-way ANOVA on the ratio. Error named by CUR13.
- **Fixed, `fixed_body.py`.** Lines 113-117: the response is oxygen_uptake; X0 = intercept + body_mass, X1 = intercept + body_mass + group dummies: the analysis-of-covariance F test of the group effect (common slope, intercept per group). The nested-model F helper, the p < 0.05 decision are shared.
- Error lines: faulty 113-115; correction lines: fixed 113-117. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Difference between groups in oxygen uptake at equal body mass.

## 5. Allowed guards used (minimum: 5)
- Minimum size: faulty line(s) 105; fixed line(s) 105. The minimum is 5 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 107, 116; fixed line(s) 107, 118 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 118; fixed line(s) 113, 120.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.2 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Helper check (scratch): the t and F tail-probability helpers of this file, run on a grid of (statistic, df) pairs, agree with scipy.stats to a worst relative error of 1.1e-13 (`work\verify_fixed.py`).
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The F p-value is computed in numpy only (see B3B-03; compared with scipy.stats.f in scratch, same worst error). Problems: none.
