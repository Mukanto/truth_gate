# D-052 (DEC-R3)

## 1. Case
- Case id: D-052 (local id DEC-R3); class B-6; tag (mechanism): significant-here-not-there; statistic family: mean; subtype: None. Reserve case.

## 2. Source
- Source key: MAK19. Documenting passage: "one should not infer that one correlation is greater than the other." (section on comparing two effects without a direct test: groups of 20 participants, an effect significant in one group but not the other, equal means, higher variance in one group)
- Who read it and how: read by the brief author in the PMC full text (first 100000 of 204772 characters); I did not re-read the source and fetched no URL.

## 3. Brief
Claim: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level.

Data keys:
  - `pre`, (participants,), float: performance score before the programme
  - `post`, (participants,), float: performance score after the programme
  - `young`, (participants,), bool: True for young participants, False for old participants

Sizes: {"participants": 40}

## 4. Mapping
Faulty (`D-052/faulty_body.py`): lines 115-119 carry the error (helper `_t1_p`, line 78): a one-sample one-sided t test (mean improvement > 0, 0.05) in the young and in the old, and the claim is declared supported when the young test is significant and the old test is not (line 119). Documented in the private note and MAK19 (one effect significant in one group but not the other, no direct test of the difference).

Fixed (`D-052/fixed_body.py`): lines 118-121: a Welch two-sample one-sided t test of the improvement (young minus old) at 0.05 (helper `_welch`, line 78), supported when p < 0.05.

Estimand: the difference in mean improvement between young and old.

## 5. Allowed-guard minimum used
Private note minimum: 2. Used: 2 participants per group; non-finite values; zero variance (faulty: a group with zero standard deviation; fixed: standard error zero).

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated data (40 participants, 20 young): False; 0.1 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta function (Lanczos log-gamma, continued fraction), because a body may import only numpy. Problems: none.
