# RECOMPUTE_D (designer, independent)

Script sha256: `b6069d9af9bad0a64f791ac7770aca37ddeaf1e7ae169fd43ac96d0d1d91b27b`

Counts with one-sided 95% Wilson lower bound in brackets. n = pairs.

## Arm R

| group | n | pb-det | attributable | generic | declared | clean | clean w/o noise | noise-only | declared-only | flag-everything det |
|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 10 (0.787) | 10 (0.787) | 6 (0.352) | 10 (0.787) | 10 (0.787) | 10 (0.787) | 6 (0.352) | 10 (0.787) | 10 (0.787) |
| B-3 | 7 | 7 (0.721) | 7 (0.721) | 5 (0.409) | 7 (0.721) | 7 (0.721) | 7 (0.721) | 5 (0.409) | 7 (0.721) | 7 (0.721) |
| B-1 | 1 | 1 (0.270) | 1 (0.270) | 0 (0.000) | 1 (0.270) | 1 (0.270) | 1 (0.270) | 0 (0.000) | 1 (0.270) | 1 (0.270) |
| B-6 | 2 | 2 (0.425) | 2 (0.425) | 0 (0.000) | 2 (0.425) | 2 (0.425) | 2 (0.425) | 0 (0.000) | 2 (0.425) | 2 (0.425) |
| decoys(B-1+B-6) | 3 | 3 (0.526) | 3 (0.526) | 0 (0.000) | 3 (0.526) | 3 (0.526) | 3 (0.526) | 0 (0.000) | 3 (0.526) | 3 (0.526) |
| B-2+B-3 | 17 | 17 (0.863) | 17 (0.863) | 11 (0.449) | 17 (0.863) | 17 (0.863) | 17 (0.863) | 11 (0.449) | 17 (0.863) | 17 (0.863) |

## Arm W0

| group | n | pb-det | attributable | generic | declared | clean | clean w/o noise | noise-only | declared-only | flag-everything det |
|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 9 (0.652) | 9 (0.652) | 6 (0.352) | 9 (0.652) | 9 (0.652) | 9 (0.652) | 6 (0.352) | 9 (0.652) | 10 (0.787) |
| B-3 | 7 | 6 (0.548) | 6 (0.548) | 5 (0.409) | 5 (0.409) | 7 (0.721) | 7 (0.721) | 5 (0.409) | 5 (0.409) | 7 (0.721) |
| B-1 | 1 | 0 (0.000) | 0 (0.000) | 0 (0.000) | 0 (0.000) | 1 (0.270) | 1 (0.270) | 0 (0.000) | 0 (0.000) | 1 (0.270) |
| B-6 | 2 | 2 (0.425) | 1 (0.121) | 0 (0.000) | 1 (0.121) | 2 (0.425) | 2 (0.425) | 1 (0.121) | 2 (0.425) | 2 (0.425) |
| decoys(B-1+B-6) | 3 | 2 (0.254) | 1 (0.078) | 0 (0.000) | 1 (0.078) | 3 (0.526) | 3 (0.526) | 1 (0.078) | 2 (0.254) | 3 (0.526) |
| B-2+B-3 | 17 | 15 (0.699) | 15 (0.699) | 11 (0.449) | 14 (0.631) | 16 (0.774) | 16 (0.774) | 11 (0.449) | 14 (0.631) | 17 (0.863) |

## Arm W1

| group | n | pb-det | attributable | generic | declared | clean | clean w/o noise | noise-only | declared-only | flag-everything det |
|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 9 (0.652) | 9 (0.652) | 6 (0.352) | 9 (0.652) | 10 (0.787) | 10 (0.787) | 6 (0.352) | 9 (0.652) | 10 (0.787) |
| B-3 | 7 | 6 (0.548) | 6 (0.548) | 5 (0.409) | 5 (0.409) | 7 (0.721) | 7 (0.721) | 5 (0.409) | 5 (0.409) | 7 (0.721) |
| B-1 | 1 | 1 (0.270) | 1 (0.270) | 0 (0.000) | 1 (0.270) | 1 (0.270) | 1 (0.270) | 0 (0.000) | 1 (0.270) | 1 (0.270) |
| B-6 | 2 | 2 (0.425) | 1 (0.121) | 0 (0.000) | 1 (0.121) | 2 (0.425) | 2 (0.425) | 1 (0.121) | 2 (0.425) | 2 (0.425) |
| decoys(B-1+B-6) | 3 | 3 (0.526) | 2 (0.254) | 0 (0.000) | 2 (0.254) | 3 (0.526) | 3 (0.526) | 1 (0.078) | 3 (0.526) | 3 (0.526) |
| B-2+B-3 | 17 | 15 (0.699) | 15 (0.699) | 11 (0.449) | 14 (0.631) | 17 (0.863) | 17 (0.863) | 11 (0.449) | 14 (0.631) | 17 (0.863) |

