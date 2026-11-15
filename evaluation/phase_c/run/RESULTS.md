# Phase C results

Gate under test (pre-registered primary table): 0.5.0. Versions with data: 0.5.0, 0.4.1.
Wilson bounds are one-sided 95% (z = 1.6448536269514722); HOLDS needs pairs >= 10 and both lower bounds >= 0.6.
B-4: no documented cases; no evidence either way. B-5: no documented cases; no evidence either way.
Information flags (K1_ABSTAINED:*, K2_MINUS_UNREAD, K8_SOME_CHANGES, BAD_RETURN) and the capping flag K1_ABSTAINED_MAJORITY:* never count as expected flags.
Allowed claims (I-8): what the gate did on errors documented in the literature, with worlds declared by a different Claude model line that was not told the error; every class verdict carries its resolved P/C/N shares (declared worlds that may contain what the error exploits).

## 1. Truth_Gate per class

### Truth_Gate 0.5.0 (pre-registered primary table)

In-scope classes

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| B-1 | 12 | 12 | 7 | 5 | 0 | 11 | 0.8160 | 0.6988 | yes | HOLDS |
| B-2 | 12 | 7 | 5 | 2 | 0 | 8 | 0.3560 | 0.4315 | yes | FAILS |
| B-3 | 10 | 8 | 6 | 2 | 0 | 8 | 0.5408 | 0.5408 | yes | FAILS |
| B-6 | 12 | 10 | 0 | 10 | 0 | 12 | 0.6008 | 0.8160 | yes | HOLDS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 0 | 1 | 0 | 1 | 0.2699 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 5 | 0 | 0 | 1 | 0.6489 | 0.0460 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 1 | 0 | 1 | 0 | 2 | 0.1209 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 0 | 0 | 0 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 0 | 0 | 0 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|
| O-1 | 2 | 0 | 0 | 0 | 0 | 2 |
| O-2 | 2 | 2 | 1 | 1 | 0 | 2 |
| O-3 | 2 | 0 | 0 | 0 | 0 | 2 |

### Truth_Gate 0.4.1 (same files, same rules)

In-scope classes

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| B-1 | 12 | 8 | 4 | 4 | 0 | 7 | 0.4315 | 0.3560 | yes | FAILS |
| B-2 | 12 | 7 | 5 | 2 | 0 | 8 | 0.3560 | 0.4315 | yes | FAILS |
| B-3 | 10 | 8 | 6 | 2 | 0 | 8 | 0.5408 | 0.5408 | yes | FAILS |
| B-6 | 12 | 10 | 0 | 10 | 0 | 12 | 0.6008 | 0.8160 | yes | HOLDS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 0 | 1 | 0 | 1 | 0.2699 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 5 | 0 | 0 | 1 | 0.6489 | 0.0460 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 1 | 0 | 1 | 0 | 2 | 0.1209 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 0 | 0 | 0 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 0 | 0 | 0 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|
| O-1 | 2 | 0 | 0 | 0 | 0 | 2 |
| O-2 | 2 | 2 | 1 | 1 | 0 | 2 |
| O-3 | 2 | 0 | 0 | 0 | 0 | 2 |

### Class verdicts

* B-1 (0.5.0): **HOLDS** - pairs 12, detections 12 (lower bound 0.8160), clean passes 11 (lower bound 0.6988); resolved awareness of these 12 pairs: P 10/12 (0.833; of which no log 5), C 2/12 (0.167), N 0/12 (0.000); declared worlds that may contain what the error exploits.
* B-2 (0.5.0): **FAILS** - pairs 12, detections 7 (lower bound 0.3560), clean passes 8 (lower bound 0.4315); resolved awareness of these 12 pairs: P 10/12 (0.833; of which no log 5), C 2/12 (0.167), N 0/12 (0.000); declared worlds that may contain what the error exploits.
* B-3 (0.5.0): **FAILS** - pairs 10, detections 8 (lower bound 0.5408), clean passes 8 (lower bound 0.5408); resolved awareness of these 10 pairs: P 10/10 (1.000; of which no log 1), C 0/10 (0.000), N 0/10 (0.000); declared worlds that may contain what the error exploits.
* B-6 (0.5.0): **HOLDS** - pairs 12, detections 10 (lower bound 0.6008), clean passes 12 (lower bound 0.8160); resolved awareness of these 12 pairs: P 12/12 (1.000; of which no log 3), C 0/12 (0.000), N 0/12 (0.000); declared worlds that may contain what the error exploits.
* B-1 (0.4.1): **FAILS** - pairs 12, detections 8 (lower bound 0.4315), clean passes 7 (lower bound 0.3560); resolved awareness of these 12 pairs: P 10/12 (0.833; of which no log 5), C 2/12 (0.167), N 0/12 (0.000); declared worlds that may contain what the error exploits.
* B-2 (0.4.1): **FAILS** - pairs 12, detections 7 (lower bound 0.3560), clean passes 8 (lower bound 0.4315); resolved awareness of these 12 pairs: P 10/12 (0.833; of which no log 5), C 2/12 (0.167), N 0/12 (0.000); declared worlds that may contain what the error exploits.
* B-3 (0.4.1): **FAILS** - pairs 10, detections 8 (lower bound 0.5408), clean passes 8 (lower bound 0.5408); resolved awareness of these 10 pairs: P 10/10 (1.000; of which no log 1), C 0/10 (0.000), N 0/10 (0.000); declared worlds that may contain what the error exploits.
* B-6 (0.4.1): **HOLDS** - pairs 12, detections 10 (lower bound 0.6008), clean passes 12 (lower bound 0.8160); resolved awareness of these 12 pairs: P 12/12 (1.000; of which no log 3), C 0/12 (0.000), N 0/12 (0.000); declared worlds that may contain what the error exploits.

## 2. Baselines (same pairs)

### Flag everything (detection = all, clean pass = none)

In-scope classes

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| B-1 | 12 | 12 | 0 | 0.8160 | 0.0000 | yes | FAILS |
| B-2 | 12 | 12 | 0 | 0.8160 | 0.0000 | yes | FAILS |
| B-3 | 10 | 10 | 0 | 0.7871 | 0.0000 | yes | FAILS |
| B-6 | 12 | 12 | 0 | 0.8160 | 0.0000 | yes | FAILS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 0 | 0.2699 | 0.0000 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 0 | 0.6489 | 0.0000 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 2 | 0 | 0.4250 | 0.0000 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 2 | 0 | 0.4250 | 0.0000 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 2 | 0 | 0.4250 | 0.0000 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | clean passes |
|---|---|---|---|
| O-1 | 2 | 2 | 0 |
| O-2 | 2 | 2 | 0 |
| O-3 | 2 | 2 | 0 |

