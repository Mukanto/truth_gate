# D-032 (DEC-05)

## 1. Case
- Case id: D-032 (local id DEC-05); class B-6; tag (mechanism): significant-here-not-there; statistic family: proportion; subtype: None.

## 2. Source
- Source key: NIE11. Documenting passage: SOURCES_D: a difference between two effects claimed because one is significant and the other is not. Abstract (Europe PMC): in a review of 513 articles from five journals, 78 used the correct method and 79 the incorrect one.
- Who read it and how: read by the brief author in the abstract through Europe PMC; I did not re-read the source and fetched no URL.

## 3. Brief
Claim: 240 participants each received either a drug or a vehicle, and each was classified as a responder or not. Some participants carry a gene variant. Claim: the drug raises the proportion of responders more in carriers than in non-carriers, that is, the difference between the two drug-minus-vehicle differences in responder proportion (carriers minus non-carriers) is positive, judged by a one-sided test at the 0.05 level.

Data keys:
  - `responder`, (participants,), bool: True if the participant met the response criterion
  - `drug`, (participants,), bool: True if the participant received the drug, False if the vehicle
  - `carrier`, (participants,), bool: True if the participant carries the gene variant

Sizes: {"participants": 240}

## 4. Mapping
Faulty (`D-032/faulty_body.py`): lines 43-47 carry the error (with the helper `_z_pooled`, line 9): a pooled-variance two-sample z test of the drug-minus-vehicle difference in responder proportion within carriers and within non-carriers separately, each one-sided at 0.05 (z > 1.6448536269514722); the claim is declared supported when the carrier effect is significant and the non-carrier effect is not (line 47). Documented in the private note and in NIE11 (a difference between effects claimed because one is significant and the other is not).

Fixed (`D-032/fixed_body.py`): lines 35-44: one one-sided z test at 0.05 of the difference of the two differences (carriers minus non-carriers), standard error from the four cell proportions (lines 39-43). Same critical value 1.6448536269514722.

Estimand: the difference between the carrier effect and the non-carrier effect on the proportion scale.

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: 1 participant in each of the four (carrier, drug) cells; zero variance (faulty: pooled variance zero in a stratum; fixed: the standard error is zero).

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated Bernoulli data (240 participants, drug effect 0.15 in both strata): False; below 0.1 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
The constant 1.6448536269514722 is the 0.95 quantile of the standard normal (the claim's 0.05 one-sided level); no numeric tail function is needed. Problems: none.
