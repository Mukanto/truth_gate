# D-001 (B3B-13, reserve)

## 1. Identity
- Case id: D-001 (local id B3B-13 of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `change-vs-baseline`. Statistic family: `correlation`. Subtype: None.

## 2. Source and documenting passage
- Source key: BLO77.
- Passage: 'it is often of interest to investigate whether there exists a relationship between the rate of change and the initial value.' 'the maximum likelihood (ML) estimates of the second-order moments of the true slope and the true initial value are obtained by simple adjustments of the corresponding moments of the estimated quantities.' (abstract, OpenAlex).
- Read by: the brief author, through the abstract (saved in `half\fetched\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: Among 150 adults with systolic blood pressure measured at three annual visits, those with a higher initial blood pressure have a lower yearly rate of change: the Pearson correlation between an individual's underlying yearly rate of change in systolic blood pressure and the individual's underlying initial systolic blood pressure is at most -0.30.
- Data keys:
  - `systolic_bp` (individuals, occasions) float: systolic blood pressure of each individual at each of three annual visits, with the visits in time order, in mmHg
- Sizes: individuals = 150, occasions = 3.

## 4. Mapping
- **Faulty, `faulty_body.py`.** Line 25: the observed first reading x[:, 0] is the correlate of the estimated individual slope (3 readings); Pearson correlation from raw moments (shared).
- **Fixed, `fixed_body.py`.** Lines 25-26 and 33-37: as in B3B-06 with m = 3: a_i is the fitted level at the first visit, s2 = SSR / (n (m - 2)) (one degree of freedom per individual), Var(a) - s2 (1/m + tbar^2 / Sxx), Var(b) - s2 / Sxx, Cov(a, b) + s2 tbar / Sxx; the correlation is formed from the corrected moments (shared lines).
- Error lines: faulty 25; correction lines: fixed 25-26 and 33-37. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\make_bodies.py`).
- **Estimand** (the quantity the claim is about): Correlation between the true rate of change and the true initial value.

## 5. Allowed guards used (minimum: 2)
- Minimum size: faulty line(s) 16; fixed line(s) 16. The minimum is 2 (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) 18; fixed line(s) 18 (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) 26, 32; fixed line(s) 27, 38.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result True, type bool or None; a repeat on a copy gave the same result; time 0.1 ms.
- Run 2 (`work\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- The None rule "a corrected variance is not positive" covers both corrected Var(a) and Var(b); same reading of "zero variance" as in B3B-06, confirmation requested.