### Noise-only, from the 0.5.0 certificates

In-scope classes

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| B-1 | 12 | 7 | 11 | 0.3560 | 0.6988 | yes | FAILS |
| B-2 | 12 | 5 | 8 | 0.2200 | 0.4315 | yes | FAILS |
| B-3 | 10 | 6 | 8 | 0.3516 | 0.5408 | yes | FAILS |
| B-6 | 12 | 0 | 12 | 0.0000 | 0.8160 | yes | FAILS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 0 | 1 | 0.0000 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 1 | 0.6489 | 0.0460 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | clean passes |
|---|---|---|---|
| O-1 | 2 | 0 | 2 |
| O-2 | 2 | 1 | 2 |
| O-3 | 2 | 0 | 2 |

### Noise-only, from the 0.4.1 certificates

In-scope classes

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| B-1 | 12 | 4 | 7 | 0.1595 | 0.3560 | yes | FAILS |
| B-2 | 12 | 5 | 8 | 0.2200 | 0.4315 | yes | FAILS |
| B-3 | 10 | 6 | 8 | 0.3516 | 0.5408 | yes | FAILS |
| B-6 | 12 | 0 | 12 | 0.0000 | 0.8160 | yes | FAILS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 0 | 1 | 0.0000 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 1 | 0.6489 | 0.0460 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | clean passes |
|---|---|---|---|
| O-1 | 2 | 0 | 2 |
| O-2 | 2 | 1 | 2 |
| O-3 | 2 | 0 | 2 |

### Declared-only, from the 0.5.0 certificates

In-scope classes

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| B-1 | 12 | 11 | 11 | 0.6988 | 0.6988 | yes | HOLDS |
| B-2 | 12 | 7 | 8 | 0.3560 | 0.4315 | yes | FAILS |
| B-3 | 10 | 7 | 8 | 0.4417 | 0.5408 | yes | FAILS |
| B-6 | 12 | 10 | 12 | 0.6008 | 0.8160 | yes | HOLDS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 1 | 0.2699 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 1 | 0.6489 | 0.0460 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 1 | 2 | 0.1209 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | clean passes |
|---|---|---|---|
| O-1 | 2 | 0 | 2 |
| O-2 | 2 | 2 | 2 |
| O-3 | 2 | 0 | 2 |

### Declared-only, from the 0.4.1 certificates

In-scope classes

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| B-1 | 12 | 7 | 7 | 0.3560 | 0.3560 | yes | FAILS |
| B-2 | 12 | 7 | 8 | 0.3560 | 0.4315 | yes | FAILS |
| B-3 | 10 | 7 | 8 | 0.4417 | 0.5408 | yes | FAILS |
| B-6 | 12 | 10 | 12 | 0.6008 | 0.8160 | yes | HOLDS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 1 | 0.2699 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 5 | 5 | 1 | 0.6489 | 0.0460 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 2 | 1 | 2 | 0.1209 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 2 | 0 | 2 | 0.0000 | 0.4250 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | clean passes |
|---|---|---|---|
| O-1 | 2 | 0 | 2 |
| O-2 | 2 | 2 | 2 |
| O-3 | 2 | 0 | 2 |

## 3. Primary comparison: 0.5.0 against 0.4.1 (unit: the one component of each file)

Study files (faulty and fixed, all classes) with a component UNDEFINED under 0.4.1: 8 (the comparison is informative from 5).

| class | files with UNDEFINED | components UNDEFINED | hard | plus majority | soft only | unknown | detections gained | clean passes gained | faulty UNDEFINED -> FALSIFIABLE/WEAK | fixed UNDEFINED -> NOT_FALSIFIABLE | components K1_ABSTAINED_MAJORITY |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B-1 | 8 | 8 | 0 | 0 | 8 | 0 | 4 | 4 | 0 | 0 | 2 |
| B-2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B-3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B-6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| O-1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| O-2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| O-3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

By name

* B-1: detections gained: B1-05, B1-06, B1-08, B1-09; clean passes gained: B1-05, B1-06, B1-08, B1-09; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: B1-05/faulty/C, B1-05/fixed/C; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: NOT_FALSIFIABLE 4, WEAK 4.
* B-2: detections gained: none; clean passes gained: none; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: none; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: none.
* B-3: detections gained: none; clean passes gained: none; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: none; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: none.
* B-6: detections gained: none; clean passes gained: none; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: none; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: none.
* O-1: detections gained: none; clean passes gained: none; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: none; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: none.
* O-2: detections gained: none; clean passes gained: none; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: none; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: none.
* O-3: detections gained: none; clean passes gained: none; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): none; fixed twins UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid): none; components with K1_ABSTAINED_MAJORITY: none; 0.5.0 verdicts of the components UNDEFINED under 0.4.1: none.

Components whose verdict differs between the versions: B1-05/faulty, B1-05/fixed, B1-06/faulty, B1-06/fixed, B1-08/faulty, B1-08/fixed, B1-09/faulty, B1-09/fixed.

### Losses (spec 0.7 section 4: none can occur; a loss counts against 0.5.0)

No 0.4.1 detection and no 0.4.1 clean pass is lost under 0.5.0.

Not comparable (a check without a certificate or a timeout in either version): none.

## 4. Abstention shares (sum of undefined - hard_undefined over the K1 streams / sum of n), 0.5.0

