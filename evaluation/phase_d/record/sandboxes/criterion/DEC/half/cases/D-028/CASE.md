# D-028 (DEC-02)

## 1. Case
- Case id: D-028 (local id DEC-02); class B-1; tag (mechanism): select-then-test-same-data; statistic family: correlation; subtype: None.

## 2. Source
- Source key: VUL09. Documenting passage: Abstract: more than half of 55 surveyed articles computed correlations voxel by voxel, then averaged only the voxels above a threshold; the reported correlations exceed what the reliabilities of the measures allow.
- Who read it and how: read by the brief author in the abstract through Europe PMC; I did not re-read the source and fetched no URL.

## 3. Brief
Claim: Twenty subjects each completed a task during functional imaging, giving an activation value in each of 1000 voxels, and each completed a personality questionnaire. Claim: in the population from which the subjects come, the 20 voxels whose activation is most strongly correlated with the questionnaire score have a mean correlation with that score of at least 0.5.

Data keys:
  - `activation`, (subjects, voxels), float: task-related activation of each voxel in each subject
  - `trait`, (subjects,), float: personality questionnaire score of each subject

Sizes: {"subjects": 20, "voxels": 1000}

## 4. Mapping
Faulty (`D-028/faulty_body.py`): lines 33-39 carry the error. Pearson r of every voxel with the trait over all 20 subjects (line 33), the 20 voxels with the largest r are kept (line 36; 20 is the claim's number), and their mean r, computed in the same subjects, is compared with 0.5 (line 39). Documented in the private note (VUL09 abstract: voxels thresholded on the correlation, then the correlations of the selected voxels averaged).

Fixed (`D-028/fixed_body.py`): lines 31-49. Subjects are split into two halves (line 32); the top 20 voxels are chosen on one half (lines 39-42) and their mean r computed on the other (line 45); the halves are swapped by the loop (line 36) and the two mean r values averaged through Fisher z and back-transformed (lines 48-49), then compared with 0.5. Same helper `_corr_cols`, same k = 20, same threshold.

Estimand: the mean population correlation with the trait of the 20 voxels chosen without using the subjects on which the correlation is estimated.

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: 1 voxel selected; also non-finite values and zero variance (a voxel or the trait constant in the subjects used; correlation undefined). Fewer than 2 subjects (fewer than 2 per half in the fixed body) is treated as too small for a correlation.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated Gaussian arrays (20, 1000) and (20,), null data: False; 0.4 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
Fisher z is applied to the per-half mean r (the arithmetic mean over the 20 voxels of each half) and the two half values are averaged in z; the private note ("compute their mean r on the other 10; swap the halves and average (Fisher z averaged, back-transformed)") allows this and another reading (z-averaging all 40 voxel correlations); I kept the structure of the faulty body (mean r of 20 voxels). Halves are even/odd subject indices. Problems: none.
