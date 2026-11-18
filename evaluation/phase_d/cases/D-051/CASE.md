# D-051 (B3B-09, case)

## 1. Identity
- Case id: D-051 (local id B3B-09 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `shared-measured-component`. Statistic family: `regression-slope`. Subtype: None.

## 2. Source and documenting passage
- Source key: STR87.
- Passage: 'For example, the relationship between O2 consumption and O2 delivery may be of interest, although these may be computed from measurements of cardiac output and blood O2 contents.' 'In two previous studies of O2 consumption and delivery, the effect of coupled error is shown to be small when the range of O2 deliveries studied is large, and measurement errors are of reasonable size.' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: In 12 anaesthetised dogs, each studied at 8 steps, whole-body oxygen consumption rises with oxygen delivery within a dog, both computed from the measured cardiac output and the arterial and mixed-venous blood oxygen contents by the standard Fick definitions: the mean over dogs of the within-dog regression slope of oxygen consumption on oxygen delivery is at least 0.15 (mL O2 per min per mL O2 per min).
- Data keys:
  - `cardiac_output` (animals, steps) float: cardiac output of each dog at each step, in L per min
  - `cardiac_output_2` (animals, steps) float: a second, independent determination of the cardiac output of each dog at each step, in L per min
  - `arterial_o2_content` (animals, steps) float: arterial blood oxygen content of each dog at each step, in mL O2 per dL
  - `venous_o2_content` (animals, steps) float: mixed-venous blood oxygen content of each dog at each step, in mL O2 per dL
- Sizes: animals = 12, steps = 8.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 30-33 and 36: per dog, VO2 and DO2 are computed from the first CO determination and the OLS slope of VO2 on DO2 over the 8 steps is raw Cov / raw Var(DO2); the slopes are averaged (no correction for the CO error, STR87).
- **Fixed, `fixed_body.py`.** Lines 30-36 (insertion 34-36): per dog, s2 = var(CO - CO_2, ddof 1) / 2 over the 8 steps (pooled across steps within dog) and the error terms k^2 s2 mean(D Ca) and k^2 s2 mean(Ca^2) are subtracted from the numerator and the denominator of the slope; the mean over dogs and the threshold 0.15 are shared.
- Error lines: faulty 30-33 and 36; correction lines: fixed 30-36 (insertion 34-36). All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Mean within-dog slope of error-free oxygen consumption on error-free delivery.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 22; fixed line(s) 22. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 24; fixed line(s) 24 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 34; fixed line(s) 37.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result True, type bool or None; a repeat on a copy gave the same result; time 0.1 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The None rule "a corrected variance is not positive" is applied to the corrected Var(DO2) of every dog (any non-positive value gives None for the whole criterion); same reading of "zero variance" as in B3B-06, confirmation requested. Content errors negligible, as in the note.