| class | twin | Phase C soft undefined / n | Phase C share | Phase B (R1, 0.5.0) soft undefined / n | Phase B share |
|---|---|---|---|---|---|
| B-1 | faulty | 211 / 4800 | 0.0440 | 451 / 4800 | 0.0940 |
| B-1 | fixed | 187 / 4800 | 0.0390 | 463 / 4800 | 0.0965 |
| B-2 | faulty | 0 / 4800 | 0.0000 | 0 / 4800 | 0.0000 |
| B-2 | fixed | 0 / 4800 | 0.0000 | 23 / 4800 | 0.0048 |
| B-3 | faulty | 0 / 4000 | 0.0000 | 0 / 4800 | 0.0000 |
| B-3 | fixed | 0 / 4000 | 0.0000 | 0 / 4800 | 0.0000 |
| B-6 | faulty | 0 / 4800 | 0.0000 | 0 / 4800 | 0.0000 |
| B-6 | fixed | 0 / 4800 | 0.0000 | 0 / 4800 | 0.0000 |
| O-1 | faulty | 0 / 800 | 0.0000 | 0 / 800 | 0.0000 |
| O-1 | fixed | 0 / 800 | 0.0000 | 0 / 800 | 0.0000 |
| O-2 | faulty | 0 / 800 | 0.0000 | 0 / 800 | 0.0000 |
| O-2 | fixed | 0 / 800 | 0.0000 | 0 / 800 | 0.0000 |
| O-3 | faulty | 0 / 800 | 0.0000 | 0 / 800 | 0.0000 |
| O-3 | fixed | 0 / 800 | 0.0000 | 0 / 800 | 0.0000 |

Phase B column: descriptive, from the 0.5.0 certificates of the Phase B files recorded by the official R1.

## 5. Awareness breakdown (descriptive)

Resolved reading = the higher of the two readers (N < C < P); 'no log' counts as P and is shown separately.

| class | reader 1 P/C/N/no log | reader 2 P/C/N/no log | resolved P/C/N | no log (inside resolved P) |
|---|---|---|---|---|
| B-1 | 5/2/0/5 | 5/2/0/5 | 10/2/0 | 5 |
| B-2 | 3/4/0/5 | 5/1/1/5 | 10/2/0 | 5 |
| B-3 | 9/0/0/1 | 9/0/0/1 | 10/0/0 | 1 |
| B-6 | 7/0/2/3 | 9/0/0/3 | 12/0/0 | 3 |
| O-1 | 1/0/0/1 | 0/1/0/1 | 2/0/0 | 1 |
| O-2 | 1/1/0/0 | 1/1/0/0 | 1/1/0 | 0 |
| O-3 | 0/2/0/0 | 2/0/0/0 | 2/0/0 | 0 |

### Results by awareness level, resolved reading (0.5.0, counts only)

| level | class | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|---|
| P | all | 47 | 35 | 16 | 19 | 0 | 41 |
| P | B-1 | 10 | 10 | 6 | 4 | 0 | 9 |
| P | B-2 | 10 | 6 | 4 | 2 | 0 | 7 |
| P | B-3 | 10 | 8 | 6 | 2 | 0 | 8 |
| P | B-6 | 12 | 10 | 0 | 10 | 0 | 12 |
| P | O-1 | 2 | 0 | 0 | 0 | 0 | 2 |
| P | O-2 | 1 | 1 | 0 | 1 | 0 | 1 |
| P | O-3 | 2 | 0 | 0 | 0 | 0 | 2 |
| C | all | 5 | 4 | 3 | 1 | 0 | 4 |
| C | B-1 | 2 | 2 | 1 | 1 | 0 | 2 |
| C | B-2 | 2 | 1 | 1 | 0 | 0 | 1 |
| C | O-2 | 1 | 1 | 1 | 0 | 0 | 1 |
| no log (counted in P) | all | 15 | 11 | 4 | 7 | 0 | 14 |
| no log (counted in P) | B-1 | 5 | 5 | 3 | 2 | 0 | 5 |
| no log (counted in P) | B-2 | 5 | 3 | 1 | 2 | 0 | 4 |
| no log (counted in P) | B-3 | 1 | 0 | 0 | 0 | 0 | 1 |
| no log (counted in P) | B-6 | 3 | 3 | 0 | 3 | 0 | 3 |
| no log (counted in P) | O-1 | 1 | 0 | 0 | 0 | 0 | 1 |

### Results by awareness level, reader1 reading (0.5.0, counts only)

| level | class | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|---|
| P | all | 26 | 22 | 11 | 11 | 0 | 22 |
| P | B-1 | 5 | 5 | 3 | 2 | 0 | 4 |
| P | B-2 | 3 | 2 | 2 | 0 | 0 | 2 |
| P | B-3 | 9 | 8 | 6 | 2 | 0 | 7 |
| P | B-6 | 7 | 6 | 0 | 6 | 0 | 7 |
| P | O-1 | 1 | 0 | 0 | 0 | 0 | 1 |
| P | O-2 | 1 | 1 | 0 | 1 | 0 | 1 |
| C | all | 9 | 5 | 4 | 1 | 0 | 7 |
| C | B-1 | 2 | 2 | 1 | 1 | 0 | 2 |
| C | B-2 | 4 | 2 | 2 | 0 | 0 | 2 |
| C | O-2 | 1 | 1 | 1 | 0 | 0 | 1 |
| C | O-3 | 2 | 0 | 0 | 0 | 0 | 2 |
| N | all | 2 | 1 | 0 | 1 | 0 | 2 |
| N | B-6 | 2 | 1 | 0 | 1 | 0 | 2 |
| no log | all | 15 | 11 | 4 | 7 | 0 | 14 |
| no log | B-1 | 5 | 5 | 3 | 2 | 0 | 5 |
| no log | B-2 | 5 | 3 | 1 | 2 | 0 | 4 |
| no log | B-3 | 1 | 0 | 0 | 0 | 0 | 1 |
| no log | B-6 | 3 | 3 | 0 | 3 | 0 | 3 |
| no log | O-1 | 1 | 0 | 0 | 0 | 0 | 1 |

### Results by awareness level, reader2 reading (0.5.0, counts only)

| level | class | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|---|
| P | all | 31 | 24 | 12 | 12 | 0 | 26 |
| P | B-1 | 5 | 5 | 3 | 2 | 0 | 4 |
| P | B-2 | 5 | 3 | 3 | 0 | 0 | 3 |
| P | B-3 | 9 | 8 | 6 | 2 | 0 | 7 |
| P | B-6 | 9 | 7 | 0 | 7 | 0 | 9 |
| P | O-2 | 1 | 1 | 0 | 1 | 0 | 1 |
| P | O-3 | 2 | 0 | 0 | 0 | 0 | 2 |
| C | all | 5 | 4 | 3 | 1 | 0 | 4 |
| C | B-1 | 2 | 2 | 1 | 1 | 0 | 2 |
| C | B-2 | 1 | 1 | 1 | 0 | 0 | 0 |
| C | O-1 | 1 | 0 | 0 | 0 | 0 | 1 |
| C | O-2 | 1 | 1 | 1 | 0 | 0 | 1 |
| N | all | 1 | 0 | 0 | 0 | 0 | 1 |
| N | B-2 | 1 | 0 | 0 | 0 | 0 | 1 |
| no log | all | 15 | 11 | 4 | 7 | 0 | 14 |
| no log | B-1 | 5 | 5 | 3 | 2 | 0 | 5 |
| no log | B-2 | 5 | 3 | 1 | 2 | 0 | 4 |
| no log | B-3 | 1 | 0 | 0 | 0 | 0 | 1 |
| no log | B-6 | 3 | 3 | 0 | 3 | 0 | 3 |
| no log | O-1 | 1 | 0 | 0 | 0 | 0 | 1 |

