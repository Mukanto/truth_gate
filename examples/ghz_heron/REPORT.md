# GHZ on ibm_kingston: report

One pre-registered run on 2026-11-12. Job `dbqfmhmjjaos73ah82u0`, 156-qubit Heron r2, 169 s of QPU time, 317 circuits × 2000 shots, no error mitigation.

## Pre-registered verdicts (rules frozen before the run, applied unchanged)

| | Verdict | |
|---|---|---|
| G1: model accurate for small states | HOLDS | R = 0.959 at n = 4, 0.932 at n = 8 |
| G2: excess decay grows with size | HOLDS | R falls from 0.794 (n = 16) to 0.682 (n = 48) |
| G3: model predicts the GME reach | FAILS | measured reach 16, predicted 32 |

Controls K1 (no spurious coherence on mixture states), K2 (simulator) and K3 (integrity) passed. The designer recomputed every number independently from the raw counts.

## What the blind audit changed in how to read them
- The model's readout term was the wrong function for the estimator F = (P + C)/2. The populations P lose readout error once per qubit, but the parity-based coherence C loses it twice.
- Treating P and C separately, and still assuming independent errors, the predicted reach becomes 16, which matches the device. The excess-decay test then no longer passes (CI upper bound +0.010).
- **G2 and G3 were decided by this modelling error, which is the designer's, not by the device.** The verdicts stay as pre-registered. They are reported together with this limitation and with the exploratory re-analysis in `AUDIT_blind.md`.
- The audit also found two weaknesses in the criteria themselves:
  - G1 is effectively one-sided: its upper bound cannot be reached.
  - G2 cannot isolate its named cause: almost any underestimated independent error makes it hold.

## What stands (device-side facts)

| n | F | 95% CI (shot noise) | P | C |
|---|---|---|---|---|
| 4 | 0.915 | 0.907–0.923 | 0.938 | 0.892 |
| 8 | 0.855 | 0.846–0.864 | 0.880 | 0.830 |
| 16 | 0.609 | 0.598–0.620 | 0.693 | 0.526 |
| 32 | 0.387 | 0.376–0.400 | 0.474 | 0.301 |
| 48 | 0.246 | 0.235–0.257 | 0.329 | 0.163 |

- Genuine multipartite entanglement without mitigation holds up to 16 qubits on this patch. The patch was chosen error-blind, rooted at qubit 69. This is one day and one patch.
- Exploratory, after the run: coherence follows the independent-error prediction closely (C/C_pred ≈ 0.91 at n = 48). The shortfall is in the populations (P/P_pred ≈ 0.81). The fitted GHZ phase drifts with n (−0.12 to −0.49 rad), a coherent-error signature.

## Kapı's part (pilot measure, a case study)
- **First certificate:** 7 distinct flags, all real and all fixed (missing controls, grid passed as data, a vacuous equality).
- **Second certificate:** 1 flag, the designer's mis-sized control, fixed.
- **Rejected:** probes yielding non-positive model predictions.
- **Final certificate:** WEAK.
- **What Kapı could not see:** the critical defect, the model–estimator mismatch, sits in the model, outside Kapı's scope. This is the same pattern as the first prospective case.

## Lessons added to the protocol
1. Predict the quantity you estimate. When the estimator combines components (here P and C), derive the model's prediction for each component separately.
2. Check that both bounds of a band can be reached. A bound the model cannot reach makes the test one-sided; say so or remove it.
3. A directional hypothesis must be identified. If every unmodelled error produces the predicted direction, the test does not isolate the named cause.
