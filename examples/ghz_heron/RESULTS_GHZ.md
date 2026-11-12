# GHZ fidelity on ibm_kingston: results

Job `dbqfmhmjjaos73ah82u0`, submitted 20261111T233323Z, snapshot sha256 `0624e0a146a4a625`, bootstrap B=2000 seed=20261112.

**Interpretable: yes**  
**Headline: n_meas = 16** (largest n with CI_low(F) > 0.5; 0 = none); n_pred = 32.

| n | F_meas | 95% CI | F_pred | R = F_meas/F_pred | P | C |
|---|---|---|---|---|---|---|
| 4 | 0.9149 | [0.9065, 0.9231] | 0.9539 | 0.959 | 0.9380 | 0.8918 |
| 8 | 0.8549 | [0.8459, 0.8639] | 0.9174 | 0.932 | 0.8795 | 0.8303 |
| 16 | 0.6092 | [0.5984, 0.6200] | 0.7677 | 0.794 | 0.6930 | 0.5255 |
| 32 | 0.3874 | [0.3764, 0.3995] | 0.5359 | 0.723 | 0.4740 | 0.3008 |
| 48 | 0.2457 | [0.2351, 0.2565] | 0.3604 | 0.682 | 0.3285 | 0.1630 |

## Criteria (imported unchanged from ghz_study.py)

| id | verdict |
|---|---|
| G1_small_n_accuracy | HOLDS |
| G2_excess_decay_grows | HOLDS |
| G3_gme_reach_matches | FAILS |

## Controls

| MIX n | P | C_mix (95% CI) | F_mix (95% CI, reported only) | K1 (C_mix CI high <= 0.05) |
|---|---|---|---|---|
| 8 | 0.9075 | 0.0110 [0.0029, 0.0276] | 0.4592 [0.4519, 0.4698] | pass |
| 32 | 0.4705 | 0.0008 [0.0009, 0.0108] | 0.2356 [0.2271, 0.2488] | pass |

- K1 (coherence detector): pass
- K2 (estimator fidelity, simulator pre-run): pass
- K3 (integrity): pass {"snapshot_hash_matches_file": true, "snapshot_hash_matches_job": true, "job_id_saved": true, "circuits_match_manifest": true, "two_qubit_count_n_minus_1_all": true, "count_totals_equal_shots": true}
- model recomputed from the snapshot equals run/model.json: True
