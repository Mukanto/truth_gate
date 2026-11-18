# D-048 (B3B-08, case)

## 1. Identity
- Case id: D-048 (local id B3B-08 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `shared-measured-component`. Statistic family: `correlation`. Subtype: None.

## 2. Source and documenting passage
- Source key: STR87.
- Passage: 'If a measured variable is used in the calculation of two derived parameters, error in the measurement will couple the calculated parameters and introduce a bias'; 'This paper presents a method of correcting for this bias in the linear regression coefficient and the Pearson correlation coefficient' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Among 40 anaesthetised dogs, whole-body oxygen consumption and oxygen delivery, each computed from the measured cardiac output and the arterial and mixed-venous blood oxygen contents by the standard Fick definitions, are positively related: their Pearson correlation is at least 0.40.
- Data keys:
  - `cardiac_output` (subjects,) float: cardiac output of each dog, in L per min
  - `cardiac_output_2` (subjects,) float: a second, independent determination of the cardiac output of each dog, in L per min
  - `arterial_o2_content` (subjects,) float: arterial blood oxygen content of each dog, in mL O2 per dL
  - `venous_o2_content` (subjects,) float: mixed-venous blood oxygen content of each dog, in mL O2 per dL
- Sizes: subjects = 40.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 25-32 and 35: VO2 = 10 CO (CaO2 - CvO2) and DO2 = 10 CO CaO2 are computed from the first cardiac output determination and their raw sample variances and covariance (np.cov, ddof 1) give the correlation; no correction for the error of CO that enters both (STR87). 10 converts L/min x mL/dL to mL/min.
- **Fixed, `fixed_body.py`.** Lines 25-36 (insertion 33-36): s2 = var(CO - CO_2, ddof 1) / 2 is the error variance of CO from the independent repeat; the first-order Taylor error terms k^2 s2 mean(D^2), k^2 s2 mean(Ca^2), k^2 s2 mean(D Ca) (D = Ca - Cv) are subtracted from Var(VO2), Var(DO2) and Cov(VO2, DO2); the correlation is formed from the corrected moments (shared lines). Errors of the two contents are taken as negligible, the documented simplification (no repeat key for them).
- Error lines: faulty 25-32 and 35; correction lines: fixed 25-36 (insertion 33-36). All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Correlation between error-free oxygen consumption and delivery.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 21; fixed line(s) 21. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 23; fixed line(s) 23 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 33; fixed line(s) 37.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result True, type bool or None; a repeat on a copy gave the same result; time 0.1 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The private note lists no None rule for B3B-08; the shared line `if not (v > 0.0 and w > 0.0)` returns None when a corrected variance is not positive (the note of B3B-09, B3B-10 and B3B-14 has that rule). For the faulty body the same line is the zero-variance guard. This reads "zero variance" as "variance not positive after correction"; I request confirmation. Content errors are taken as negligible (the note's documented simplification).