## 6. Overlap with Phase B and addendum sources

| class | pairs | overlapping pairs | addendum-source pairs | >= 4 addendum pairs | wording (more than half overlap) |
|---|---|---|---|---|---|
| B-1 | 12 | 4 | 6 | yes | - |
| B-2 | 12 | 6 | 4 | yes | - |
| B-3 | 10 | 4 | 4 | yes | - |
| B-6 | 12 | 5 | 4 | yes | - |
| O-1 | 2 | 1 | 0 | - | - |
| O-2 | 2 | 2 | 0 | - | - |
| O-3 | 2 | 1 | 0 | - | - |

### Truth_Gate 0.5.0 without the overlapping pairs (descriptive)

In-scope classes

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| B-1 | 8 | 8 | 5 | 3 | 0 | 8 | 0.7473 | 0.7473 | no | FAILS |
| B-2 | 6 | 5 | 4 | 1 | 0 | 2 | 0.4976 | 0.1173 | no | FAILS |
| B-3 | 6 | 4 | 3 | 1 | 0 | 5 | 0.3470 | 0.4976 | no | FAILS |
| B-6 | 7 | 5 | 0 | 5 | 0 | 7 | 0.4087 | 0.7212 | no | FAILS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 0 | 1 | 0 | 1 | 0.2699 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 4 | 4 | 4 | 0 | 0 | 0 | 0.5965 | 0.0000 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 1 | 0 | 0 | 0 | 0 | 1 | 0.0000 | 0.2699 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|
| O-1 | 1 | 0 | 0 | 0 | 0 | 1 |
| O-3 | 1 | 0 | 0 | 0 | 0 | 1 |

### Truth_Gate 0.4.1 without the overlapping pairs (descriptive)

In-scope classes

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| B-1 | 8 | 5 | 3 | 2 | 0 | 5 | 0.3480 | 0.3480 | no | FAILS |
| B-2 | 6 | 5 | 4 | 1 | 0 | 2 | 0.4976 | 0.1173 | no | FAILS |
| B-3 | 6 | 4 | 3 | 1 | 0 | 5 | 0.3470 | 0.4976 | no | FAILS |
| B-6 | 7 | 5 | 0 | 5 | 0 | 7 | 0.4087 | 0.7212 | no | FAILS |

B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)

| group | pairs | detections | generic | declared | K2-only | clean passes | detection lower | clean-pass lower | pairs>=10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| L1.1 | 1 | 1 | 0 | 1 | 0 | 1 | 0.2699 | 0.2699 | no | FAILS (descriptive, not a class verdict) |
| L1.2 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L1.3 | 4 | 4 | 4 | 0 | 0 | 0 | 0.5965 | 0.0000 | no | FAILS (descriptive, not a class verdict) |
| L1.4 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L3.1 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | no | FAILS (descriptive, not a class verdict) |
| L3.2 | 1 | 0 | 0 | 0 | 0 | 1 | 0.0000 | 0.2699 | no | FAILS (descriptive, not a class verdict) |

Out of scope (counts only, descriptive)

| group | pairs | detections | generic | declared | K2-only | clean passes |
|---|---|---|---|---|---|---|
| O-1 | 1 | 0 | 0 | 0 | 0 | 1 |
| O-3 | 1 | 0 | 0 | 0 | 0 | 1 |

Class lines without the overlapping pairs (descriptive):

* B-1 (0.5.0, without overlapping pairs, descriptive): **FAILS** - pairs 8, detections 8 (lower bound 0.7473), clean passes 8 (lower bound 0.7473); resolved awareness of these 8 pairs: P 6/8 (0.750; of which no log 4), C 2/8 (0.250), N 0/8 (0.000); declared worlds that may contain what the error exploits.
* B-2 (0.5.0, without overlapping pairs, descriptive): **FAILS** - pairs 6, detections 5 (lower bound 0.4976), clean passes 2 (lower bound 0.1173); resolved awareness of these 6 pairs: P 5/6 (0.833; of which no log 3), C 1/6 (0.167), N 0/6 (0.000); declared worlds that may contain what the error exploits.
* B-3 (0.5.0, without overlapping pairs, descriptive): **FAILS** - pairs 6, detections 4 (lower bound 0.3470), clean passes 5 (lower bound 0.4976); resolved awareness of these 6 pairs: P 6/6 (1.000; of which no log 1), C 0/6 (0.000), N 0/6 (0.000); declared worlds that may contain what the error exploits.
* B-6 (0.5.0, without overlapping pairs, descriptive): **FAILS** - pairs 7, detections 5 (lower bound 0.4087), clean passes 7 (lower bound 0.7212); resolved awareness of these 7 pairs: P 7/7 (1.000; of which no log 2), C 0/7 (0.000), N 0/7 (0.000); declared worlds that may contain what the error exploits.

## 7. Phase B next to Phase C (descriptive: briefs, worlds, criteria and the size rule differ)

Phase B gate: v040; Phase C gate: 0.5.0.

