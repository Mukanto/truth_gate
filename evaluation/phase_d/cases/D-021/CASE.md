# D-021 (DEC-R4)

## 1. Case
- Case id: D-021 (local id DEC-R4); class B-6; tag (mechanism): units-not-independent; statistic family: proportion; subtype: None. Reserve case.

## 2. Source
- Source key: HUR84. Documenting passage: Abstract as reproduced in search summaries; temporal pseudoreplication (repeated samples through time from the same unit) as described in secondary summaries of the paper.
- Who read it and how: read by the brief author as the abstract in search summaries and secondary summaries (the full text was not readable); I did not re-read the source and fetched no URL.

## 3. Brief
Claim: In a field experiment, 8 plots were each surveyed on 12 successive dates and scored as occupied or not by a species on each date; the array fenced marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.15, where the occupancy of a plot is the fraction of dates on which it is occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level.

Data keys:
  - `present`, (plots, dates), bool: True if the species was present in that plot on that date; dates are in time order
  - `fenced`, (plots,), bool: True if the plot was fenced against grazers

Sizes: {"plots": 8, "dates": 12}

## 4. Mapping
Faulty (`D-021/faulty_body.py`): lines 20-35 carry the error: all 96 plot-date records are pooled and treated as independent; the difference of occupied proportions (fenced minus open) must be >= 0.15 and the pooled two-proportion z test one-sided at 0.05 (z > 1.6448536269514722) significant (line 35). Documented in the private note (HUR84: temporal pseudoreplication).

Fixed (`D-021/fixed_body.py`): lines 108-118: occupancy per plot as the mean over its 12 dates (line 110), Welch t test one-sided at 0.05 on the plot occupancies (helper `_welch`, line 78), difference >= 0.15 and p < 0.05 (line 118).

Estimand: the difference of mean plot occupancy with plots as replicates.

## 5. Allowed-guard minimum used
Private note minimum: 2. Used: 2 plots per group (fixed); at least one record per group (faulty); zero variance (faulty: pooled proportion 0 or 1; fixed: standard error zero).

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated Bernoulli presence (8 plots, 12 dates, 4 fenced): False; 0.1 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
Same reading of "zero variance" as D-012. The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta function (Lanczos log-gamma, continued fraction), because a body may import only numpy. Problems: none.
