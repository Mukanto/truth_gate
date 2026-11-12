# GHZ run 2 on ibm_kingston: results

Job `dbqg2dgk09pc73at7d9g`, submitted 20261111T235843Z, snapshot sha256 `104fb995b806e2aa`, bootstrap B=2000 seed=20261113.

**Interpretable: yes**  
**Headline: n_meas = 24** (largest n with F_hat > 0.5, the H2 definition; 0 = none); n_pred = 24. 95% CI at n_meas excludes 0.5: False (reported, not used by H2). Largest n with CI_low(F) > 0.5: 16.

| n | P (95% CI) | P_pred | C (95% CI) | C_pred | F (95% CI) | F_pred | R = F/F_pred | F_M (ref.) |
|---|---|---|---|---|---|---|---|---|
| 4 | 0.9290 [0.9170, 0.9400] | 0.9548 | 0.8545 [0.8411, 0.8680] | 0.9183 | 0.8917 [0.8832, 0.9005] | 0.9366 | 0.952 | 0.9539 |
| 8 | 0.8645 [0.8500, 0.8800] | 0.9194 | 0.8016 [0.7911, 0.8120] | 0.8564 | 0.8331 [0.8241, 0.8420] | 0.8879 | 0.938 | 0.9174 |
| 16 | 0.6835 [0.6640, 0.7045] | 0.7777 | 0.5422 [0.5329, 0.5518] | 0.6161 | 0.6129 [0.6020, 0.6244] | 0.6969 | 0.879 | 0.7677 |
| 24 | 0.5880 [0.5665, 0.6090] | 0.6890 | 0.4307 [0.4227, 0.4388] | 0.4898 | 0.5093 [0.4981, 0.5201] | 0.5894 | 0.864 | 0.6739 |
| 32 | 0.4670 [0.4455, 0.4885] | 0.5613 | 0.3009 [0.2934, 0.3084] | 0.3416 | 0.3840 [0.3724, 0.3957] | 0.4514 | 0.851 | 0.5359 |
| 48 | 0.3305 [0.3100, 0.3510] | 0.3965 | 0.1551 [0.1491, 0.1614] | 0.1787 | 0.2428 [0.2321, 0.2533] | 0.2876 | 0.844 | 0.3604 |

Sensitivity I-1: C with Re (nominal phase) instead of |.|

| n | C (abs) | C_re (95% CI) |
|---|---|---|
| 4 | 0.8545 | 0.8532 [0.8400, 0.8667] |
| 8 | 0.8016 | 0.7983 [0.7876, 0.8088] |
| 16 | 0.5422 | 0.5362 [0.5268, 0.5457] |
| 24 | 0.4307 | 0.4239 [0.4161, 0.4319] |
| 32 | 0.3009 | 0.2969 [0.2896, 0.3041] |
| 48 | 0.1551 | 0.1443 [0.1383, 0.1503] |

## Criteria (imported unchanged from ghz2_study.py)

| id | verdict |
|---|---|
| H1_small_n_accuracy | FAILS |
| H2_gme_reach_matches | HOLDS |
| H3_population_specific | FAILS |

## Controls

| MIX n | P | C_mix (95% CI) | F_mix (95% CI, reported only) | K1 (C_mix CI high <= 0.05) |
|---|---|---|---|---|
| 8 | 0.8645 | 0.0136 [0.0036, 0.0292] | 0.4391 [0.4298, 0.4500] | pass |
| 32 | 0.4745 | 0.0092 [0.0033, 0.0174] | 0.2418 [0.2308, 0.2539] | pass |

- K1 (coherence detector): pass
- K2 (estimator fidelity + bit-order control, simulator pre-run): pass
- K3 (integrity): pass {"snapshot_hash_matches_file": true, "snapshot_hash_matches_job": true, "job_id_saved": true, "circuits_match_manifest": true, "two_qubit_count_n_minus_1_all": true, "count_totals_equal_shots": true, "m2_recomputed_equals_saved_model": true}