## H-D1 / H-D2 (arm W1)

- H-D1 (B-2): n=10, attributable 9 (0.652), clean 10 (0.787) -> **insufficient cases**
- H-D2 (B-3): n=7, attributable 6 (0.548), clean 7 (0.721) -> **insufficient cases**

## H-D3 (B-2+B-3, declared attributable, W1 vs W0)

- pool 17, comparable 17; b (W1 only) = 0, c (W0 only) = 0, both = 14, neither = 3; p = 1.000000 (1/1) -> **not demonstrated**
- per class: B-2 b=0 c=0 (n=10); B-3 b=0 c=0 (n=7)
- exclusions: none
- sensitivity: b=0 c=0 p=1.000000 -> not demonstrated

## Clean-pass guard (W0 better than W1; decoys excluded)

- n=17; b (W0 clean, W1 not) = 0; c (W1 clean, W0 not) = 1; p = 1.000000 (1/1); significant: False
- pooled W1 minus W0 clean pass: 1; decoys clean pass W0 3, W1 3

## Per pair

| id | class | arm | faulty | fixed | pb-det | attrib | generic | declared | clean | clean w/o noise | qualifying streams | attrition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-007 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-007 (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 3/200, p=1.33e-113); world:minus (200/200 vs 3/200, p=1.33e-113); control:D-007 (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-007 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:survival_permuted_across_patients (200/200 vs 3/200, p=1.33e-113); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:expression,survival_months (200/200 vs 3/200, p=1.33e-113); world:minus (200/200 vs 2/200, p=1.97e-115); world:minus (200/200 vs 2/200, p=1.97e-115); control:survival_permuted_across_patients (200/200 vs 3/200, p=1.33e-113); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:expression,survival_months (200/200 vs 3/200, p=1.33e-113) | - |
| D-007 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:survival_shuffled_across_patients (200/200 vs 1/200, p=1.95e-117); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 2/200, p=1.97e-115); world:minus (200/200 vs 2/200, p=1.97e-115); control:survival_shuffled_across_patients (200/200 vs 1/200, p=1.95e-117); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-008 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:permute_vo2_across_patients (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (96/200 vs 0/200, p=3.06e-36); control:permute_vo2_across_patients (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-008 | B-3 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:vo2_permuted_across_occasions_within_patient (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:cardiac_output,vo2_expired_gas (200/200 vs 0/200, p=9.71e-120); world:minus (25/200 vs 0/200, p=1.34e-08); control:vo2_permuted_across_occasions_within_patient (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:cardiac_output,vo2_expired_gas (200/200 vs 0/200, p=9.71e-120) | - |
| D-008 | B-3 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:consumption_shuffled_across_occasions_within_patient (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (18/200 vs 0/200, p=2.56e-06); control:consumption_shuffled_across_occasions_within_patient (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-010 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-010 (200/200 vs 0/200, p=9.71e-120); probe:noise (112/200 vs 0/200, p=4.78e-44); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:D-010 (200/200 vs 0/200, p=9.71e-120) | - |
| D-010 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:y_permuted_across_patients (200/200 vs 0/200, p=9.71e-120); probe:noise (112/200 vs 0/200, p=4.78e-44); probe:shuffle:covariates,y (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:y_permuted_across_patients (200/200 vs 0/200, p=9.71e-120); probe:shuffle:covariates,y (200/200 vs 0/200, p=9.71e-120) | - |
| D-010 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:y_shuffled_across_patients (200/200 vs 0/200, p=9.71e-120); probe:noise (112/200 vs 0/200, p=4.78e-44); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:y_shuffled_across_patients (200/200 vs 0/200, p=9.71e-120) | - |
| D-011 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-011 (85/200 vs 0/200, p=2.74e-31); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (88/200 vs 0/200, p=1.31e-32); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-011 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:labels_permuted_across_samples (144/200 vs 0/200, p=1.49e-62); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:expression,myeloid (149/200 vs 0/200, p=6.44e-66); world:minus (157/200 vs 0/200, p=1.18e-71); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-011 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:myeloid_labels_shuffled_across_samples (123/200 vs 0/200, p=6.55e-50); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (120/200 vs 0/200, p=2.89e-48); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-012 | B-6 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:D-012 (60/200 vs 2/200, p=3.12e-18); world:minus (57/200 vs 14/200, p=8.26e-09) | - |
| D-012 | B-6 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | world:minus (19/200 vs 4/200, p=0.000977) | - |
| D-012 | B-6 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:exclosure_shuffled_across_plots (50/200 vs 10/200, p=7.95e-09); world:minus (53/200 vs 11/200, p=3.77e-09) | - |
| D-022 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-022 (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:D-022 (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120) | - |
| D-022 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:y_permuted_across_runs (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:X,y (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:y_permuted_across_runs (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:X,y (200/200 vs 0/200, p=9.71e-120) | - |
| D-022 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:y_circularly_shifted_against_X_by_30_to_270_runs (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:X,y (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 3/200, p=1.33e-113); world:minus (200/200 vs 3/200, p=1.33e-113); control:y_circularly_shifted_against_X_by_30_to_270_runs (200/200 vs 0/200, p=9.71e-120); probe:noise (200/200 vs 0/200, p=9.71e-120); probe:shuffle:X,y (200/200 vs 0/200, p=9.71e-120) | - |
| D-023 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-023 (200/200 vs 0/200, p=9.71e-120); probe:noise (66/200 vs 0/200, p=2.13e-23); world:minus (197/200 vs 0/200, p=1.33e-113); control:D-023 (200/200 vs 0/200, p=9.71e-120) | - |
| D-023 | B-3 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | - | Y | Y | probe:noise (66/200 vs 0/200, p=2.13e-23) | - |
| D-023 | B-3 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | - | Y | Y | probe:noise (66/200 vs 0/200, p=2.13e-23) | - |
| D-027 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-027 (198/200 vs 0/200, p=1.97e-115); probe:noise (196/200 vs 0/200, p=6.8e-112); world:minus (197/200 vs 0/200, p=1.33e-113); control:D-027 (198/200 vs 0/200, p=1.97e-115); probe:noise (196/200 vs 0/200, p=6.8e-112) | - |
| D-027 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:y_permuted_across_samples (198/200 vs 0/200, p=1.97e-115); probe:noise (196/200 vs 0/200, p=6.8e-112); probe:shuffle:X,y (196/200 vs 0/200, p=6.8e-112); world:minus (199/200 vs 0/200, p=1.95e-117); control:y_permuted_across_samples (198/200 vs 0/200, p=1.97e-115); probe:noise (196/200 vs 0/200, p=6.8e-112); probe:shuffle:X,y (196/200 vs 0/200, p=6.8e-112) | - |
| D-027 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:y_shuffled_across_samples (199/200 vs 0/200, p=1.95e-117); probe:noise (196/200 vs 0/200, p=6.8e-112); world:minus (198/200 vs 0/200, p=1.97e-115); control:y_shuffled_across_samples (199/200 vs 0/200, p=1.95e-117); probe:noise (196/200 vs 0/200, p=6.8e-112) | - |
| D-035 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:D-035 (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:D-035 (200/200 vs 0/200, p=9.71e-120) | - |
| D-035 | B-2 | W0 | NOT_FALSIFIABLE | NOT_FALSIFIABLE | Y | Y | - | Y | - | - | world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120) | - |
| D-035 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:positive_labels_shuffled_across_records (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:positive_labels_shuffled_across_records (200/200 vs 0/200, p=9.71e-120) | - |
| D-040 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:permute_height_within_length (200/200 vs 1/200, p=1.95e-117); probe:noise (87/200 vs 0/200, p=3.63e-32); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:permute_height_within_length (200/200 vs 1/200, p=1.95e-117) | - |
| D-040 | B-3 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:height_permuted_within_length_blocks (195/200 vs 0/200, p=2.79e-110); probe:noise (87/200 vs 0/200, p=3.63e-32); probe:shuffle:breadth,height (200/200 vs 0/200, p=9.71e-120); world:minus (192/200 vs 0/200, p=7.36e-106); control:height_permuted_within_length_blocks (195/200 vs 0/200, p=2.79e-110); probe:shuffle:breadth,height (200/200 vs 0/200, p=9.71e-120) | - |
| D-040 | B-3 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:height_shuffled_within_blocks_of_10_similar_lengths (124/200 vs 1/200, p=1.65e-48); probe:noise (87/200 vs 0/200, p=3.63e-32); world:minus (74/200 vs 0/200, p=1.26e-26) | - |
| D-042 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | world:minus (128/200 vs 0/200, p=9.88e-53) | - |
| D-042 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:compound_activity_permuted_across_compounds (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:compound_activity_permuted_across_compounds (200/200 vs 0/200, p=9.71e-120) | - |
| D-042 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:compound_mean_activity_shuffled_across_compounds (141/200 vs 0/200, p=1.31e-60); world:minus (95/200 vs 0/200, p=8.9e-36) | - |
| D-047 | B-1 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:D-047 (136/200 vs 0/200, p=1.77e-57); world:minus (148/200 vs 0/200, p=3.12e-65) | - |
| D-047 | B-1 | W0 | WEAK | WEAK | - | - | - | - | Y | Y | - | - |
| D-047 | B-1 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:entry_and_week12_swapped_at_random_within_patient (135/200 vs 0/200, p=7.2e-57) | - |
| D-052 | B-6 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:D-052 (49/200 vs 6/200, p=6.54e-11); world:minus (95/200 vs 13/200, p=7.15e-22) | - |
| D-052 | B-6 | W0 | NOT_FALSIFIABLE | WEAK | Y | - | - | - | Y | Y | - | - |
| D-052 | B-6 | W1 | NOT_FALSIFIABLE | WEAK | Y | - | - | - | Y | Y | - | - |
| D-055 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:D-055 (65/200 vs 2/200, p=4.25e-20); world:minus (45/200 vs 3/200, p=5.63e-12) | - |
| D-055 | B-2 | W0 | WEAK | WEAK | - | - | - | - | Y | Y | - | - |
| D-055 | B-2 | W1 | WEAK | WEAK | - | - | - | - | Y | Y | - | - |
| D-056 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | world:minus (53/200 vs 10/200, p=1.13e-09) | - |
| D-056 | B-3 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | world:minus (22/200 vs 6/200, p=0.00133) | - |
| D-056 | B-3 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | world:minus (47/200 vs 10/200, p=5.26e-08) | - |
| D-062 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:permute_humerus_within_species (176/200 vs 1/200, p=1.76e-85); world:minus (149/200 vs 0/200, p=6.44e-66) | - |
| D-062 | B-3 | W0 | WEAK | WEAK | - | - | - | - | Y | Y | - | - |
| D-062 | B-3 | W1 | WEAK | WEAK | - | - | - | - | Y | Y | - | - |
| D-064 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-064 (200/200 vs 2/200, p=1.97e-115); probe:noise (200/200 vs 1/200, p=1.95e-117); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:D-064 (200/200 vs 2/200, p=1.97e-115); probe:noise (200/200 vs 1/200, p=1.95e-117) | - |
| D-064 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:response_permuted_across_patients (200/200 vs 3/200, p=1.33e-113); probe:noise (200/200 vs 1/200, p=1.95e-117); world:minus (200/200 vs 1/200, p=1.95e-117); world:minus (200/200 vs 1/200, p=1.95e-117); control:response_permuted_across_patients (200/200 vs 3/200, p=1.33e-113); probe:noise (200/200 vs 1/200, p=1.95e-117) | - |
| D-064 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:response_permuted_across_patients (200/200 vs 2/200, p=1.97e-115); probe:noise (200/200 vs 1/200, p=1.95e-117); probe:shuffle:expression,response (200/200 vs 2/200, p=1.97e-115); world:minus (200/200 vs 4/200, p=6.8e-112); world:minus (200/200 vs 4/200, p=6.8e-112); control:response_permuted_across_patients (200/200 vs 2/200, p=1.97e-115); probe:noise (200/200 vs 1/200, p=1.95e-117); probe:shuffle:expression,response (200/200 vs 2/200, p=1.97e-115) | - |
| D-066 | B-2 | R | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:D-066 (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:D-066 (200/200 vs 0/200, p=9.71e-120) | - |
| D-066 | B-2 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:outcome_permuted_across_patients (200/200 vs 0/200, p=9.71e-120); probe:shuffle:y,X (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:outcome_permuted_across_patients (200/200 vs 0/200, p=9.71e-120); probe:shuffle:y,X (200/200 vs 0/200, p=9.71e-120) | - |
| D-066 | B-2 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | - | Y | Y | Y | control:outcome_permuted_across_patients (200/200 vs 0/200, p=9.71e-120); probe:shuffle:X,y (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:outcome_permuted_across_patients (200/200 vs 0/200, p=9.71e-120); probe:shuffle:X,y (200/200 vs 0/200, p=9.71e-120) | - |
| D-067 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:permute_heart_within_mass (123/200 vs 5/200, p=3.41e-42); probe:noise (64/200 vs 8/200, p=2.55e-14); world:minus (121/200 vs 6/200, p=5.78e-40) | - |
| D-067 | B-3 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:heart_exchanged_among_mass_matched_rats (200/200 vs 6/200, p=9.58e-109); control:heart_permuted_across_rats (200/200 vs 2/200, p=1.97e-115); probe:noise (64/200 vs 8/200, p=2.55e-14); probe:shuffle:kidney_weight,heart_weight (200/200 vs 1/200, p=1.95e-117); world:minus (200/200 vs 15/200, p=4.37e-97); world:minus (200/200 vs 15/200, p=4.37e-97); control:heart_exchanged_among_mass_matched_rats (200/200 vs 6/200, p=9.58e-109); control:heart_permuted_across_rats (200/200 vs 2/200, p=1.97e-115); probe:shuffle:kidney_weight,heart_weight (200/200 vs 1/200, p=1.95e-117) | - |
| D-067 | B-3 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:heart_permuted_across_rats (33/200 vs 3/200, p=3.42e-08); probe:noise (64/200 vs 8/200, p=2.55e-14); probe:shuffle:kidney_weight,heart_weight (20/200 vs 2/200, p=4.03e-05) | - |
| D-068 | B-3 | R | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:D-068 (200/200 vs 3/200, p=1.33e-113); probe:noise (20/200 vs 0/200, p=5.79e-07); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:D-068 (200/200 vs 3/200, p=1.33e-113) | - |
| D-068 | B-3 | W0 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:head_width_exchanged_among_length_matched_specimens (175/200 vs 0/200, p=1e-86); control:head_width_permuted_within_population (197/200 vs 0/200, p=1.33e-113); probe:noise (20/200 vs 0/200, p=5.79e-07); world:minus (200/200 vs 0/200, p=9.71e-120); world:minus (200/200 vs 0/200, p=9.71e-120); control:head_width_permuted_within_population (197/200 vs 0/200, p=1.33e-113) | - |
| D-068 | B-3 | W1 | NOT_FALSIFIABLE | WEAK | Y | Y | Y | Y | Y | Y | control:head_permuted_within_population (124/200 vs 0/200, p=1.82e-50); control:head_swapped_between_body_length_neighbours (121/200 vs 0/200, p=8.25e-49); probe:noise (20/200 vs 0/200, p=5.79e-07); world:minus (125/200 vs 1/200, p=4.61e-49) | - |

Integrity: runlog verdict mismatches 0; certificate sha mismatches 0; part-B no: none

