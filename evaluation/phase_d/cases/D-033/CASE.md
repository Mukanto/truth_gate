# D-033 (DEC-R1)

## 1. Case
- Case id: D-033 (local id DEC-R1); class B-1; tag (mechanism): select-then-test-same-data; statistic family: correlation; subtype: None. Reserve case.

## 2. Source
- Source key: KRI10. Documenting passage: "The effect-size statistics need to be independent of the selection criterion" (PMC full text; a design in which half the data choose signal-carrying voxels and the other half estimate the signal).
- Who read it and how: read by the brief author in the PMC full text through a summarising fetch; I did not re-read the source and fetched no URL.

## 3. Brief
Claim: The response of each of 1000 voxels was estimated on each of 60 trials, in which a stimulus of varying intensity was presented. Claim: in the population, the 25 voxels whose trial-by-trial response is most strongly correlated with stimulus intensity have a mean correlation with intensity of at least 0.25.

Data keys:
  - `betas`, (voxels, trials), float: estimated response amplitude of each voxel on each trial
  - `intensity`, (trials,), float: stimulus intensity presented on each trial

Sizes: {"voxels": 1000, "trials": 60}

## 4. Mapping
Faulty (`D-033/faulty_body.py`): lines 33-39 carry the error: Pearson r of every voxel with intensity over all 60 trials (line 33), the 25 voxels with the largest r kept (line 36; 25 is the claim's number), their mean r from the same trials compared with 0.25 (line 39). Documented in the private note (KRI10: effect-size statistics must be independent of the selection criterion).

Fixed (`D-033/fixed_body.py`): lines 31-49: trials split into even- and odd-indexed halves (line 32); the 25 voxels chosen on one half (lines 39-42), their mean r computed on the other (line 45), roles swapped (line 36), the two mean r averaged through Fisher z (lines 48-49) and compared with 0.25.

Estimand: the mean population correlation with intensity of the 25 voxels chosen without the trials used for estimating it.

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: 1 voxel selected; non-finite values; zero variance (a voxel or the intensity constant on the trials used). Fewer than 2 trials (fewer than 2 per half in the fixed body) is too small.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated Gaussian arrays (1000, 60) and (60,), null data: False; 0.7 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
Same readings as D-028: Fisher z on the per-half mean r; even/odd trial halves ("odd-numbered trials" in the note; the swap makes the base of the index irrelevant). Problems: none.
