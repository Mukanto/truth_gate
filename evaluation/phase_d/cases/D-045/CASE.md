# D-045 (B3B-05, case)

## 1. Identity
- Case id: D-045 (local id B3B-05 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `change-vs-baseline`. Statistic family: `correlation`. Subtype: None.

## 2. Source and documenting passage
- Source key: TU07.
- Passage: 'statisticians have repeatedly warned against correlating/regressing change with baseline due to two methodological concerns known as mathematical coupling and regression to the mean'; 'Oldham's method and Blomqvist's formula are the two most often adopted methods to rectify these problems' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: In 300 patients with a continuous disease severity score measured before and after treatment, improvement is larger in patients with a higher severity level: the Pearson correlation between each patient's change in score (follow-up minus baseline) and the mean of that patient's baseline and follow-up scores is at most -0.30.
- Data keys:
  - `baseline_score` (patients,) float: severity score of each patient at the baseline visit, higher is more severe
  - `baseline_score_retest` (patients,) float: a second, independent reading of the severity score of each patient taken at the baseline visit
  - `followup_score` (patients,) float: severity score of each patient at the follow-up visit after treatment
- Sizes: patients = 300.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Line 30: the baseline reading b is the correlate of the change (follow-up minus baseline): coupled correlation of change with baseline (TU07: mathematical coupling).
- **Fixed, `fixed_body.py`.** Line 30: the mean of the baseline and follow-up readings is the correlate (Oldham's method, TU07). The shared line `return bool(corr(chg, x) <= -0.30)` is unchanged. baseline_score_retest is read by neither body (as the private note states).
- Error lines: faulty 30; correction lines: fixed 30. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Association between change and the average level of the two readings.

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
