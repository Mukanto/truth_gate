# D-057 (B3B-07, case)

## 1. Identity
- Case id: D-057 (local id B3B-07 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `change-vs-baseline`. Statistic family: `R-squared`. Subtype: None.

## 2. Source and documenting passage
- Source key: TU04.
- Passage: 'relating change to baseline values using correlation or regression is methodologically flawed due to mathematical coupling'; the relation between clinical outcomes and baseline 'were reanalysed using Oldham's method and the variance ratio test' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: In 24 intrabony periodontal defects treated by guided tissue regeneration, the level of disease explains the amount of change: the mean of the baseline and follow-up pocket probing depth explains at least 15% of the variance in the change in pocket probing depth (follow-up minus baseline), that is, the R-squared of the linear regression of the change on that mean is at least 0.15.
- Data keys:
  - `baseline_depth` (defects,) float: pocket probing depth of each defect at the baseline examination, in mm
  - `baseline_depth_retest` (defects,) float: a second, independent probing of the depth of each defect at the baseline examination, in mm
  - `followup_depth` (defects,) float: pocket probing depth of each defect at the follow-up examination after treatment, in mm
- Sizes: defects = 24.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Line 30: the regressor of the change is the baseline depth; the R-squared is the squared correlation (shared line `return bool(r * r >= 0.15)`), equal to the R-squared of the simple regression.
- **Fixed, `fixed_body.py`.** Line 30: the regressor is the mean of baseline and follow-up depth (Oldham's method, TU04, as R-squared). baseline_depth_retest is read by neither body.
- Error lines: faulty 30; correction lines: fixed 30. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Variance of the change explained by the average level of the two readings.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 25; fixed line(s) 25. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 27; fixed line(s) 27 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 31; fixed line(s) 31.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.1 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- none
