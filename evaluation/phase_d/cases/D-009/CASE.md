# D-009 (B3B-03, case)

## 1. Identity
- Case id: D-009 (local id B3B-03 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `ratio-vs-denominator-proxy`. Statistic family: `mean`. Subtype: None.

## 2. Source and documenting passage
- Source key: CUR13.
- Passage: 'only if the relationship between numerator and denominator is a straight line through the origin will the ratio be meaningful'; regression techniques, 'these include analysis of covariance', can accommodate the relationship when a ratio is useless (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Among 60 mice, treated mice produce more peak twitch force than untreated mice of the same body mass: the difference between the group means of peak force, adjusted for body mass by analysis of covariance, is positive with a two-sided p-value below 0.05.
- Data keys:
  - `peak_force` (animals,) float: peak twitch force of one hindlimb muscle of each mouse, in mN
  - `body_mass` (animals,) float: body mass of each mouse, in g
  - `treated` (animals,) bool: True if the mouse received the treatment, False if it did not
- Sizes: animals = 60.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 106-107: the response is the ratio peak_force / body_mass and the design is intercept + treated indicator; the treated coefficient and its two-sided t-test (n-2 df) are taken. This is the Student two-sample t test on the ratio (the private note allows Student or Welch). The ratio analysis is the error named by CUR13 (ratio is meaningful only for a line through the origin).
- **Fixed, `fixed_body.py`.** Lines 106-109: the response is peak_force and the design is intercept + treated + body_mass (analysis of covariance, common slope); the treated coefficient and its two-sided t-test (n-3 df) are taken. The decision line (coefficient > 0 and p < 0.05) and the helper are shared.
- Error lines: faulty 106-107; correction lines: fixed 106-109. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Difference in peak force between treated and untreated mice at equal body mass.

## 5. Allowed guards used (minimum: 4)
- Minimum size: faulty line(s) 99, 103; fixed line(s) 99, 103. The minimum is 4 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 101, 108; fixed line(s) 101, 110 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 110; fixed line(s) 106, 112.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.2 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Helper check (scratch): the t and F tail-probability helpers of this file, run on a grid of (statistic, df) pairs, agree with scipy.stats to a worst relative error of 1.1e-13 (`work\verify_fixed.py`).
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- Faulty uses the Student (pooled) test, which the note allows ("Student or Welch"); it is computed as the t test of the indicator coefficient in an OLS regression, the same helper as the fixed analysis. The t p-value is computed in numpy only (continued-fraction incomplete beta, Lanczos log-gamma), because only `import numpy as np` is allowed; it was compared with scipy.stats.t in scratch (worst relative error 1.1e-13). An empty treatment group is guarded as an empty selection. Problems: none.
