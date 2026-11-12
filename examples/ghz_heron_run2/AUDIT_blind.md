# Blind audit: GHZ run 2 (fresh agent, 2026-11-12)

The auditor did not see `certs/`, `REVISIONS.md` or `FREEZE_*.json` in either folder. Below are its findings, condensed, then the designer's re-check.

## Findings (auditor)
- **Recomputation:** H1 FAILS (|ΔF| = 0.0448 and 0.0548), H2 HOLDS (24 = 24), H3 FAILS (97.5th percentile −0.006 at n = 32, +0.031 at n = 48). All three follow from the rules. P_pred and C_pred re-derive from the saved components.
- **F1, major:** run 2 used the same calibration as run 1 (identical qubit and edge tables, 25 minutes apart). It is a data replicate, not an out-of-sample test of the model's predictions. Robustness to calibration drift is untested.
- **F2, major:** the shot-noise CIs understate the real uncertainty at small n.
  - Between the runs, C moved by −0.037 at n = 4 and −0.029 at n = 8 (z ≈ −4), with P stable. For C, Σz² = 40 on 5 degrees of freedom.
  - Run-to-run drift of about 0.02 in F is not in the bootstrap.
- **F3, major:** H1's failure is a coin flip between drifting runs.
  - The margin (0.017 below the band) is smaller than the run-to-run shift (0.022). Run 1's data, or the mean of both runs, would pass.
  - M2 overpredicts F at every n (R = 0.84–0.95). Infidelity is underestimated by about 40–50% at n = 4 and 8.
- **F4, major:** H3 was underpowered (about 25–30% power), and its effect shrank on replication.
  - The direction replicates in sign in all four cells (n = 32 and 48, both runs).
  - Pooled post hoc, contrary to I-4: −0.049 [−0.087, −0.014] at n = 32 and −0.068 [−0.122, −0.018] at n = 48.
  - The direction reverses at n = 4 and is equal at n = 16. Both shortfalls plateau for n ≥ 16–32, which suggests a few bad qubits or edges rather than a per-qubit effect.
- **F5, major:** H3's identification argument (rule 15) is incomplete.
  - Z-dominant gate errors cut C only; X-dominant errors and leakage cut P only. Correlated readout flips kill P but partly preserve parity.
  - The exclusion holds for underestimated ε_ro and T2 and for readout asymmetry, not for "generic errors" as a class.
- **F6, major:** H2's pass is thin and grid-quantised.
  - F(24) = 0.509 (CI [0.498, 0.520]); with Re-phase C it is 0.506.
  - The CI-based reach is 16, which would fail H2.
  - The interpolated crossings are about 29 (predicted) and about 25 (measured); the offset hides inside the 24 → 32 grid cell.
- **F7, minor:** K1 tests false positives only. The bit-order positive control cannot detect a permutation, because P and C are invariant under any bit permutation (they count 1s and use one φ for all qubits). It guards against a failure that cannot affect this estimator.
- **F8, note:** runs 1 and 2 agree at n ≥ 16 (ΔF = 0.004, −0.003, −0.003). The large-n shortfall (R ≈ 0.85 under M2) is stable.

**Per criterion (auditor):**
- H1: sound with caveat (drift-sensitive).
- H2: sound with caveat (thin margin; a CI-based definition would fail).
- H3: defective (underpowered, unstable in n, identification incomplete).

## Designer's re-check
- **F1 confirmed.** The two snapshots differ only in the `utc` field: qubits, edges, faulty lists and timing are identical.
- **F2 confirmed in direction.** Run 2 minus run 1, with z estimated roughly from shot noise:
  - C: −0.037 (n = 4) and −0.029 (n = 8), z ≈ −2.7 to −4 depending on the variance estimate; F: −0.023 and −0.022.
  - At n = 16, 32 and 48, |ΔF| ≤ 0.004.
- **Verdicts re-derived independently, from my own script and bootstrap:**
  - H1 |ΔF| = 0.0448 and 0.0548, so FAILS.
  - H2 n_meas = n_pred = 24, so HOLDS.
  - H3 97.5th percentile −0.006 (n = 32) and +0.034 (n = 48), so FAILS.
- **F7 accepted.** The bit-order control was a designer error: it was added in response to run 1's audit without checking that the guarded failure can affect a permutation-invariant estimator.
