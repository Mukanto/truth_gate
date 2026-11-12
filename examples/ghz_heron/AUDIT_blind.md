# Blind audit: GHZ on ibm_kingston (fresh agent, 2026-11-12)

The auditor did not see `certs/`, `REVISIONS.md` or `FREEZE_GHZ.json`. Below are its findings, condensed, then the designer's re-check of the claims that would change a verdict.

## Findings (auditor)
- **F1, critical, could change G2 and G3:** the readout term of model M (PREREG §5, `ghz_core.py` 481–489) is the wrong function for the estimator F = (P + C)/2.
  - P decays like Π(1−ε_ro), but C comes from a parity and decays like Π(1−2ε_ro).
  - Readout makes up 0.67 of the 1.18 total −ln M at n = 48.
  - Treating P and C separately, and still assuming independent errors, gives F_pred = 0.936, 0.889, 0.699, 0.455, 0.292.
  - Under that treatment G2 flips to FAILS and G3 flips to HOLDS. G1 still holds.
- **F2, major, G2:** almost any independent error that M underestimates makes R fall like exp(−kn). So G2 does not isolate its named cause (correlated errors and crosstalk), and it is close to confirmatory by construction. The measured coherence tracks C_pred (0.163 vs 0.180 at n = 48), while the populations fall short of P_pred (0.329 vs 0.405).
- **F3, major, G3:** the test is an equality on a coarse grid, and it treats the two sides differently.
  - The measured side uses a CI lower bound; the predicted side uses a bare point.
  - F_pred(32) = 0.536 is only 0.036 above the threshold.
  - One CZ edge with a 5.3% error rate sits in the n ≥ 32 trees.
- **F4, major, G1:** the upper bound 1.1 cannot be reached, because F_pred(4) = 0.954 and F_pred(8) = 0.917. So G1 is effectively one-sided, and a model that always predicted F = 1 would still pass at n = 4.
- **F5, minor:**
  - The estimator matches PREREG §4, and the numbers reproduce to every printed digit.
  - Bit order is irrelevant.
  - |·| measures fidelity to the best-phase GHZ. The fitted phase grows with n (−0.12 … −0.49 rad), a coherent-error signature that M cannot express. Using Re instead of |·| changes no verdict.
- **F6, minor:** the percentile CI of |·| is invalid near zero (MIX_32: point 0.0008, CI [0.0009, 0.0108]). K1 uses only the upper end, so the check is conservative. All CIs cover shot noise only.
- **F7, minor:**
  - M is built from the POP circuit, while C comes from the PAR circuits, which have one more sx gate per qubit.
  - The idle term is small (about 10% of −ln M at n = 48). Dephasing should act on C only.
  - The two-qubit error from randomized benchmarking is an average gate infidelity.
- **F8, minor:**
  - K1 is a valid null test but loose: the 0.05 threshold is about five times the noise floor, and it runs only at n = 8 and n = 32.
  - K2 would pass even with a bit-order bug.
  - K3 is real; the auditor re-checked the trees, the circuits and the mid-circuit measurement.
- **F9, note:** the qubit selection is error-blind as claimed. The patch is typical. It is a single fixed patch.
- **F10, note:** n_meas = 16 rests on one job, one day and one patch. The GME witness is valid for n = 16 (CI low 0.598).

**Per criterion (auditor):**
- G1: sound with caveat.
- G2: defective as a test of its stated hypothesis.
- G3: sound with caveat. It flips under the corrected readout treatment.

## Designer's re-check (exploratory, after the run; not a replacement verdict)
**F1 confirmed.** The re-check used `run/model.json` components and `run/counts.json`:

| n | F_M (frozen) | F_pred, P/C treated separately | F_meas | R_M | R_P/C |
|---|---|---|---|---|---|
| 4 | 0.9539 | 0.9364 | 0.9149 | 0.959 | 0.977 |
| 8 | 0.9174 | 0.8887 | 0.8549 | 0.932 | 0.962 |
| 16 | 0.7677 | 0.6985 | 0.6092 | 0.794 | 0.872 |
| 32 | 0.5359 | 0.4550 | 0.3874 | 0.723 | 0.851 |
| 48 | 0.3604 | 0.2923 | 0.2457 | 0.682 | 0.841 |

- **n_pred:** 32 under M, 16 under the P/C treatment. So G3 would hold under P/C.
- **G2, independent bootstrap** (B = 2000, own resampling of the counts), 97.5th percentile of ln R(48) − ln R(16):
  - M: −0.105, so G2 HOLDS.
  - P/C: +0.010, so G2 FAILS.
- **Account data:** none in `run/` or `RESULTS_GHZ.*`.