| group | B pairs | B detections | B clean passes | B det. lower | B clean lower | B verdict | C pairs | C detections | C clean passes | C det. lower | C clean lower | C verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-1 | 12 | 7 | 7 | 0.3560 | 0.3560 | FAILS | 12 | 12 | 11 | 0.8160 | 0.6988 | HOLDS |
| B-2 | 12 | 7 | 11 | 0.3560 | 0.6988 | FAILS | 12 | 7 | 8 | 0.3560 | 0.4315 | FAILS |
| B-3 | 12 | 8 | 8 | 0.4315 | 0.4315 | FAILS | 10 | 8 | 8 | 0.5408 | 0.5408 | FAILS |
| B-6 | 12 | 11 | 11 | 0.6988 | 0.6988 | HOLDS | 12 | 10 | 12 | 0.6008 | 0.8160 | HOLDS |
| L1.1 | 2 | 2 | 2 | 0.4250 | 0.4250 | FAILS | 1 | 1 | 1 | 0.2699 | 0.2699 | FAILS |
| L1.2 | 2 | 1 | 2 | 0.1209 | 0.4250 | FAILS | 0 | 0 | 0 | - | - | FAILS |
| L1.3 | 2 | 1 | 2 | 0.1209 | 0.4250 | FAILS | 5 | 5 | 1 | 0.6489 | 0.0460 | FAILS |
| L1.4 | 2 | 2 | 2 | 0.4250 | 0.4250 | FAILS | 2 | 1 | 2 | 0.1209 | 0.4250 | FAILS |
| L3.1 | 2 | 0 | 1 | 0.0000 | 0.1209 | FAILS | 2 | 0 | 2 | 0.0000 | 0.4250 | FAILS |
| L3.2 | 2 | 1 | 2 | 0.1209 | 0.4250 | FAILS | 2 | 0 | 2 | 0.0000 | 0.4250 | FAILS |
| O-1 | 2 | 1 | 2 | - | - | - | 2 | 0 | 2 | - | - | - |
| O-2 | 2 | 1 | 2 | - | - | - | 2 | 2 | 2 | - | - | - |
| O-3 | 2 | 0 | 1 | - | - | - | 2 | 0 | 2 | - | - | - |

## 8. Run times (seconds per check)

| version | checks | min | median | max | beyond 3600 s |
|---|---|---|---|---|---|
| 0.5.0 | 104 | 0.4 | 0.6 | 374.5 | 0 |
| 0.4.1 | 104 | 0.4 | 0.6 | 377.5 | 0 |

Commits recorded in the 0.5.0 run log (tag commit, worktree HEAD): 5661709326f11451323820210b8a49f0e16a031d / 5661709326f11451323820210b8a49f0e16a031d.

Commits recorded in the 0.4.1 run log (tag commit, worktree HEAD): 90e8dad70bd2b1ad3d12b7c470e8c648d5dd3652 / 90e8dad70bd2b1ad3d12b7c470e8c648d5dd3652.

## 9. Pairs

Label "error too small in the declared worlds at this size": a miss under 0.5.0 whose faulty file carries no expected flag and whose world:minus rate holds / n is at most 0.05 + 2 * sqrt(0.05 * 0.95 / n) (P-7 item 5).

