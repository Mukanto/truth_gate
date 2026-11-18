# D-047 (DEC-03)

## 1. Case
- Case id: D-047 (local id DEC-03); class B-1; tag (mechanism): extreme-group-change; statistic family: proportion; subtype: None.

## 2. Source
- Source key: MOR03. Documenting passage: "Any intervention aimed at a group or characteristic that is very different from the average will appear to be successful because of regression to the mean." (SOURCES_D)
- Who read it and how: read by the brief author in the PMC full text through a summarising fetch; I did not re-read the source and fetched no URL.

## 3. Brief
Claim: 600 patients with menopausal hot flushes received a treatment. Symptom severity (scale 0 to 100, higher is worse) was scored at a screening visit, again at entry on the day treatment began, and again 12 weeks later. Claim: among patients whose screening score was at least 60, at least half have a week-12 score that is 10 or more points below their entry score (proportion of at least 0.5).

Data keys:
  - `screening`, (patients,), float: symptom severity score at the screening visit
  - `entry`, (patients,), float: symptom severity score at entry, on the day treatment began
  - `week12`, (patients,), float: symptom severity score 12 weeks after treatment began

Sizes: {"patients": 600}

## 4. Mapping
Faulty (`D-047/faulty_body.py`): line 28 carries the error: the change of flagged patients is measured from the flagging measurement itself (`s[flag] - w[flag]`, screening minus week 12). Line 25 flags patients with screening >= 60 (the claim's threshold); line 29 compares the proportion with change >= 10 against 0.5. Documented in the private note (MOR03: groups far from the average improve by regression to the mean).

Fixed (`D-047/fixed_body.py`): line 28 only: `e[flag] - w[flag]`, the entry score (a second pre-treatment measurement, not used for flagging) minus week 12. Everything else is identical (the flag is still the screening score).

Estimand: the share of the flagged patients whose score fell by 10 or more from an independent pre-treatment measurement (the change after treatment among those flagged).

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: 1 flagged patient (non-empty selection); non-finite values.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated latent-level data (600 patients): False; below 0.1 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
none. Problems: none.
