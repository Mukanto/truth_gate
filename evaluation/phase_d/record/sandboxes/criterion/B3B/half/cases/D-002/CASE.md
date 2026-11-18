# D-002 (B3B-10, case)

## 1. Identity
- Case id: D-002 (local id B3B-10 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `shared-measured-component`. Statistic family: `correlation`. Subtype: None.

## 2. Source and documenting passage
- Source key: MOR86.
- Passage: 'the presence of error in the common set of measured variables distorts the relationship among the calculated quantities'; 'This article presents a method of correcting for such distortions in the Pearson correlation coefficient and in the linear regression coefficient for linear calculations involving two measured variables.' (abstract, Europe PMC).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Across 120 anaesthetised animals, tissues extract more oxygen when more is supplied: the Pearson correlation between the arterial-minus-mixed-venous oxygen content difference and the arterial oxygen content is at least 0.30.
- Data keys:
  - `arterial_o2_content` (subjects,) float: arterial blood oxygen content of each animal, in mL O2 per dL
  - `arterial_o2_content_2` (subjects,) float: a second, independent determination of the arterial blood oxygen content of each animal, in mL O2 per dL
  - `venous_o2_content` (subjects,) float: mixed-venous blood oxygen content of each animal, in mL O2 per dL
  - `venous_o2_content_2` (subjects,) float: a second, independent determination of the mixed-venous blood oxygen content of each animal, in mL O2 per dL
- Sizes: subjects = 120.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Lines 25-29 and 32: D = arterial - venous content and the arterial content (first determinations) are correlated from raw moments; no correction for the arterial error present in both (MOR86).
- **Fixed, `fixed_body.py`.** Lines 25-33 (insertion 30-34): s_a2 = var(Ca - Ca_2, ddof 1) / 2 and s_v2 = var(Cv - Cv_2, ddof 1) / 2 from the repeats; corrected Cov(D, Ca) = Cov - s_a2, corrected Var(Ca) = Var(Ca) - s_a2, corrected Var(D) = Var(D) - s_a2 - s_v2; correlation from the corrected moments (shared lines). Additive independent errors, as chosen in the private note.
- Error lines: faulty 25-29 and 32; correction lines: fixed 25-33 (insertion 30-34). All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Correlation between the true content difference and the true arterial content.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 21; fixed line(s) 21. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 23; fixed line(s) 23 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 30; fixed line(s) 35.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result None (corrected variance not positive: pure noise), type bool or None; a repeat on a copy gave the same result; time 0.1 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The None rule "a corrected variance is not positive" is in the shared line `if not (v > 0.0 and w > 0.0)` (only two of the three corrected variances are used in the denominator; the covariance has no sign constraint). Same reading of "zero variance" as in B3B-06; confirmation requested.
