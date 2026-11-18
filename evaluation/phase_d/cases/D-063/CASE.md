# D-063 (B3B-14, reserve)

## 1. Identity
- Case id: D-063 (local id B3B-14 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `shared-measured-component`. Statistic family: `R-squared`. Subtype: None.

## 2. Source and documenting passage
- Source key: STR87.
- Passage: 'This paper presents a method of correcting for this bias in the linear regression coefficient and the Pearson correlation coefficient when calculations involve the nonlinear and linear combination of the measured variables. The general solution is obtained when the first two terms of a Taylor series expansion of the function can be used to represent the function, as in the case of multiplication.' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Among 600 anaesthetised dogs, whole-body oxygen consumption, computed from the measured cardiac output and the arterial and mixed-venous blood oxygen contents by the standard Fick definition, depends on cardiac output: the R-squared of the linear regression of oxygen consumption on cardiac output is at least 0.25.
- Data keys:
  - `cardiac_output` (subjects,) float: cardiac output of each dog, in L per min
  - `cardiac_output_2` (subjects,) float: a second, independent determination of the cardiac output of each dog, in L per min
  - `arterial_o2_content` (subjects,) float: arterial blood oxygen content of each dog, in mL O2 per dL
  - `venous_o2_content` (subjects,) float: mixed-venous blood oxygen content of each dog, in mL O2 per dL
- Sizes: subjects = 600.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 26-31 and 34: VO2 = 10 CO (CaO2 - CvO2) is regressed on the first CO determination; R-squared = raw Cov^2 / (Var(VO2) Var(CO)) (= R-squared of the simple regression); no correction for the CO error on both sides (STR87).
- **Fixed, `fixed_body.py`.** Lines 26-35 (insertion 32-35): s2 = var(CO - CO_2, ddof 1) / 2; first-order Taylor terms k^2 s2 mean(D^2), s2 and k s2 mean(D) are subtracted from Var(VO2), Var(CO) and Cov(VO2, CO); the corrected R-squared is the square of the corrected correlation (shared decision line). Content errors taken as negligible (documented simplification).
- Error lines: faulty 26-31 and 34; correction lines: fixed 26-35 (insertion 32-35). All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Variance of the error-free consumption explained by the error-free cardiac output.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 21; fixed line(s) 21. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 23; fixed line(s) 23 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 32; fixed line(s) 36.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result False, type bool or None; a repeat on a copy gave the same result; time 0.2 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The None rule is the shared line `if not (v > 0.0 and w > 0.0)`; same reading of "zero variance" as in B3B-06, confirmation requested. Content errors negligible, as in the note.
