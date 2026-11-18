# D-068 (B3B-02, case)

## 1. Identity
- Case id: D-068 (local id B3B-02 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `ratio-shared-denominator`. Statistic family: `regression-slope`. Subtype: None.

## 2. Source and documenting passage
- Source key: ATC76.
- Passage: 'Simulation studies with minimum sample sizes of 25,000 indicated large and systematic changes in both the structure and the underlying distributions of data when ratios and proportions were compounded between continuous variables.' The cases examined include Y = X1/X2, Z = X3/X2 (abstract, via OpenAlex).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width).
- Data keys:
  - `head_width` (populations, specimens) float: head width of each specimen in each population, in mm
  - `wing_length` (populations, specimens) float: wing length of each specimen in each population, in mm
  - `body_length` (populations, specimens) float: body length of each specimen in each population, in mm
- Sizes: populations = 25, specimens = 40.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 30-32: within each population, wing_length / body_length is regressed on head_width / body_length (intercept + ratio, simple OLS); coefficient index 1 is taken (Y = X1/X2, Z = X3/X2).
- **Fixed, `fixed_body.py`.** Lines 30-31: within each population, wing_length is regressed on head_width and body_length (intercept, two predictors); coefficient index 1 (head_width) is taken. The loop, the per-population guards, the mean over populations and the threshold 0.30 are shared.
- Error lines: faulty 30-32; correction lines: fixed 30-31. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Mean over populations of the within-population partial slope of wing length on head width at fixed body length.

## 5. Allowed guards used (minimum: 3)
- Minimum size: faulty line(s) -; fixed line(s) -. The minimum is 3 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 26, 33; fixed line(s) 26, 32 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 36; fixed line(s) 35.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 1.0 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- none
