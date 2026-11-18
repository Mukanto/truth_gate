# D-016 (DEC-08)

## 1. Case
- Case id: D-016 (local id DEC-08); class B-6; tag (mechanism): units-not-independent; statistic family: correlation; subtype: None.

## 2. Source
- Source key: LAZ18. Documenting passage: "If treatments are randomly and independently applied to an entity other than the individual animal, then the sample size is not the number of animals." (Animal experiments section)
- Who read it and how: read by the brief author in the PMC full text through a summarising fetch; I did not re-read the source and fetched no URL.

## 3. Brief
Claim: Fourteen pregnant dams each had a measured exposure level to a chemical, and 4 pups per dam were scored on a performance test at weaning. Claim: across dams, the correlation between a dam's exposure level and the mean score of her pups is positive, judged by a one-sided test of the correlation against zero at the 0.05 level.

Data keys:
  - `exposure`, (dams,), float: exposure level of each dam
  - `outcome`, (dams, pups), float: performance score at weaning of each pup of each dam

Sizes: {"dams": 14, "pups": 4}

## 4. Mapping
Faulty (`D-016/faulty_body.py`): line 112 carries the error: each dam's exposure is repeated for each of her pups and the Pearson correlation with the 56 pup scores is tested one-sided with df = 54 (`t = r sqrt(54/(1-r^2))`, helper `_corr_p`, shared, line 78). Line 115 applies p < 0.05. Documented in the private note and LAZ18 (the sample size is not the number of animals when treatment is applied to the litter).

Fixed (`D-016/fixed_body.py`): line 112 only: `_corr_p(x, y.mean(axis=1))`, the correlation of exposure with the dam's mean pup score over the 14 dams (df = 12).

Estimand: the correlation of exposure with litter mean score, dams as replicates.

## 5. Allowed-guard minimum used
Private note minimum: 3. Used: 3 units (pups in the faulty body, dams in the fixed body); non-finite values; zero variance of exposure or of the scores.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated random-intercept data (14 dams, 4 pups): False; 0.1 ms per call (3 calls + 1 repeat, equal); the correlation p-value of `_corr_p` matched scipy.stats.pearsonr (alternative greater) to 1.3e-15. Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta function (Lanczos log-gamma, continued fraction), because a body may import only numpy. For a perfect correlation (1 - r^2 = 0) the helper takes t as infinite instead of dividing by zero. Problems: none.