| case | class | subtype | source | world | overlap with Phase B | size ratio | awareness r1/r2/resolved | faulty 0.5.0 | detected 0.5.0 | label 0.5.0 | fixed 0.5.0 | clean 0.5.0 | seconds 0.5.0 faulty / fixed | faulty 0.4.1 | detected 0.4.1 | label 0.4.1 | fixed 0.4.1 | clean 0.4.1 | seconds 0.4.1 faulty / fixed | interpretation label (0.5.0) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1-01 | B-1 | - | MOR03 | C33 | no (addendum source) | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.6 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.6 / 0.5 | - |
| B1-02 | B-1 | - | MOR03 | C43 | no (addendum source) | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.6 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.6 | - |
| B1-03 | B-1 | - | MOR03 | C50 | no (addendum source) | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | - |
| B1-04 | B-1 | - | KRI10 | C05 | no (addendum source) | source states none | C/C/C | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 2.5 / 2.4 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 2.4 / 2.3 | - |
| B1-05 | B-1 | - | KRI10 | C36 | no (addendum source) | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 71.4 / 70.5 | UNDEFINED | no | - | UNDEFINED | no | 70.9 / 70.8 | - |
| B1-06 | B-1 | - | KRI10 | C06 | no (addendum source) | source states none | C/C/C | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 39.8 / 37.6 | UNDEFINED | no | - | UNDEFINED | no | 39.7 / 37.6 | - |
| B1-07 | B-1 | - | KRI09 | C28 | yes, Phase B case B1-01 | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 14.5 / 14.7 | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 14.7 / 14.7 | - |
| B1-08 | B-1 | - | KRI09 | C54 | no | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 3.7 / 3.6 | UNDEFINED | no | - | UNDEFINED | no | 3.6 / 3.6 | - |
| B1-09 | B-1 | - | VUL09 | C19 | yes, Phase B case B1-04 | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 56.6 / 56.6 | UNDEFINED | no | - | UNDEFINED | no | 56.8 / 56.8 | - |
| B1-10 | B-1 | - | MAK19 | C41 | no | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.6 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.6 | - |
| B1-11 | B-1 | - | MAK19 | C31 | yes, Phase B case B1-07 | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 1.2 / 1.2 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 1.2 / 1.2 | - |
| B1-12 | B-1 | - | BAR05 | C11 | yes, Phase B case B1-11 | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | - |
| B2-01 | B-2 | L1.1 | KAP23 | C44 | no | country-years 896/896 = 1.0; indicators 30/90 = 0.33 | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 3.3 / 8.6 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 3.6 / 8.7 | - |
| B2-02 | B-2 | L1.4 | KAP23 | C37 | yes, Phase B case B2-07 | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 2.6 / 2.8 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 2.6 / 2.8 | - |
| B2-03 | B-2 | L1.4 | KAP23 | C21 | yes, Phase B case B2-07 | source states none | C/N/C | WEAK | no | - | WEAK | yes | 14.0 / 14.4 | WEAK | no | - | WEAK | yes | 16.3 / 15.6 | error too small in the declared worlds at this size (rate 0.0100 <= 0.0808, n 200) |
| B2-04 | B-2 | L3.1 | KAP23 | C34 | yes, Phase B case B2-09 | source states none | no log/no log/P | WEAK | no | - | WEAK | yes | 4.6 / 3.6 | WEAK | no | - | WEAK | yes | 4.4 / 3.5 | error too small in the declared worlds at this size (rate 0.0050 <= 0.0808, n 200) |
| B2-05 | B-2 | L3.1 | KAP23 | C51 | yes, Phase B case B2-10 | source states none | C/P/P | WEAK | no | - | WEAK | yes | 2.2 / 2.1 | WEAK | no | - | WEAK | yes | 2.2 / 2.1 | error too small in the declared worlds at this size (rate 0.0000 <= 0.0808, n 200) |
| B2-06 | B-2 | L3.2 | KAP23 | C47 | yes, Phase B case B2-11 | source states none | P/P/P | WEAK | no | - | WEAK | yes | 3.9 / 3.9 | WEAK | no | - | WEAK | yes | 3.9 / 3.9 | error too small in the declared worlds at this size (rate 0.0000 <= 0.0808, n 200) |
| B2-07 | B-2 | L3.2 | KAP23 | C42 | no | source states none | no log/no log/P | WEAK | no | - | WEAK | yes | 1.4 / 1.4 | WEAK | no | - | WEAK | yes | 1.4 / 1.4 | error too small in the declared worlds at this size (rate 0.0600 <= 0.0808, n 200) |
| B2-08 | B-2 | L1.3 | VAR06 | C26 | no (addendum source) | samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap) | P/P/P | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 8.8 / 111.9 | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 10.9 / 84.5 | - |
| B2-09 | B-2 | L1.3 | VAR06 | C32 | no (addendum source) | samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap) | no log/no log/P | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 11.3 / 110.7 | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 11.5 / 115.4 | - |
| B2-10 | B-2 | L1.3 | VAR06 | C48 | no (addendum source) | samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap) | C/C/C | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 46.4 / 374.5 | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 47.0 / 377.5 | - |
| B2-11 | B-2 | L1.3 | VAR06 | C01 | no (addendum source) | samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap) | C/P/P | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 5.1 / 42.1 | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 5.1 / 45.2 | - |
| B2-12 | B-2 | L1.3 | AMB02 | C07 | yes, Phase B case B2-03 | source states none (as read; the author's 62 x 2000 from memory is unverified) | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 3.2 / 6.5 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 3.2 / 6.5 | - |
| B3-01 | B-3 | - | CUR13 | C16 | no (addendum source) | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.6 / 0.6 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.6 / 0.6 | - |
| B3-02 | B-3 | - | CUR13 | C53 | no (addendum source) | source states none | P/P/P | WEAK | no | - | WEAK | yes | 0.5 / 0.6 | WEAK | no | - | WEAK | yes | 0.5 / 0.5 | error too small in the declared worlds at this size (rate 0.0100 <= 0.0808, n 200) |
| B3-03 | B-3 | - | CUR13 | C39 | no (addendum source) | source states none | no log/no log/P | WEAK | no | - | WEAK | yes | 0.5 / 0.6 | WEAK | no | - | WEAK | yes | 0.5 / 0.6 | error too small in the declared worlds at this size (rate 0.0000 <= 0.0808, n 200) |
| B3-04 | B-3 | - | CUR13 | C13 | no (addendum source) | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | generic | NOT_FALSIFIABLE | no | 0.4 / 0.5 | - |
| B3-05 | B-3 | - | PEA97 | C12 | yes, Phase B case B3-05 | skeletons 1000/'some thousand' = about 1.0 | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.6 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.6 | - |
| B3-06 | B-3 | - | PEA97 | C09 | yes, Phase B case B3-05 | observers 3/3 = 1.0; trials: source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.7 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.6 / 0.7 | - |
| B3-08 | B-3 | - | ARC81 | C30 | no | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.5 | - |
| B3-09 | B-3 | - | ARC81 | C04 | yes, Phase B case B3-01 | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.5 | - |
| B3-11 | B-3 | - | KRO93 | C24 | no | source states none | P/P/P | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 0.5 / 0.5 | - |
| B3-12 | B-3 | - | KRO93 | C25 | yes, Phase B case B3-09 | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | NOT_FALSIFIABLE | no | 0.7 / 0.7 | NOT_FALSIFIABLE | yes | declared | NOT_FALSIFIABLE | no | 0.7 / 0.7 | - |
| B6-01 | B-6 | - | LAZ18 | C27 | no (addendum source) | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | - |
| B6-02 | B-6 | - | LAZ18 | C38 | no (addendum source) | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | - |
| B6-03 | B-6 | - | LAZ18 | C17 | no (addendum source) | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | - |
| B6-04 | B-6 | - | LAZ18 | C10 | no (addendum source) | source states none | P/P/P | WEAK | no | - | WEAK | yes | 0.5 / 0.5 | WEAK | no | - | WEAK | yes | 0.5 / 0.5 | error too small in the declared worlds at this size (rate 0.0350 <= 0.0808, n 200) |
| B6-05 | B-6 | - | NIE11 | C45 | yes, Phase B case B6-01 | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | - |
| B6-06 | B-6 | - | NIE11 | C52 | no | source states none | N/P/P | NOT_FALSIFIABLE | no | - | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | no | - | WEAK | yes | 0.5 / 0.5 | - |
| B6-07 | B-6 | - | NIE11 | C08 | yes, Phase B case B6-01 | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.4 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.4 | - |
| B6-08 | B-6 | - | HUR84 | C22 | yes, Phase B case B6-04 | tanks per treatment 4/2 = 2.0 (Hurlbert: twofold replication in such examples); samples per tank: source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.5 | - |
| B6-09 | B-6 | - | HUR84 | C35 | no | source states none | no log/no log/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | - |
| B6-10 | B-6 | - | LAZ10 | C23 | yes, Phase B case B6-07 | rats 10/10 = 1.0; days 3/3 = 1.0 | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | - |
| B6-11 | B-6 | - | LAZ10 | C03 | yes, Phase B case B6-08 | source states none | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.4 / 0.4 | - |
| B6-12 | B-6 | - | MAK19 | C15 | no | participants 40/40 = 1.0 | N/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.4 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.4 | - |
| O1-A | O | O-1 | KAP23 | C40 | no | source states none | no log/no log/P | WEAK | no | - | WEAK | yes | 12.1 / 47.3 | WEAK | no | - | WEAK | yes | 12.2 / 47.1 | error too small in the declared worlds at this size (rate 0.0000 <= 0.0808, n 200) |
| O1-B | O | O-1 | KAP23 | C49 | yes, Phase B case O1a | source states none | P/C/P | WEAK | no | - | WEAK | yes | 9.8 / 11.1 | WEAK | no | - | WEAK | yes | 9.7 / 11.1 | error too small in the declared worlds at this size (rate 0.0000 <= 0.0808, n 200) |
| O2-A | O | O-2 | SIM11 | C18 | yes, Phase B case O2a | participants per cell 20/20 = 1.0 | P/P/P | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.5 | NOT_FALSIFIABLE | yes | declared | WEAK | yes | 0.5 / 0.4 | - |
| O2-B | O | O-2 | SIM11 | C20 | yes, Phase B case O2a | maximum participants per condition 50/50 = 1.0 | C/C/C | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 2.1 / 0.4 | NOT_FALSIFIABLE | yes | generic | WEAK | yes | 2.1 / 0.4 | - |
| O3-A | O | O-3 | BAG09 | C29 | no | cell lines 60/60 = 1.0; probe sets 1000/12 558-22 283 = 0.045-0.080 (reduced to the cap) | C/P/P | NOT_FALSIFIABLE | no | - | WEAK | yes | 1.7 / 1.6 | NOT_FALSIFIABLE | no | - | WEAK | yes | 1.7 / 1.6 | - |
| O3-B | O | O-3 | HER14 | C14 | yes, Phase B case O3b | countries 20/20 = 1.0; years 64/64 = 1.0 | C/P/P | WEAK | no | - | WEAK | yes | 0.7 / 0.6 | WEAK | no | - | WEAK | yes | 0.6 / 0.6 | error too small in the declared worlds at this size (rate 0.0000 <= 0.0808, n 200) |

### Flags per pair

| case | expected flags present 0.5.0 | all faulty flags 0.5.0 | all fixed flags 0.5.0 | expected flags present 0.4.1 | all faulty flags 0.4.1 | all fixed flags 0.4.1 |
|---|---|---|---|---|---|---|
| B1-01 | HIGH_RATE:control:permute_active, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:permute_active, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_active, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:permute_active, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros |
| B1-02 | K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | K2_LOW_POWER, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_DEGENERATE, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | K2_LOW_POWER, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_DEGENERATE, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B1-03 | HIGH_RATE:control:swap_readings_2_and_3_at_random_within_patient, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:swap_readings_2_and_3_at_random_within_patient, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:swap_readings_2_and_3_at_random_within_patient, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:swap_readings_2_and_3_at_random_within_patient, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros |
| B1-04 | HIGH_RATE:probe:noise, K5_HOLDS_ON_NOISE | HIGH_RATE:probe:noise, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:probe:noise, K5_HOLDS_ON_NOISE | HIGH_RATE:probe:noise, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B1-05 | HIGH_RATE:control:random_sign_per_participant, HIGH_RATE:control:scramble_voxels_within_participant, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:random_sign_per_participant, HIGH_RATE:control:scramble_voxels_within_participant, HIGH_RATE:probe:noise, K1_ABSTAINED:world:minus, K1_ABSTAINED_MAJORITY:world:minus, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K4_INCONCLUSIVE, K5_INCONCLUSIVE:zeros | K1_ABSTAINED:world:minus, K1_ABSTAINED_MAJORITY:world:minus, K4_INCONCLUSIVE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:random_sign_per_participant, HIGH_RATE:control:scramble_voxels_within_participant, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:random_sign_per_participant, HIGH_RATE:control:scramble_voxels_within_participant, HIGH_RATE:probe:noise, K1_UNDEFINED, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K4_INCONCLUSIVE, K5_INCONCLUSIVE:zeros | K1_UNDEFINED, K4_INCONCLUSIVE, K5_INCONCLUSIVE:zeros |
| B1-06 | HIGH_RATE:control:permute_contrast_across_trials, HIGH_RATE:probe:shuffle:response,contrast, K2_HIGH_SIZE, K5_HOLDS_ON_SHUFFLE | HIGH_RATE:control:permute_contrast_across_trials, HIGH_RATE:probe:shuffle:response,contrast, K1_ABSTAINED:world:minus, K2_HIGH_SIZE, K5_HOLDS_ON_SHUFFLE, K5_INCONCLUSIVE:zeros | K1_ABSTAINED:world:minus, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_contrast_across_trials, HIGH_RATE:probe:shuffle:response,contrast, K2_HIGH_SIZE, K5_HOLDS_ON_SHUFFLE | HIGH_RATE:control:permute_contrast_across_trials, HIGH_RATE:probe:shuffle:response,contrast, K1_UNDEFINED, K2_HIGH_SIZE, K5_HOLDS_ON_SHUFFLE, K5_INCONCLUSIVE:zeros | K1_UNDEFINED, K5_INCONCLUSIVE:zeros |
| B1-07 | HIGH_RATE:control:shuffle_orientation_labels_within_neuron, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:shuffle_orientation_labels_within_neuron, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:zeros | HIGH_RATE:probe:noise, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:shuffle_orientation_labels_within_neuron, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:shuffle_orientation_labels_within_neuron, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:zeros | HIGH_RATE:probe:noise, K5_INCONCLUSIVE:zeros |
| B1-08 | HIGH_RATE:control:permute_stimulus_condition_across_trials, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_stimulus_condition_across_trials, HIGH_RATE:probe:noise, K1_ABSTAINED:world:minus, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K1_ABSTAINED:world:minus, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_stimulus_condition_across_trials, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_stimulus_condition_across_trials, HIGH_RATE:probe:noise, K1_UNDEFINED, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K1_UNDEFINED, K5_INCONCLUSIVE:zeros |
| B1-09 | HIGH_RATE:control:permute_trait_across_participants, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_trait_across_participants, HIGH_RATE:probe:noise, K1_ABSTAINED:world:minus, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K1_ABSTAINED:world:minus, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_trait_across_participants, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_trait_across_participants, HIGH_RATE:probe:noise, K1_UNDEFINED, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K1_UNDEFINED, K5_INCONCLUSIVE:zeros |
| B1-10 | HIGH_RATE:control:permute_rate_rest, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_rate_rest, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_rate_rest, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_rate_rest, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B1-11 | HIGH_RATE:control:permute_patient, K2_HIGH_SIZE | HIGH_RATE:control:permute_patient, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_patient, K2_HIGH_SIZE | HIGH_RATE:control:permute_patient, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B1-12 | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros |
| B2-01 | HIGH_RATE:control:permute_onset_across_country_years, HIGH_RATE:control:permute_onset_histories_across_countries, K2_HIGH_SIZE | HIGH_RATE:control:permute_onset_across_country_years, HIGH_RATE:control:permute_onset_histories_across_countries, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_onset_across_country_years, HIGH_RATE:control:permute_onset_histories_across_countries, K2_HIGH_SIZE | HIGH_RATE:control:permute_onset_across_country_years, HIGH_RATE:control:permute_onset_histories_across_countries, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-02 | HIGH_RATE:control:permute_outcome, K2_HIGH_SIZE | HIGH_RATE:control:permute_outcome, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_outcome, K2_HIGH_SIZE | HIGH_RATE:control:permute_outcome, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-03 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-04 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-05 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-06 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-07 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B2-08 | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros |
| B2-09 | HIGH_RATE:control:permute_responder, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_responder, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_responder, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_responder, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_responder, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_responder, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros |
| B2-10 | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_class_across_samples, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros |
| B2-11 | HIGH_RATE:control:permute_group_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,group_b, K2_HIGH_SIZE | HIGH_RATE:control:permute_group_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,group_b, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_group_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,group_b, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_group_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,group_b, K2_HIGH_SIZE | HIGH_RATE:control:permute_group_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,group_b, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_group_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,group_b, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros |
| B2-12 | HIGH_RATE:control:permute_tumour_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,tumour, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_tumour_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,tumour, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_tumour_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,tumour, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_tumour_labels, HIGH_RATE:probe:noise, HIGH_RATE:probe:shuffle:expression,tumour, K2_HIGH_SIZE, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-01 | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-02 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-03 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-04 | HIGH_RATE:control:permute_kidney_within_body_mass_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_kidney_within_body_mass_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_kidney_within_body_mass_blocks, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_kidney_within_body_mass_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:permute_kidney_within_body_mass_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_kidney_within_body_mass_blocks, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros |
| B3-05 | HIGH_RATE:probe:noise | HIGH_RATE:probe:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:probe:noise | HIGH_RATE:probe:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-06 | HIGH_RATE:control:decouple_observers_within_true_value_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:decouple_observers_within_true_value_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:decouple_observers_within_true_value_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:decouple_observers_within_true_value_blocks, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-08 | HIGH_RATE:control:permute_second_baseline_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_second_baseline_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_second_baseline_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_second_baseline_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-09 | HIGH_RATE:control:permute_uptake_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_uptake_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_uptake_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE | HIGH_RATE:control:permute_uptake_across_patients, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-11 | HIGH_RATE:control:permute_gene_a_across_samples, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:permute_gene_a_across_samples, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_gene_a_across_samples, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS | HIGH_RATE:control:permute_gene_a_across_samples, HIGH_RATE:probe:noise, K2_FAILS_UNREACHABLE, K2_HIGH_SIZE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B3-12 | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros |
| B6-01 | HIGH_RATE:control:permute_exposed_across_dams, K2_HIGH_SIZE | HIGH_RATE:control:permute_exposed_across_dams, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_exposed_across_dams, K2_HIGH_SIZE | HIGH_RATE:control:permute_exposed_across_dams, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-02 | HIGH_RATE:control:reassign_wells_to_treatment, K2_HIGH_SIZE | HIGH_RATE:control:reassign_wells_to_treatment, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:reassign_wells_to_treatment, K2_HIGH_SIZE | HIGH_RATE:control:reassign_wells_to_treatment, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-03 | HIGH_RATE:control:permute_dose_across_animals, K2_HIGH_SIZE | HIGH_RATE:control:permute_dose_across_animals, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_dose_across_animals, K2_HIGH_SIZE | HIGH_RATE:control:permute_dose_across_animals, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-04 | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-05 | K2_HIGH_SIZE, K2_NO_SEPARATION | K2_HIGH_SIZE, K2_LOW_POWER, K2_NO_SEPARATION, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE, K2_NO_SEPARATION | K2_HIGH_SIZE, K2_LOW_POWER, K2_NO_SEPARATION, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-06 | - | K2_HOLDS_UNREACHABLE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K2_HOLDS_UNREACHABLE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-07 | HIGH_RATE:control:swap_region_labels_in_half_the_subjects, K2_HIGH_SIZE | HIGH_RATE:control:swap_region_labels_in_half_the_subjects, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:swap_region_labels_in_half_the_subjects, K2_HIGH_SIZE | HIGH_RATE:control:swap_region_labels_in_half_the_subjects, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-08 | HIGH_RATE:control:permute_treated_across_tanks, K2_HIGH_SIZE | HIGH_RATE:control:permute_treated_across_tanks, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_treated_across_tanks, K2_HIGH_SIZE | HIGH_RATE:control:permute_treated_across_tanks, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-09 | HIGH_RATE:control:reassign_plots_to_treatment, K2_HIGH_SIZE | HIGH_RATE:control:reassign_plots_to_treatment, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:reassign_plots_to_treatment, K2_HIGH_SIZE | HIGH_RATE:control:reassign_plots_to_treatment, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-10 | HIGH_RATE:control:permute_treated_across_rats, K2_HIGH_SIZE | HIGH_RATE:control:permute_treated_across_rats, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_treated_across_rats, K2_HIGH_SIZE | HIGH_RATE:control:permute_treated_across_rats, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-11 | HIGH_RATE:control:permute_cortisol_subjects, HIGH_RATE:probe:shuffle:heart_rate,cortisol, K2_HIGH_SIZE | HIGH_RATE:control:permute_cortisol_subjects, HIGH_RATE:probe:shuffle:heart_rate,cortisol, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_cortisol_subjects, HIGH_RATE:probe:shuffle:heart_rate,cortisol, K2_HIGH_SIZE | HIGH_RATE:control:permute_cortisol_subjects, HIGH_RATE:probe:shuffle:heart_rate,cortisol, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| B6-12 | HIGH_RATE:control:permute_group_labels, K2_HIGH_SIZE | HIGH_RATE:control:permute_group_labels, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:permute_group_labels, K2_HIGH_SIZE | HIGH_RATE:control:permute_group_labels, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| O1-A | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| O1-B | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| O2-A | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | K2_HIGH_SIZE | K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| O2-B | HIGH_RATE:control:reassign_conditions, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:reassign_conditions, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | HIGH_RATE:control:reassign_conditions, HIGH_RATE:probe:noise, K2_HIGH_SIZE | HIGH_RATE:control:reassign_conditions, HIGH_RATE:probe:noise, K2_HIGH_SIZE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| O3-A | - | K2_HOLDS_UNREACHABLE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros | - | K2_HOLDS_UNREACHABLE, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:zeros |
| O3-B | - | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | - | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros |
