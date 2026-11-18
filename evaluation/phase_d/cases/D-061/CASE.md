# D-061 (DEC-01)

## 1. Case
- Case id: D-061 (local id DEC-01); class B-1; tag (mechanism): select-then-test-same-data; statistic family: proportion; subtype: None.

## 2. Source
- Source key: KRI09. Documenting passage: "Nonindependent selective analysis is incorrect and should not be acceptable in neuroscientific publications." Also the regional-activation simulation (ROI chosen by contrast A-D, contrast A-B with true value zero tested on the same data, 20 of 100 runs significant at p<0.05).
- Who read it and how: read by the brief author in the PMC full text through a summarising fetch (WebFetch); I did not re-read the source and fetched no URL.

## 3. Brief
Claim: Each of 1500 voxels was measured in each of 10 runs of an experiment with four stimulus conditions, labelled A, B, C and D. Claim: among the voxels whose expected response to condition A is greater than their expected response to condition D, the proportion whose expected response to condition A is also greater than their expected response to condition B is at least 0.70.

Data keys:
  - `response`, (voxels, runs, conditions), float: estimated response amplitude of each voxel in each run to each stimulus condition; the conditions axis holds A, B, C, D in this order

Sizes: {"voxels": 1500, "runs": 10, "conditions": 4}

## 4. Mapping
Faulty (`D-061/faulty_body.py`): lines 116-125 carry the error. Lines 116-120 choose the voxels (one-sided one-sample t test of A - D across all 10 runs, df = 9, p < 0.001, the uncorrected primary threshold of the source's Example 1; the `0.001` is on line 120). Lines 123-125 then compute the proportion with mean A > mean B over the same 10 runs and compare it with 0.70. Selection and estimation use the same data. Parameters: p < 0.001, 10 runs, threshold 0.70 (claim); documented in the private note.

Fixed (`D-061/fixed_body.py`): lines 116-132. The runs are split into even- and odd-indexed runs (line 116); voxels are chosen on one half (lines 121-125, t test with df = 4, same p < 0.001) and the proportion A > B is computed on the other half (lines 126-129); the two roles are swapped by the loop (line 118) and the two proportions averaged (line 132). Same helpers, same threshold, same proportion statistic.

Estimand: the population proportion of voxels with expected A > expected B among voxels with expected A > expected D, estimated on runs independent of the choice of voxels.

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: 1 voxel kept (non-empty selection). Also: non-finite values; zero variance of A - D in some voxel across the runs used (the t statistic is undefined). In the fixed body a direction with an empty selection is skipped and the other direction alone is used; None only if neither direction keeps a voxel.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated array (1500, 10, 4) with 600 voxels whose A is shifted by 1.5 and Gaussian noise: True; pure-noise array: False; per run 3 timing calls plus 1 repeat call, 3.0 and 4.3 ms per call; repeated calls gave equal answers. Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
Runs are split by parity (even/odd), the form the source's correction takes, rather than the example "runs 0-4 / 5-9" of the private note (both are named there). "None if no voxel is kept in either direction" is read as: no voxel kept in either of the two directions (one empty direction is skipped, not a reason for None). The critical t is found by bisection of the hand-written t tail and equals p < 0.001. The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta function (Lanczos log-gamma, continued fraction), because a body may import only numpy. Problems: none.
