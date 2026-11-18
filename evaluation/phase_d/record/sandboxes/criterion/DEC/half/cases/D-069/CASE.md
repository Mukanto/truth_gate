# D-069 (DEC-04)

## 1. Case
- Case id: D-069 (local id DEC-04); class B-1; tag (mechanism): split-by-baseline-compare-change; statistic family: mean; subtype: None.

## 2. Source
- Source key: BAR05. Documenting passage: Abstract: the effect of regression to the mean "becomes more noticeable with increasing measurement error and when follow-up measurements are only examined on a sub-sample selected using a baseline value".
- Who read it and how: read by the brief author in the publisher abstract only; I did not re-read the source and fetched no URL.

## 3. Brief
Claim: In a trial of a blood-pressure drug, 900 patients had systolic pressure measured at baseline and again after 6 months, and the array treated marks which patients received the drug. The reduction of a patient is the baseline pressure minus the 6-month pressure. Claim: the reduction attributable to the drug (mean reduction in treated patients minus mean reduction in untreated patients) is larger in patients in the top third of baseline pressures than in patients in the bottom third of baseline pressures, by at least 3 mmHg.

Data keys:
  - `baseline_sbp`, (patients,), float: systolic blood pressure in mmHg at baseline
  - `followup_sbp`, (patients,), float: systolic blood pressure in mmHg after 6 months
  - `treated`, (patients,), bool: True if the patient received the drug

Sizes: {"patients": 900}

## 4. Mapping
Faulty (`D-069/faulty_body.py`): lines 27-34 carry the error. Thirds are cut among the treated patients only (line 29, percentiles 100/3 and 200/3 of the treated patients' baselines; the private note says 33rd and 67th), and the top-third minus bottom-third mean reduction of the treated patients (reduction = baseline - follow-up, line 26) is compared with 3 mmHg (line 34), so the movement of extreme baselines toward the mean enters the contrast and there is no untreated reference. Documented in the private note (BAR05 abstract).

Fixed (`D-069/fixed_body.py`): lines 27-37. Thirds over all patients (line 29), four cells (top/bottom third x treated/untreated, line 32), the drug-attributable reduction (treated minus untreated mean reduction) in the top and in the bottom third (lines 35-36), and the top-minus-bottom difference of these compared with 3 mmHg (line 37).

Estimand: the difference between the top and bottom baseline thirds of the drug-attributable reduction (treated minus untreated), a treatment-by-baseline contrast.

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: 1 patient in each cell needed (faulty: one in each of the treated top and bottom thirds; fixed: one in each of the four cells); non-finite values.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated latent-level data with a drug effect of 5 mmHg (900 patients): False; 0.2 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
"Thirds" are cut at the 100/3 and 200/3 percentiles (linear interpolation) with membership `<=` the lower and `>=` the upper cut; the private note says 33rd and 67th percentile, which I read as thirds. Problems: none.
