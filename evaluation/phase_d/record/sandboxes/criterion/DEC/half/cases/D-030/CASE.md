# D-030 (DEC-R2)

## 1. Case
- Case id: D-030 (local id DEC-R2); class B-1; tag (mechanism): split-by-baseline-compare-change; statistic family: proportion; subtype: None. Reserve case.

## 2. Source
- Source key: MAK19. Documenting passage: "circular analysis recruits the noise (inherent to any empirical data) to inflate the statistical outcome" (section on circular analysis: neurons binned by baseline activity, a significant interaction found although there is no overall change).
- Who read it and how: read by the brief author in the PMC full text (first 100000 of 204772 characters); I did not re-read the source and fetched no URL.

## 3. Brief
Claim: Each of 400 neurons was recorded on 40 trials before and on 40 trials after a manipulation. Claim: the proportion of neurons whose expected firing rate rises after the manipulation is larger among neurons whose expected pre-manipulation rate is below 8 Hz than among neurons whose expected pre-manipulation rate is at least 8 Hz, by at least 0.20.

Data keys:
  - `pre`, (neurons, trials), float: firing rate in Hz of each neuron on each trial before the manipulation
  - `post`, (neurons, trials), float: firing rate in Hz of each neuron on each trial after the manipulation

Sizes: {"neurons": 400, "trials": 40}

## 4. Mapping
Faulty (`D-030/faulty_body.py`): lines 22-28 carry the error: one estimate of the baseline (the mean of all pre trials, line 22) both assigns the neuron to the below-8-Hz or at-least-8-Hz bin (line 24) and is the reference of the change (line 23, mean post > mean pre); the difference of the proportions of rising neurons (low bin minus high bin) is compared with 0.20 (line 28). Documented in the private note (MAK19: circular analysis with neurons binned by baseline).

Fixed (`D-030/fixed_body.py`): lines 22-35: the pre trials are split into even- and odd-indexed halves (line 24); the bin comes from one half (line 28), the change is the mean post minus the mean of the other half (line 29), the same proportions and rule; the roles are swapped by the loop (line 27) and the two differences averaged (line 35).

Estimand: the same difference of proportions with the bin assigned by one baseline estimate and the change measured from an independent one.

## 5. Allowed-guard minimum used
Private note minimum: 1. Used: A non-empty bin (below 8 Hz and at least 8 Hz) is needed in both directions of the fixed body; non-finite values; at least 2 pre trials.

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated gamma-rate data (400 neurons, 40 trials): False; 0.2 ms per call (3 calls + 1 repeat, equal). Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
"None if a bin is empty" is applied to either direction of the fixed body. "Even-numbered" and "odd-numbered" trials are the two parity classes of the trial index; the swap makes the base of the index irrelevant. Problems: none.
