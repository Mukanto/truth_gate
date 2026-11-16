# GHZ run 3 on ibm_kingston: results

Job `dbtecsfasvbs73b9l4e0`, submitted 20261116T111730Z, snapshot sha256 `b1ac08d58a3ba91e`, bootstrap B=2000 seed=20261113, quota given 234.0 s.

**Interpretable: yes**

## Answer to Q1 and Q2 (assembled from the pre-written sentences, PREREG section 4)

- Q1: on this run's calibration M2 is not accurate within 0.05 for 4 or 8 qubits.
- Q2: on a new calibration M2 still overpredicts the fidelity at every n.
- Together: the bias persists and exceeds 0.05 at small n.

Labels: within drift (H1)

C-1 per question: Q1 model test = True (max |dF_pred(4), dF_pred(8)| on the snapshot's predictions = 0.0592; on the predictions in use = 0.0592; threshold 0.02).

Predictions in use: snapshot (execution-time calibration: equal, verified; attempt used: execution_calibration_20261116T112310Z.json of 1)

**Headline: n_meas = 8** (largest n with F_hat > 0.5, the H2 definition; 0 = none); n_pred = 24. 95% CI at n_meas excludes 0.5: True (reported, not used by H2). Largest n with CI_low(F) > 0.5: 8.

| n | P (95% CI) | P_pred | C (95% CI) | C_pred | F (95% CI) | F_pred | R = F/F_pred | 97.5% of F_boot/F_pred (H4) | margin 1 - q | sigma_d,R | F_M (ref.) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 0.9290 [0.9170, 0.9400] | 0.9584 | 0.8826 [0.8697, 0.8959] | 0.9265 | 0.9058 [0.8972, 0.9144] | 0.9424 | 0.961 | 0.970 | +0.030 | 0.0110 | 0.9574 |
| 8 | 0.8365 [0.8195, 0.8530] | 0.8773 | 0.6884 [0.6769, 0.6998] | 0.7802 | 0.7624 [0.7517, 0.7724] | 0.8287 | 0.920 | 0.932 | +0.068 | 0.0105 | 0.8752 |
| 16 | 0.5700 [0.5490, 0.5920] | 0.7434 | 0.4101 [0.4003, 0.4197] | 0.5659 | 0.4900 [0.4780, 0.5016] | 0.6547 | 0.749 | 0.766 | +0.234 | 0.0097 | 0.7331 |
| 24 | 0.4465 [0.4260, 0.4685] | 0.6681 | 0.2795 [0.2710, 0.2875] | 0.4627 | 0.3630 [0.3521, 0.3739] | 0.5654 | 0.642 | 0.661 | +0.339 | 0.0091 | 0.6526 |
| 32 | 0.3705 [0.3495, 0.3905] | 0.5385 | 0.1848 [0.1773, 0.1925] | 0.3144 | 0.2777 [0.2663, 0.2889] | 0.4264 | 0.651 | 0.678 | +0.322 | 0.0082 | 0.5132 |
| 48 | 0.2335 [0.2145, 0.2520] | 0.4141 | 0.0922 [0.0859, 0.0986] | 0.1957 | 0.1629 [0.1530, 0.1722] | 0.3049 | 0.534 | 0.565 | +0.435 | 0.0072 | 0.3769 |

Sensitivity I-1: C with Re (nominal phase) instead of |.|

| n | C (abs) | C_re (95% CI) |
|---|---|---|
| 4 | 0.8826 | 0.8794 [0.8664, 0.8928] |
| 8 | 0.6884 | 0.6844 [0.6726, 0.6958] |
| 16 | 0.4101 | 0.4037 [0.3938, 0.4134] |
| 24 | 0.2795 | 0.2729 [0.2647, 0.2812] |
| 32 | 0.1848 | 0.1789 [0.1713, 0.1863] |
| 48 | 0.0922 | 0.0891 [0.0830, 0.0953] |

## Criteria (H1-H3 imported unchanged from ghz2_study.py, H4 from ghz3_study_h4.py)

| id | role | verdict | reading |
|---|---|---|---|
| H1_small_n_accuracy | confirmatory | FAILS | fails |
| H2_gme_reach_matches | reported | FAILS |  |
| H3_population_specific | reported (exploratory) | FAILS |  |
| H4_overprediction_every_n | confirmatory | HOLDS |  |

### Within-drift labels and margins

sigma_rel: P 0.0000, C 0.0224
- H1: decisive n = 8, |F_hat - F_pred| = 0.0663, distance to the 0.05 band = 0.0163, 2 sigma_d,F = 0.0174: within drift
- H4: no within-drift label; n concerned (HOLDS: n with margin < 2 sigma_d,R; FAILS: n with q97.5 >= 1): none

| n | q97.5 | margin 1 - q | 2 sigma_d,R |
|---|---|---|---|
| 4 | 0.9703 | +0.0297 | 0.0220 |
| 8 | 0.9320 | +0.0680 | 0.0210 |
| 16 | 0.7662 | +0.2338 | 0.0193 |
| 24 | 0.6614 | +0.3386 | 0.0183 |
| 32 | 0.6775 | +0.3225 | 0.0165 |
| 48 | 0.5646 | +0.4354 | 0.0143 |

## Reported (not confirmatory): H2 and H3

- H2 (point values): n_meas = 8, n_pred = 24: FAILS
- CI-based reach (largest n with CI low of F > 0.5): 8
- interpolated crossing of F = 0.5: measured 15.7 (95% CI 15.4 to 16.1; 0 of 2000 replicates without a crossing), predicted 27.8
- H3 (exploratory): FAILS

## Power at submission (run/power_run3.json; certs/power.json is a design-time stand-in and is not used)

Power of H1 (truth F_pred - 0.03 at n = 4, 8): 0.959; power of H4 (truth with run-2 ratios): 1.000. Label: at submission, new snapshot. Recomputed from the snapshot's predictions: equal.

Expected outcome under run 2's ratios (reported, not power):

| id | P(HOLDS) | P(FAILS) | P(UNDEFINED) |
|---|---|---|---|
| H1_small_n_accuracy | 0.312 | 0.688 | 0.000 |
| H2_gme_reach_matches | 0.051 | 0.950 | 0.000 |
| H3_population_specific | 0.120 | 0.880 | 0.000 |
| H4_overprediction_every_n | 1.000 | 0.000 | 0.000 |

Sensitivity (power of H1, power of H4):

- correlated: 0.959, 0.999
- drift_x2: 0.742, 0.953

## R(n) = F/F_pred under M2, runs 1, 2 and 3 side by side (descriptive; runs are not pooled, I-4)

- run 1: recomputed with ghz2_core from ghz_heron/run (counts, snapshot, circuits.qpy)
- run 2: RESULTS_GHZ2.json (frozen run 2)

| n | R run 1 | R run 2 | R run 3 |
|---|---|---|---|
| 4 | 0.977 | 0.952 | 0.961 |
| 8 | 0.963 | 0.938 | 0.920 |
| 16 | 0.874 | 0.879 | 0.749 |
| 24 | n/a | 0.864 | 0.642 |
| 32 | 0.858 | 0.851 | 0.651 |
| 48 | 0.854 | 0.844 | 0.534 |

## Tracking: measured change F_run3 - F_run2 against the predicted change (descriptive; CI: shot noise only)

| n | measured change (95% CI, shot noise only) | sigma_d,F | predicted change | predicted inside CI |
|---|---|---|---|---|
| 4 | +0.0140 [+0.0024, +0.0258] | 0.0104 | +0.0059 | True |
| 8 | -0.0706 [-0.0853, -0.0573] | 0.0087 | -0.0592 | True |
| 16 | -0.1228 [-0.1385, -0.1061] | 0.0063 | -0.0422 | False |
| 24 | -0.1464 [-0.1617, -0.1308] | 0.0052 | -0.0240 | False |
| 32 | -0.1063 [-0.1224, -0.0908] | 0.0035 | -0.0250 | False |
| 48 | -0.0799 [-0.0947, -0.0652] | 0.0022 | +0.0173 | False |

## Small-n drift next to H1 (F and C at n = 4, 8)

| n | F run 1 | F run 2 | F run 3 | F_pred run 3 | H1 deviation (run 3) | F run 2 - run 1 | F run 3 - run 2 | C run 2 - run 1 | C run 3 - run 2 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 0.9149 | 0.8917 | 0.9058 | 0.9424 | -0.0367 | -0.0232 | 0.0140 | -0.0373 | 0.0281 |
| 8 | 0.8549 | 0.8331 | 0.7624 | 0.8287 | -0.0663 | -0.0218 | -0.0706 | -0.0287 | -0.1132 |

## C-1 (v3) and the rule-14 check

- at submission: C-1 satisfied = True; device run 2 = ibm_kingston, run 3 = ibm_kingston; M2 inputs changed: 4 of 8; max |dF_pred| = 0.0592 (threshold 0.02); Q1 model test = True
- dF_pred (run 3 - run 2) per n: n=4: +0.0059, n=8: -0.0592, n=16: -0.0422, n=24: -0.0240, n=32: -0.0250, n=48: +0.0173
- recomputed in the analysis: C-1 satisfied = True
- rule-14 check (F_pred + 0.05 < 1 at n = 4, 8): ok = True

## Log (run/dryrun_log.jsonl, the whole log) and the stopping rule

2 lines: 0 dry runs, 1 attempts (0 refused, 0 failed, 1 accepted), 0 not-attempts; unparsable lines: 0.
Log prefix recorded in job.json unchanged: True; lines after the anchor: 2; the accepted line's predictions hash matches the snapshot's: True.
Post-anchor lines dated not before the submission: True; first logged fetch: execution_calibration_20261116T112310Z.json (file and hash ok: True; 1 logged); job created 2026-11-16T11:18:09.725074+00:00, started 2026-11-16T11:18:15.910351+00:00 (after the submission: True).
Deviations from the stopping rule: none
Environment (power file / now): identical

| utc | snapshot utc | mode | attempt | backend | exit | reason | D-7 | K2 | C-1 | C-2 | quota | predictions sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20261116T111804Z | 20261116T111730Z | submit-checks-passed | True | ibm_kingston | 0 |  | True | True | True | True | 234.0 | 50c96f288461 |
| 20261116T111809Z | 20261116T111730Z | submit-accepted | True | ibm_kingston | 0 |  | True | True | True | True | 234.0 | 50c96f288461 |
| 20261116T112314Z | None | fetch | False | ibm_kingston | 0 |  |  |  |  |  | None |  |

## Controls

| MIX n | P | C_mix (95% CI) | F_mix (95% CI, reported only) | K1 (C_mix CI high <= 0.05) |
|---|---|---|---|---|
| 8 | 0.8205 | 0.0125 [0.0028, 0.0291] | 0.4165 [0.4072, 0.4279] | pass |
| 32 | 0.3550 | 0.0022 [0.0009, 0.0110] | 0.1786 [0.1692, 0.1911] | pass |

- K1 (coherence detector): pass
- K2: pass = design check (certs/k2_sim.json, FakeKingston circuits; a missing or unreadable file fails): pass; binding (noiseless MPS on the submitted circuits): pass; bit-order control (reported, uninformative, not part of K2): true
- K3 (integrity): pass {"snapshot_hash_matches_file": true, "snapshot_hash_matches_job": true, "job_id_saved": true, "circuits_match_manifest": true, "two_qubit_count_n_minus_1_all": true, "count_totals_equal_shots": true, "core_and_study_sha256_equal_run2_frozen": true, "m2_recomputed_equals_saved_model": true, "c1_recomputed_holds": true, "run2_hashes_in_calibration_check_equal_known": true, "power_run3_exists_and_hash_matches_job": true, "power_run3_input_hashes_match_frozen": true, "power_run3_recomputation_equal": true, "log_prefix_recorded_in_job_unchanged": true, "log_post_anchor_lines_not_before_submission": true, "first_logged_fetch_file_exists_and_hash_matches": true, "job_created_and_started_after_submission": true}
