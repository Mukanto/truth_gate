# Phase D results

Scoring script `score_phase_d.py` (SHA-256 96a687c4a9ce6f87eee2d41764a2af4022ff74f1aec5726a1a3229711172b0e0); run folder `E:\Claude Projects\Kapi\phase_d_work\run`; 20 pairs x arms R, W0, W1; run-log result rows 120 (infrastructure failures 0).

## Per arm and class

### Arm R

| class | n | attributable | generic | declared | both | PB-style | draft-1 | clean | clean w/o noise | noise-only | declared-only | flag-everything | attr. lower | clean lower |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 10 | 6 | 10 | 6 | 10 | 10 | 10 | 10 | 6 | 10 | 10 | 0.7871 | 0.7871 |
| B-3 | 7 | 7 | 5 | 7 | 5 | 7 | 7 | 7 | 7 | 5 | 7 | 7 | 0.7212 | 0.7212 |
| B-1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0.2699 | 0.2699 |
| B-6 | 2 | 2 | 0 | 2 | 0 | 2 | 2 | 2 | 2 | 0 | 2 | 2 | 0.4250 | 0.4250 |
| decoys (B-1 + B-6) | 3 | 3 | 0 | 3 | 0 | 3 | 3 | 3 | 3 | 0 | 3 | 3 | 0.5258 | 0.5258 |

Attrition by cause:

none

### Arm W0

| class | n | attributable | generic | declared | both | PB-style | draft-1 | clean | clean w/o noise | noise-only | declared-only | flag-everything | attr. lower | clean lower |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 9 | 6 | 9 | 6 | 9 | 9 | 9 | 9 | 6 | 9 | 10 | 0.6523 | 0.6523 |
| B-3 | 7 | 6 | 5 | 5 | 4 | 6 | 5 | 7 | 7 | 5 | 5 | 7 | 0.5477 | 0.7212 |
| B-1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 0.0000 | 0.2699 |
| B-6 | 2 | 1 | 0 | 1 | 0 | 2 | 0 | 2 | 2 | 1 | 2 | 2 | 0.1209 | 0.4250 |
| decoys (B-1 + B-6) | 3 | 1 | 0 | 1 | 0 | 2 | 0 | 3 | 3 | 1 | 2 | 3 | 0.0783 | 0.5258 |

Attrition by cause:

none

### Arm W1

| class | n | attributable | generic | declared | both | PB-style | draft-1 | clean | clean w/o noise | noise-only | declared-only | flag-everything | attr. lower | clean lower |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 9 | 6 | 9 | 6 | 9 | 9 | 10 | 10 | 6 | 9 | 10 | 0.6523 | 0.7871 |
| B-3 | 7 | 6 | 5 | 5 | 4 | 6 | 6 | 7 | 7 | 5 | 5 | 7 | 0.5477 | 0.7212 |
| B-1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0.2699 | 0.2699 |
| B-6 | 2 | 1 | 0 | 1 | 0 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 0.1209 | 0.4250 |
| decoys (B-1 + B-6) | 3 | 2 | 0 | 2 | 0 | 3 | 2 | 3 | 3 | 1 | 3 | 3 | 0.2535 | 0.5258 |

Attrition by cause:

none

## H-D1 and H-D2 (arm W1)

| hypothesis | class | n | k_detect | k_clean | detect lower | clean lower | verdict |
|---|---|---|---|---|---|---|---|
| H-D1 | B-2 | 10 | 9 | 10 | 0.6523 | 0.7871 | insufficient cases |
| H-D2 | B-3 | 7 | 6 | 7 | 0.5477 | 0.7212 | insufficient cases |

## H-D3 (B-2 + B-3 pooled; declared attributable detection, W1 against W0)

Pooled pairs: 17.

Not comparable (by arm and cause):

none

| analysis | n | W1 declared | W0 declared | b (W1 only) | c (W0 only) | both | neither | p | label |
|---|---|---|---|---|---|---|---|---|---|
| comparable pairs | 17 | 14 | 14 | 0 | 0 | 14 | 3 | 1.0000 | not demonstrated |
| sensitivity (not comparable counted as non-detections) | 17 | 14 | 14 | 0 | 0 | 14 | 3 | 1.0000 | not demonstrated |

Discordant counts per class (descriptive):

| analysis | class | b (W1 only) | c (W0 only) |
|---|---|---|---|
| comparable | B-2 | 0 | 0 |
| comparable | B-3 | 0 | 0 |
| sensitivity | B-2 | 0 | 0 |
| sensitivity | B-3 | 0 | 0 |

## Clean-pass guard (W0 better than W1; H-D3 pairs; decoys excluded)

| pairs | W0 clean | W1 clean | W0 clean only | W1 clean only | p |
|---|---|---|---|---|---|
| 17 | 16 | 17 | 0 | 1 | 1.0000 |

Numbers for the adoption rule (I-D2):

| quantity | value |
|---|---|
| pooled_clean_difference_w1_minus_w0_on_h_d3_pairs | 1 |
| decoys_clean_w0 | 3 |
| decoys_clean_w1 | 3 |
| decoys_n | 3 |
| decoys_clean_difference_w1_minus_w0 | 0 |

## Arm R: pairs not attributable or without a clean pass (I-D4)

none

## W-0 next to PB and PC (descriptive; not a test: briefs, sizes, validity, pairs and the world-author model differ (PB: a model of the gate's line; PC: Fable; Phase D: Claude Opus 5.5))

Sources: PC: E:\Claude Projects\kapi-oss\evaluation\phase_c\run\RESULTS.json: gate/v050/classes, PB: PC RESULTS.json (the PB table PHASE_B_TABLE.json holds pair descriptors only, no counts): phase_b_next_to_c/phase_b/classes, PC_gate_version: v050, PB_gate_version: v040

| class | W0 pairs | W0 attributable | W0 PB-style | W0 clean | PB pairs | PB detections | PB clean | PC pairs | PC detections | PC clean |
|---|---|---|---|---|---|---|---|---|---|---|
| B-2 | 10 | 9 | 9 | 9 | 12 | 7 | 11 | 12 | 7 | 8 |
| B-3 | 7 | 6 | 6 | 7 | 12 | 8 | 8 | 10 | 8 | 8 |
| B-1 | 1 | 0 | 0 | 1 | 12 | 7 | 7 | 12 | 12 | 11 |
| B-6 | 2 | 1 | 2 | 2 | 12 | 11 | 11 | 12 | 10 | 12 |

## Decoys per arm and mechanism tag

| arm | class | tag | n | attributable | declared | PB-style | clean |
|---|---|---|---|---|---|---|---|
| R | B-1 | extreme-group-change | 1 | 1 | 1 | 1 | 1 |
| R | B-6 | significant-here-not-there | 1 | 1 | 1 | 1 | 1 |
| R | B-6 | units-not-independent | 1 | 1 | 1 | 1 | 1 |
| W0 | B-1 | extreme-group-change | 1 | 0 | 0 | 0 | 1 |
| W0 | B-6 | significant-here-not-there | 1 | 0 | 0 | 1 | 1 |
| W0 | B-6 | units-not-independent | 1 | 1 | 1 | 1 | 1 |
| W1 | B-1 | extreme-group-change | 1 | 1 | 1 | 1 | 1 |
| W1 | B-6 | significant-here-not-there | 1 | 0 | 0 | 1 | 1 |
| W1 | B-6 | units-not-independent | 1 | 1 | 1 | 1 | 1 |

## Validity drop rates

Label counts of FREEZE_VALIDITY.json: V2: 29, V1b: 7, V1a: 9, timing infeasible: 1, reference rejected by check_skeletons_d: 2, fidelity A (h): 2; pairs built 72; selected per class B-2: 10, B-3: 7, B-1: 1, B-6: 2.

| class | built | dropped | drop rate | labels |
|---|---|---|---|---|
| B-1 | 6 | 5 | 0.8333 | V2: 5, pass: 1 |
| B-2 | 30 | 19 | 0.6333 | V1a: 3, V1b: 2, V2: 11, pass: 11, reference rejected by check_skeletons_d: 2, timing infeasible: 1 |
| B-3 | 30 | 22 | 0.7333 | V1a: 6, V1b: 3, V2: 12, fidelity A (h): 1, pass: 8 |
| B-6 | 6 | 4 | 0.6667 | V1b: 2, V2: 1, fidelity A (h): 1, pass: 2 |

| class and subtype or tag | built | dropped | drop rate | labels |
|---|---|---|---|---|
| B-1 extreme-group-change | 1 | 0 | 0.0000 | pass: 1 |
| B-1 select-then-test-same-data | 3 | 3 | 1.0000 | V2: 3 |
| B-1 split-by-baseline-compare-change | 2 | 2 | 1.0000 | V2: 2 |
| B-2 L1.1 | 6 | 1 | 0.1667 | V2: 1, pass: 5 |
| B-2 L1.2 | 5 | 3 | 0.6000 | V2: 1, pass: 2, reference rejected by check_skeletons_d: 2 |
| B-2 L1.3 | 5 | 4 | 0.8000 | V1b: 1, V2: 3, pass: 1 |
| B-2 L1.4 | 5 | 3 | 0.6000 | V2: 3, pass: 2 |
| B-2 L3.1 | 5 | 4 | 0.8000 | V1a: 1, V2: 3, pass: 1 |
| B-2 L3.2 | 4 | 4 | 1.0000 | V1a: 2, V1b: 1, timing infeasible: 1 |
| B-3 change-vs-baseline | 9 | 9 | 1.0000 | V1a: 1, V2: 7, fidelity A (h): 1 |
| B-3 ratio-shared-denominator | 7 | 1 | 0.1429 | V1a: 1, pass: 6 |
| B-3 ratio-vs-denominator-proxy | 7 | 6 | 0.8571 | V1a: 3, V1b: 2, V2: 1, pass: 1 |
| B-3 shared-measured-component | 7 | 6 | 0.8571 | V1a: 1, V1b: 1, V2: 4, pass: 1 |
| B-6 significant-here-not-there | 2 | 1 | 0.5000 | V1b: 1, pass: 1 |
| B-6 units-not-independent | 4 | 3 | 0.7500 | V1b: 1, V2: 1, fidelity A (h): 1, pass: 1 |

## Miss labels per arm and class

| arm | class | misses | by label | (e) by cause |
|---|---|---|---|---|
| R | B-2 | 0 | - | - |
| R | B-3 | 0 | - | - |
| R | B-1 | 0 | - | - |
| R | B-6 | 0 | - | - |
| W0 | B-2 | 1 | b: 1 | - |
| W0 | B-3 | 1 | b: 1 | - |
| W0 | B-1 | 1 | b: 1 | - |
| W0 | B-6 | 1 | c: 1 | - |
| W1 | B-2 | 1 | b: 1 | - |
| W1 | B-3 | 1 | b: 1 | - |
| W1 | B-1 | 0 | - | - |
| W1 | B-6 | 1 | c: 1 | - |

## Clean-pass classes per arm and class

| arm | class | failed clean passes | by class | (e) by cause |
|---|---|---|---|---|
| R | B-2 | 0 | - | - |
| R | B-3 | 0 | - | - |
| R | B-1 | 0 | - | - |
| R | B-6 | 0 | - | - |
| W0 | B-2 | 1 | 3: 1 | - |
| W0 | B-3 | 0 | - | - |
| W0 | B-1 | 0 | - | - |
| W0 | B-6 | 0 | - | - |
| W1 | B-2 | 0 | - | - |
| W1 | B-3 | 0 | - | - |
| W1 | B-1 | 0 | - | - |
| W1 | B-6 | 0 | - | - |

## Structure statistic (share of 200 minus samples at or beyond the half-way point)

| arm | class | pairs | share >= 0.5 | share < 0.5 | set by the brief | no statistic | not computable | no study file |
|---|---|---|---|---|---|---|---|---|
| R | B-2 | 10 | 5 | 0 | 5 | 0 | 0 | 0 |
| R | B-3 | 7 | 7 | 0 | 0 | 0 | 0 | 0 |
| R | B-1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| R | B-6 | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| W0 | B-2 | 10 | 5 | 0 | 5 | 0 | 0 | 0 |
| W0 | B-3 | 7 | 7 | 0 | 0 | 0 | 0 | 0 |
| W0 | B-1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| W0 | B-6 | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| W1 | B-2 | 10 | 5 | 0 | 5 | 0 | 0 | 0 |
| W1 | B-3 | 7 | 6 | 1 | 0 | 0 | 0 | 0 |
| W1 | B-1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| W1 | B-6 | 2 | 1 | 1 | 0 | 0 | 0 | 0 |

## Awareness (P / C / N)

First reading (r1b and r2; W-0 and W-1), per arm and class:

