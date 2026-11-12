# GHZ on Heron: revisions before the freeze

Every decision here is the designer's (Claude, under the author's delegation) and gives its reason.
- First certificate: `certs/cert_v1.json`, body_sha256 fdffb5af…, overall NOT_FALSIFIABLE. It was stored verbatim.
- PREREG before these revisions: SHA16 1054B49CF558786C.

## Flags of certificate v1

| # | Criterion | Flag | Decision | Reason |
|---|---|---|---|---|
| 1 | G1, G2, G3 | K4_NO_CONTROL | **fixed** | Real gap. Each criterion now has a control that models a plausible real failure, not a cosmetic one: G1 gets "stale calibration" (F_pred inflated by 15%); G2 gets "column swap" (the n = 16 and n = 48 columns exchanged, i.e. an indexing bug); G3 gets "device worse than model" (every F_boot shifted down by 0.10). |
| 2 | G1, G2 | K5_INCONCLUSIVE:noise, :zeros | **fixed** | Real defect: the grid `n` was passed as data. The probes overwrote it, so the column lookup failed silently and returned None. `n` is a design constant, not a measurement. It is removed from the data. The criteria index the module constant GRID by position, and the analysis asserts that the column order equals GRID. |
| 3 | G3 | K5_HOLDS_ON_DEGENERATE, HIGH_RATE:probe:zeros, HIGH_RATE:probe:noise | **fixed** | Real defect: when the model predicts no GME anywhere (n_pred = 0), G3 holds vacuously whenever the device also shows none (0 = 0). G3 is now UNDEFINED when n_pred = 0: a reach comparison needs a predicted reach. |

## Defects found outside Kapı before the freeze (D4 / implementation review)

| # | Item | Decision | Reason |
|---|---|---|---|
| 4 | K1 (control of the real run) | **redefined** | As written, K1 contradicts itself on ideal data. C is an absolute value (≥ 0), so F_mix = (P + C)/2 ≥ 0.5 when P = 1, and "CI_low(F_mix) ≤ 0.5" can fail with no defect present. The coder found this while testing. The coherence detector is what K1 is for, so K1 is now: the upper end of the bootstrap 95% CI of C_mix is ≤ 0.05, for both MIX_8 and MIX_32. The F_mix condition is dropped: given C_mix ≤ 0.05 and P ≤ 1, F_mix ≤ 0.525, and the term adds nothing that is well posed. |
| 5 | D-1 (backend choice) | **made robust** | The implementation filtered on `processor_type` = Heron r2 and stops if that field is missing. Every 156-qubit IBM processor is Heron r2, so the rule is now: Heron r2 by `processor_type` when the field is present, otherwise num_qubits == 156. The chosen backend and the basis for choosing it are recorded. |

## Certificate v2 (after #1–#5)
- `certs/cert_v2.json`, body_sha256 08c6a640…, overall NOT_FALSIFIABLE.
- G1 WEAK and G2 WEAK, each with K5_INCONCLUSIVE:noise and :zeros.
- G3 NOT_FALSIFIABLE: HIGH_RATE:control:device_worse_than_model (G3 held on 129 of 200 draws) and K5_INCONCLUSIVE:zeros.
- Every v1 flag that was fixed is gone.

| # | Criterion | Flag | Decision | Reason |
|---|---|---|---|---|
| 6 | G3 | HIGH_RATE:control:device_worse_than_model | **fixed** | My error as designer: the control was too small to be a failure world. With a −0.10 shift the n = 16 column stays at 0.52 ± 0.01, so the device would still show GME at 16 and G3 holding there was correct. The control must lose one grid step of GME reach, so the shift is now −0.15 (n = 16 drops to 0.47). This sizes the control so that it represents the failure it names; it does not tune the criterion. |
| 7 | G1, G2, G3 | K5_INCONCLUSIVE (noise, zeros) | **rejected** | The probes produce F_pred ≤ 0, a physically impossible model prediction. By the pre-registered definition, R and the reach comparison are then UNDEFINED. The undefined branch is intended: a fidelity ratio against a non-positive prediction has no meaning. This is the same root as the rejected K5 flags of the previous study (probes on a quantity that is undefined outside its physical range). |

## Certificate v3 (final before freeze)
- `certs/cert_v3.json`, body_sha256 527a92a7…, overall **WEAK**: G1 WEAK, G2 WEAK, G3 WEAK. Only the rejected K5_INCONCLUSIVE flags (#7) remain; no mandatory flag.
- Tests 25 OK. ghz_d4: budget OK, K2 PASS, D4 OK. Selftest OK.

**Tally:** v1 raised 7 distinct flags on 3 criteria, all fixed (#1–#3, 3 root causes). v2 raised 1 new flag, fixed (#6, designer error in the control's size). The K5_INCONCLUSIVE flags were rejected (#7, 1 root cause). 2 defects were found outside Kapı (#4 K1 ill-posed, #5 D-1 brittle).

## Freeze (Claude, delegated, 2026-11-12)
The study is frozen with the gate at WEAK (capped only by #7).
