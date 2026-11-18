# D-012 (DEC-06)

## 1. Case
- Case id: D-012 (local id DEC-06); class B-6; tag (mechanism): units-not-independent; statistic family: proportion; subtype: None.

## 2. Source
- Source key: HUR84. Documenting passage: Abstract as reproduced in search summaries: pseudoreplication is the use of inferential statistics to test for treatment effects where treatments are not replicated or replicates are not statistically independent.
- Who read it and how: read by the brief author as the abstract reproduced in search summaries (the full text is a scanned PDF and was not readable); I did not re-read the source and fetched no URL.

## 3. Brief
Claim: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level.

Data keys:
  - `occupied`, (plots, quadrats), bool: True if the species was present in that quadrat of that plot
  - `exclosure`, (plots,), bool: True if the plot was fenced against grazers

Sizes: {"plots": 10, "quadrats": 30}

## 4. Mapping
Faulty (`D-012/faulty_body.py`): lines 20-35 carry the error: all 300 quadrats are pooled and treated as independent (lines 22-31); the difference of occupied proportions (fenced minus open, line 34) must be >= 0.10 and the pooled-variance two-proportion z test one-sided at 0.05 (z > 1.6448536269514722) significant (line 35). Parameters 0.10 and 0.05 come from the claim; the intra-plot correlation of 0.3 and the design effect are in the private note and are not used by the criterion. Documented in the private note (HUR84: replicates not statistically independent).

Fixed (`D-012/fixed_body.py`): lines 108-118: occupancy per plot (line 110), Welch t test one-sided at 0.05 on the plot occupancies (helper `_welch`, defined at line 78), and the same rule (difference of mean plot occupancies >= 0.10 and p < 0.05, line 118).

Estimand: the difference of mean plot occupancy (fenced minus open) with plots as replicates.

## 5. Allowed-guard minimum used
Private note minimum: 2. Used: 2 plots per group (fixed); at least one unit per group (faulty); zero variance (faulty: pooled proportion 0 or 1; fixed: both groups have zero variance, so the standard error is zero).

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated Bernoulli occupancy (10 plots, 30 quadrats, 5 fenced): False; 0.1 ms per call (3 calls + 1 repeat, equal); the Welch p-value of `_welch` matched scipy.stats.ttest_ind (Welch, alternative greater) to 4e-16. Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
"A zero variance" is read as a zero standard error of the difference (both groups constant); a single constant group with a varying other group still has a defined Welch statistic. The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta function (Lanczos log-gamma, continued fraction), because a body may import only numpy. Problems: none.
