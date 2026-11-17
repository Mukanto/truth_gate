# RESULTS

| id | set | faulty | fixed | pb_det | attrib | generic | declared | qualifying streams | exclusions |
|---|---|---|---|---|---|---|---|---|---|
| P01 | acceptance | UNDEFINED | FALSIFIABLE | - | - | - | - | - | faulty_load_error |
| P02 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| P03 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | Y | - | Y | control:permute_y (K4_CONTROL_ALSO_HOLDS, 17/200 vs 1/200, p=5.285e-05) | - |
| P04 | acceptance | NOT_FALSIFIABLE | UNDEFINED | Y | - | - | - | - | fixed_hard_undefined:world:minus |
| P05 | acceptance | NOT_FALSIFIABLE | FALSIFIABLE | Y | Y | - | Y | world:minus (K2_HIGH_SIZE, 60/200 vs 6/200, p=1.83e-14) | - |
| P06 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| P07 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | Y | - | Y | probe:shuffle:x,y (K5_HOLDS_ON_SHUFFLE, 17/200 vs 1/200, p=5.285e-05) | - |
| P08 | acceptance | NOT_FALSIFIABLE | FALSIFIABLE | Y | - | - | - | - | - |
| P09 | acceptance | NOT_FALSIFIABLE | UNDEFINED | Y | - | - | - | - | fixed_load_error |
| P10 | acceptance | NOT_FALSIFIABLE | WEAK | Y | Y | Y | - | probe:noise (K5_HOLDS_ON_NOISE, 17/200 vs 1/200, p=5.285e-05) | - |
| P11 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| P12 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| P13 | acceptance | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| B2-01 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | control:permute_onset_across_country_years (HIGH_RATE:control:permute_onset_across_country_years, 47/200 vs 0/200, p=3.309e-16); control:permute_onset_histories_across_countries (HIGH_RATE:control:permute_onset_histories_across_countries, 186/200 vs 6/200, p=1.303e-87); world:minus (K2_HIGH_SIZE, 178/200 vs 5/200, p=1.177e-80) | - |
| B2-02 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | control:permute_outcome (HIGH_RATE:control:permute_outcome, 29/200 vs 1/200, p=1.038e-08); world:minus (K2_HIGH_SIZE, 25/200 vs 0/200, p=1.34e-08) | - |
| B2-03 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B2-04 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B2-05 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B2-06 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B2-07 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B2-08 | pc | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| B2-09 | pc | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| B2-10 | pc | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| B2-11 | pc | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |
| B2-12 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | control:permute_tumour_labels (HIGH_RATE:control:permute_tumour_labels, 173/200 vs 6/200, p=1.429e-74); probe:noise (HIGH_RATE:probe:noise, 188/200 vs 6/200, p=5.862e-90); probe:shuffle:expression,tumour (HIGH_RATE:probe:shuffle:expression,tumour, 166/200 vs 5/200, p=4.944e-70); world:minus (K2_HIGH_SIZE, 165/200 vs 5/200, p=3.154e-69); probe:noise (K5_HOLDS_ON_NOISE, 188/200 vs 6/200, p=5.862e-90) | - |
| B3-01 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | world:minus (K2_HIGH_SIZE, 33/200 vs 13/200, p=0.001292) | - |
| B3-02 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B3-03 | pc | WEAK | WEAK | - | - | - | - | - | - |
| B3-04 | pc | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | Y | Y | - | probe:noise (HIGH_RATE:probe:noise, 65/200 vs 0/200, p=5.293e-23) | - |
| B3-05 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | Y | - | probe:noise (HIGH_RATE:probe:noise, 67/200 vs 0/200, p=8.558e-24) | - |
| B3-06 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | control:decouple_observers_within_true_value_blocks (HIGH_RATE:control:decouple_observers_within_true_value_blocks, 62/200 vs 0/200, p=7.879e-22); probe:noise (HIGH_RATE:probe:noise, 38/200 vs 0/200, p=5.213e-13); world:minus (K2_HIGH_SIZE, 61/200 vs 0/200, p=1.922e-21) | - |
| B3-08 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | control:permute_second_baseline_across_patients (HIGH_RATE:control:permute_second_baseline_across_patients, 200/200 vs 0/200, p=9.713e-120); probe:noise (HIGH_RATE:probe:noise, 200/200 vs 0/200, p=9.713e-120); world:minus (K2_HIGH_SIZE, 72/200 vs 0/200, p=8.308e-26); control:permute_second_baseline_across_patients (K4_CONTROL_ALSO_HOLDS, 200/200 vs 0/200, p=9.713e-120); probe:noise (K5_HOLDS_ON_NOISE, 200/200 vs 0/200, p=9.713e-120) | - |
| B3-09 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | control:permute_uptake_across_patients (HIGH_RATE:control:permute_uptake_across_patients, 200/200 vs 3/200, p=1.334e-113); probe:noise (HIGH_RATE:probe:noise, 199/200 vs 2/200, p=3.885e-113); world:minus (K2_HIGH_SIZE, 34/200 vs 4/200, p=9.002e-08); control:permute_uptake_across_patients (K4_CONTROL_ALSO_HOLDS, 200/200 vs 3/200, p=1.334e-113); probe:noise (K5_HOLDS_ON_NOISE, 199/200 vs 2/200, p=3.885e-113) | - |
| B3-11 | pc | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | control:permute_gene_a_across_samples (HIGH_RATE:control:permute_gene_a_across_samples, 200/200 vs 0/200, p=9.713e-120); probe:noise (HIGH_RATE:probe:noise, 155/200 vs 9/200, p=1.059e-56); world:minus (K2_FAILS_UNREACHABLE, 200/200 vs 0/200, p=9.713e-120); world:minus (K2_HIGH_SIZE, 200/200 vs 0/200, p=9.713e-120); control:permute_gene_a_across_samples (K4_CONTROL_ALSO_HOLDS, 200/200 vs 0/200, p=9.713e-120) | - |
| B3-12 | pc | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | - | - | - | - | - |

(sensitivity, expected flag need not be present in faulty) acceptance: attributable=4 generic=1 declared=3
(sensitivity, expected flag need not be present in faulty) pc: attributable=10 generic=7 declared=8

acceptance: n=13 pb_detected=12 attributable=4 generic=1 declared=3
pc: n=22 pb_detected=15 attributable=10 generic=7 declared=8
