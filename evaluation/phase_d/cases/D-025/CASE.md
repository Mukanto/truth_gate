# D-025 (B3B-15, reserve)

## 1. Identity
- Case id: D-025 (local id B3B-15 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `change-vs-baseline`. Statistic family: `regression-slope`. Subtype: None.

## 2. Source and documenting passage
- Source key: TU04.
- Passage: 'Ten out of 12 studies for PPD and nine out of 14 for LCAL initially claimed a significant positive relationship; after using either of the more appropriate statistical methods of adjustment, only three correlations in each group of studies remained significant.' 'relating change to baseline values using correlation or regression is methodologically flawed due to mathematical coupling' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Across 12 trials of guided tissue regeneration with 20 defects each, deeper disease means larger gain: the mean over trials of the within-trial regression slope of the change in attachment loss (follow-up minus baseline) on the mean of the baseline and follow-up attachment loss is at most -0.20 (mm per mm).
- Data keys:
  - `baseline_attachment_loss` (trials, defects) float: clinical attachment loss of each defect in each trial at the baseline examination, in mm
  - `baseline_attachment_loss_retest` (trials, defects) float: a second, independent measurement of the attachment loss of each defect at the baseline examination, in mm
  - `followup_attachment_loss` (trials, defects) float: clinical attachment loss of each defect at the follow-up examination after treatment, in mm
- Sizes: trials = 12, defects = 20.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Line 25: the within-trial regressor of the change is the baseline attachment loss; slopes are computed per trial (shared lines) and averaged.
- **Fixed, `fixed_body.py`.** Line 25: the regressor is the mean of baseline and follow-up attachment loss (Oldham's variable, TU04); the per-trial slopes, their mean and the threshold -0.20 are shared. The retest key is read by neither body.
- Error lines: faulty 25; correction lines: fixed 25. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Mean within-trial slope of change on the average level of the two measurements.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 20; fixed line(s) 20. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 22; fixed line(s) 22 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 26; fixed line(s) 26.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.1 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- none