| arm | class | resolved | r1b | r2 |
|---|---|---|---|---|
| W0 | B-2 | P: 5, C: 3, N: 2, ?: 0 | P: 5, C: 3, N: 2, ?: 0 | P: 5, C: 2, N: 3, ?: 0 |
| W0 | B-3 | P: 4, C: 1, N: 2, ?: 0 | P: 4, C: 1, N: 2, ?: 0 | P: 3, C: 1, N: 3, ?: 0 |
| W0 | B-1 | P: 1, C: 0, N: 0, ?: 0 | P: 1, C: 0, N: 0, ?: 0 | P: 1, C: 0, N: 0, ?: 0 |
| W0 | B-6 | P: 1, C: 0, N: 1, ?: 0 | P: 1, C: 0, N: 1, ?: 0 | P: 1, C: 0, N: 1, ?: 0 |
| W0 | all | P: 11, C: 4, N: 5, ?: 0 | P: 11, C: 4, N: 5, ?: 0 | P: 10, C: 3, N: 7, ?: 0 |
| W1 | B-2 | P: 1, C: 1, N: 8, ?: 0 | P: 1, C: 1, N: 8, ?: 0 | P: 0, C: 2, N: 8, ?: 0 |
| W1 | B-3 | P: 2, C: 5, N: 0, ?: 0 | P: 2, C: 4, N: 1, ?: 0 | P: 2, C: 4, N: 1, ?: 0 |
| W1 | B-1 | P: 1, C: 0, N: 0, ?: 0 | P: 1, C: 0, N: 0, ?: 0 | P: 1, C: 0, N: 0, ?: 0 |
| W1 | B-6 | P: 0, C: 0, N: 2, ?: 0 | P: 0, C: 0, N: 2, ?: 0 | P: 0, C: 0, N: 2, ?: 0 |
| W1 | all | P: 4, C: 6, N: 10, ?: 0 | P: 4, C: 5, N: 11, ?: 0 | P: 3, C: 6, N: 11, ?: 0 |

Second reading (r3 and r4; W-1 only), per class:

| class | resolved | r3 | r4 |
|---|---|---|---|
| B-2 | P: 4, C: 5, N: 1, ?: 0 | P: 3, C: 4, N: 3, ?: 0 | P: 4, C: 5, N: 1, ?: 0 |
| B-3 | P: 4, C: 3, N: 0, ?: 0 | P: 4, C: 3, N: 0, ?: 0 | P: 4, C: 3, N: 0, ?: 0 |
| B-1 | P: 1, C: 0, N: 0, ?: 0 | P: 1, C: 0, N: 0, ?: 0 | P: 1, C: 0, N: 0, ?: 0 |
| B-6 | P: 2, C: 0, N: 0, ?: 0 | P: 2, C: 0, N: 0, ?: 0 | P: 2, C: 0, N: 0, ?: 0 |
| all | P: 11, C: 8, N: 1, ?: 0 | P: 10, C: 7, N: 3, ?: 0 | P: 11, C: 8, N: 1, ?: 0 |

Detection and clean pass by resolved first-reading level:

| arm | class | level | n | attributable | declared | PB-style | clean |
|---|---|---|---|---|---|---|---|
| W0 | B-2 | P | 5 | 5 | 5 | 5 | 5 |
| W0 | B-2 | C | 3 | 2 | 2 | 2 | 2 |
| W0 | B-2 | N | 2 | 2 | 2 | 2 | 2 |
| W0 | B-3 | P | 4 | 3 | 2 | 3 | 4 |
| W0 | B-3 | C | 1 | 1 | 1 | 1 | 1 |
| W0 | B-3 | N | 2 | 2 | 2 | 2 | 2 |
| W0 | B-1 | P | 1 | 0 | 0 | 0 | 1 |
| W0 | B-6 | P | 1 | 1 | 1 | 1 | 1 |
| W0 | B-6 | N | 1 | 0 | 0 | 1 | 1 |
| W0 | all | P | 11 | 9 | 8 | 9 | 11 |
| W0 | all | C | 4 | 3 | 3 | 3 | 3 |
| W0 | all | N | 5 | 4 | 4 | 5 | 5 |
| W1 | B-2 | P | 1 | 1 | 1 | 1 | 1 |
| W1 | B-2 | C | 1 | 0 | 0 | 0 | 1 |
| W1 | B-2 | N | 8 | 8 | 8 | 8 | 8 |
| W1 | B-3 | P | 2 | 2 | 2 | 2 | 2 |
| W1 | B-3 | C | 5 | 4 | 3 | 4 | 5 |
| W1 | B-1 | P | 1 | 1 | 1 | 1 | 1 |
| W1 | B-6 | N | 2 | 1 | 1 | 2 | 2 |
| W1 | all | P | 4 | 4 | 4 | 4 | 4 |
| W1 | all | C | 6 | 4 | 3 | 4 | 6 |
| W1 | all | N | 10 | 9 | 9 | 10 | 10 |

Detection and clean pass by resolved second-reading level (W-1):

