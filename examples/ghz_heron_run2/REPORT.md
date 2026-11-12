# GHZ run 2: report

One pre-registered run on 2026-11-12, about 25 minutes after run 1. Job `dbqg2dgk09pc73at7d9g`, ibm_kingston, 196 s of QPU time, 368 circuits × 2000 shots, no mitigation.

## Pre-registered verdicts (frozen, applied unchanged, recomputed independently)

| | Verdict | |
|---|---|---|
| H1: corrected model M2 accurate for small states (\|ΔF\| ≤ 0.05) | FAILS | 0.045 at n = 4, **0.055** at n = 8 |
| H2: M2 predicts the GME reach | HOLDS | point values: measured 24, predicted 24 |
| H3: the shortfall is population-specific | FAILS | holds at n = 32 (−0.006), not at n = 48 (+0.034) |

Controls K1 (no spurious coherence), K2 (simulator) and K3 (integrity) passed.

| n | F | 95% CI (shot noise) | F_pred (M2) | F_M (run-1 model) |
|---|---|---|---|---|
| 4 | 0.892 | 0.883–0.901 | 0.937 | 0.954 |
| 8 | 0.833 | 0.824–0.842 | 0.888 | 0.917 |
| 16 | 0.613 | 0.602–0.624 | 0.697 | 0.768 |
| 24 | 0.509 | 0.498–0.520 | 0.589 | 0.674 |
| 32 | 0.384 | 0.372–0.396 | 0.451 | 0.536 |
| 48 | 0.243 | 0.232–0.253 | 0.288 | 0.360 |

## How to read them (blind audit, confirmed by the designer)
- **This was a data replicate, not a model test.** The device had not been recalibrated since run 1; the two snapshots differ only in their time stamp. So M2's predictions were the same ones already compared with run 1's data. The run tests whether run 1's measurements replicate; it does not test whether M2 survives a new calibration.
- **Shot-noise CIs are too narrow at small n.** Between the runs, coherence at n = 4 and 8 moved by about −0.03 (several shot-noise σ) and F by about −0.022, while n ≥ 16 agreed within 0.004.
- **H1 failed by less than that drift.** Run 1's data would have passed it, so its failure is not informative on its own.
- **M2 still overpredicts F at every n** (R = 0.84–0.95). Its infidelity is too small by roughly 40–50% at n = 4 and 8.
- **H2 holds by 0.009 on point values.** The CI-based reach is 16, and the interpolated crossings differ by about 4–5 qubits. Read it as "the reach is 16 with confidence, about 24 on point values".
- **H3 was underpowered** (about 25–30%), and its identification argument covered readout and T2 errors but not Pauli structure or correlated readout. The direction (P short more than C at n = 32 and 48) appeared in all four cells of the two runs; it is not demonstrated.
- **One of the designer's own controls was useless.** The bit-order positive control guarded against a failure that cannot affect this estimator, because P and C are invariant under any permutation of bits.

## What stands across both runs
- The large-n behaviour replicates: F(16) ≈ 0.61, F(32) ≈ 0.385, F(48) ≈ 0.245 in both runs.
- GME without mitigation is certified up to 16 qubits, with 24 at the threshold on point values. This holds for one patch, one calibration day.
- The calibration-based independent-error model, even with P and C treated consistently, predicts fidelity too high by 5–16%. The gap is roughly flat for n ≥ 16, which suggests a few bad qubits or edges rather than a per-qubit effect.

## Kapı's part
- Before the freeze, Kapı raised 2 actionable flags, both fixed:
  - a criterion that held on random data;
  - a control that a fix had made inconsistent.
- The designer caught 3 errors in their own first draft before any certificate.
- As in the earlier cases, the decisive weaknesses were outside Kapı's scope: same calibration, drift larger than shot noise, power, identification.

## Lessons added to the protocol
- **Rule 9, extended:** the noise ceiling includes run-to-run drift. Measure it with a repeat run, or with a cheap repeated subset, before setting tolerances.
- **Rule 16:** compute the power of every confirmatory test for the effect size you expect. An underpowered FAILS reads "not demonstrated".
- **Rule 2, extended:** a replicate on the same calibration (or the same inputs) tests the data, not the model's predictions. Say which one a run is.
- **§4:** before adding a control in response to an audit, check that the failure it guards against can affect the estimator.