| class | level | n | attributable | declared | PB-style | clean |
|---|---|---|---|---|---|---|
| B-2 | P | 4 | 3 | 3 | 3 | 4 |
| B-2 | C | 5 | 5 | 5 | 5 | 5 |
| B-2 | N | 1 | 1 | 1 | 1 | 1 |
| B-3 | P | 4 | 3 | 3 | 3 | 4 |
| B-3 | C | 3 | 3 | 2 | 3 | 3 |
| B-1 | P | 1 | 1 | 1 | 1 | 1 |
| B-6 | P | 2 | 1 | 1 | 2 | 2 |
| all | P | 11 | 8 | 8 | 9 | 11 |
| all | C | 8 | 8 | 7 | 8 | 8 |
| all | N | 1 | 1 | 1 | 1 | 1 |

## Pairs

### Arm R

| id | class | tag | faulty | fixed | attributable | generic | declared | PB-style | clean | miss label | clean-pass class | structure share | attrition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-007 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-008 | B-3 | shared-measured-component | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-010 | B-2 | L1.2 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-011 | B-2 | L1.3 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-012 | B-6 | units-not-independent | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.9150 | - |
| D-022 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-023 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-027 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-035 | B-2 | L1.2 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-040 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-042 | B-2 | L1.4 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-047 | B-1 | extreme-group-change | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-052 | B-6 | significant-here-not-there | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.9550 | - |
| D-055 | B-2 | L3.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-056 | B-3 | ratio-vs-denominator-proxy | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.7150 | - |
| D-062 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-064 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-066 | B-2 | L1.4 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-067 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-068 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |

### Arm W0

| id | class | tag | faulty | fixed | attributable | generic | declared | PB-style | clean | miss label | clean-pass class | structure share | attrition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-007 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-008 | B-3 | shared-measured-component | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-010 | B-2 | L1.2 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-011 | B-2 | L1.3 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-012 | B-6 | units-not-independent | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.0150 | - |
| D-022 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-023 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | False | True | True | - | - | 0.9950 | - |
| D-027 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-035 | B-2 | L1.2 | ok/NOT_FALSIFIABLE | ok/NOT_FALSIFIABLE | True | False | True | True | False | - | 3 | 1.0000 | - |
| D-040 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-042 | B-2 | L1.4 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-047 | B-1 | extreme-group-change | ok/WEAK | ok/WEAK | False | False | False | False | True | b | - | 1.0000 | - |
| D-052 | B-6 | significant-here-not-there | ok/NOT_FALSIFIABLE | ok/WEAK | False | False | False | True | True | c | - | 0.1550 | - |
| D-055 | B-2 | L3.1 | ok/WEAK | ok/WEAK | False | False | False | False | True | b | - | 1.0000 | - |
| D-056 | B-3 | ratio-vs-denominator-proxy | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.9450 | - |
| D-062 | B-3 | ratio-shared-denominator | ok/WEAK | ok/WEAK | False | False | False | False | True | b | - | 1.0000 | - |
| D-064 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-066 | B-2 | L1.4 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-067 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-068 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 0.9950 | - |

### Arm W1

| id | class | tag | faulty | fixed | attributable | generic | declared | PB-style | clean | miss label | clean-pass class | structure share | attrition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-007 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-008 | B-3 | shared-measured-component | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-010 | B-2 | L1.2 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-011 | B-2 | L1.3 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-012 | B-6 | units-not-independent | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.7350 | - |
| D-022 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-023 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | False | True | True | - | - | 1.0000 | - |
| D-027 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-035 | B-2 | L1.2 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.9500 | - |
| D-040 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-042 | B-2 | L1.4 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-047 | B-1 | extreme-group-change | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.9750 | - |
| D-052 | B-6 | significant-here-not-there | ok/NOT_FALSIFIABLE | ok/WEAK | False | False | False | True | True | c | - | 0.1550 | - |
| D-055 | B-2 | L3.1 | ok/WEAK | ok/WEAK | False | False | False | False | True | b | - | 1.0000 | - |
| D-056 | B-3 | ratio-vs-denominator-proxy | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 0.9850 | - |
| D-062 | B-3 | ratio-shared-denominator | ok/WEAK | ok/WEAK | False | False | False | False | True | b | - | 1.0000 | - |
| D-064 | B-2 | L1.1 | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | - | - |
| D-066 | B-2 | L1.4 | ok/NOT_FALSIFIABLE | ok/WEAK | True | False | True | True | True | - | - | 1.0000 | - |
| D-067 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 1.0000 | - |
| D-068 | B-3 | ratio-shared-denominator | ok/NOT_FALSIFIABLE | ok/WEAK | True | True | True | True | True | - | - | 0.0000 | - |

