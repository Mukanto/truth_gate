# GHZ on Heron r2, run 2: testing the corrected model on new data

Status: **pre-registration v2 draft (2026-11-12)**; revisions with reasons in `REVISIONS.md`. No circuit of this run has been executed. After the freeze, nothing below changes.
Designer: Claude, under the author's delegation. Hardware run: the author's account, submitted with the author's approval.

## 0. Why this run exists (known vs prospective)
- **Run 1** (`../ghz_heron/`, job dbqfmhmjjaos73ah82u0) had a model whose readout term did not match the estimator F = (P + C)/2. The blind audit found it. A corrected model (P and C predicted separately) was then evaluated on run 1's data as an exploratory analysis.
- **Known (run 1, exploratory, NOT evidence for this run):**
  - The corrected model gave R = F_meas/F_pred = 0.98, 0.96, 0.87, 0.85, 0.84 for n = 4, 8, 16, 32, 48.
  - Its predicted GME reach (16) matched the measured one.
  - Populations fell short of their prediction more than coherence did (P/P_pred ≈ 0.81 vs C/C_pred ≈ 0.91 at n = 48).
- **Run 1 is the training data. This run is the test.** Everything that run 1 suggested is re-tested here on new shots, at a different time, with a fresh calibration snapshot and possibly on a different device. Tolerances that were informed by run 1 are labelled as such.
- **Prospective:**
  - Does the corrected model M2 hold on new data?
  - Does the population-specific shortfall replicate?
  - Where does GME end on a finer grid?

## 1. Design (Claude, delegated). Unchanged from run 1 unless stated
- **D-1 device:** as in run 1. Least busy operational Heron r2 (processor_type, or num_qubits == 156 as fallback). Snapshot JSON and SHA-256 saved before submission.
- **D-2 qubit selection:** as in run 1 (error-blind; BFS from the closeness-central root of the operational graph).
- **D-3 circuits and transpiler options:** as in run 1. Dynamical decoupling OFF, twirling OFF, optimization_level 1, seed_transpiler 20261112. Integrity: n − 1 two-qubit gates.
- **D-4 grid (changed):** n ∈ {4, 8, 16, **24**, 32, 48}; 2000 shots. *Reason: run 1's audit (F3) found the grid too coarse near the GME boundary.*
- **D-5 measurements:** POP_n and PAR_n,j (j = 0..2n+1) as in run 1.
- **D-6 controls:** MIX_8 and MIX_32 as in run 1.
- **D-7 budget:** 6 + 276 GHZ circuits plus 2 + 84 MIX circuits = 368 circuits, 736k shots, about 190 s estimated. About 430 s of the month's allocation remains. `--dry-run` prints the estimate first. If the estimate exceeds 300 s the run is not submitted.

## 2. Estimators
As in run 1:
- P = [N(0ⁿ) + N(1ⁿ)]/shots;
- parity_j as in run 1;
- C = (2/(2n+2)) |Σ_j parity_j e^{inφ_j}|;
- F = (P + C)/2.

Uncertainty: joint multinomial bootstrap with B = 2000 and seed 20261113. It returns replicates of P, C and F per n.

## 3. Model M2 (fixed now; predicts each estimated component separately, protocol rule 13)
**Shared factors** (from the snapshot `Target`):
- G_pop(n) = Π_{tree}(1 − ε_cz) · Π_{1q gates in POP_n}(1 − ε_1q).
- G_par(n) = Π_{tree}(1 − ε_cz) · Π_{1q gates in PAR_n,0}(1 − ε_1q). The PAR circuits carry the extra basis-change gates.
- t_q = idle time of qubit q in the ALAP-scheduled POP_n (as in run 1).

**Predictions:**
- P_pred(n) = G_pop(n) · Π_q(1 − ε_ro(q)) · ½(1 + Π_q exp(−t_q/T1(q))). Amplitude damping during idle time acts on the |1…1⟩ branch.
- C_pred(n) = G_par(n) · Π_q(1 − 2ε_ro(q)) · Π_q exp(−t_q/T2(q)). Readout enters a parity twice; dephasing acts on coherence only.
- F_pred(n) = (P_pred(n) + C_pred(n))/2.

**Assumptions and reference arm:**
- ε_ro is the symmetric readout error reported in the snapshot. An asymmetry is not modelled (limitation I-2).
- **Reference arm (reported, not a criterion):** run 1's model M on this run's snapshot, F_M(n).

## 4. Criteria (protocol rules 13–15 applied)
**Data given to the criteria:** six columns in GRID order [4, 8, 16, 24, 32, 48].
- Predictions: `F_pred`, `P_pred`, `C_pred`, each (6,).
- Point estimates: `F_hat`, `P_hat`, `C_hat`, each (6,).
- Bootstrap replicates: `F_boot`, `P_boot`, `C_boot`, each (B, 6).

The criteria compute everything from these arrays themselves.

| id | Claim | HOLDS | FAILS | UNDEFINED |
|---|---|---|---|---|
| H1 | M2 is accurate for small states | \|F_hat(n) − F_pred(n)\| ≤ 0.05 for n = 4 and 8 | otherwise | any F_pred outside (0, 1) |
| H2 | M2 predicts the GME reach | n_meas = n_pred | otherwise | n_pred = 0, or any F_pred outside (0, 1) (revision #1) |
| H3 | The shortfall is population-specific | for n = 32 and 48: the 97.5th percentile of ln(P_boot/P_pred) − ln(C_boot/C_pred) < 0 | otherwise | any involved replicate or prediction ≤ 0 |

**How the criteria are built:**
- **H2:** n_meas is the largest n in GRID with F_hat > 0.5, else 0. n_pred is the largest n in GRID with F_pred > 0.5, else 0.
  - Both sides use point values (symmetric, per audit F3). Whether the 95% CI at n_meas excludes 0.5 is reported, not used.
- **Bands (rule 14):** H1 uses an absolute band, so both directions are reachable. F_pred + 0.05 < 1 for n = 4 and 8 must be checked in D4 on the snapshot; if it fails, H1 is reported as one-sided.
  - The 0.05 was **informed by run 1** (deviations of 0.021 and 0.034 under the corrected model).
- **Identification (rule 15):** H3's direction (P short more than C) is not produced by generic underestimation of the shared factors. Gate errors scale P and C alike. Underestimated readout or T2 lowers C more than P, the opposite direction. Only population-specific error (T1 beyond the model, leakage, bit-flip-type readout correlations) gives H3. This is a confirmatory test of a run-1 exploratory observation.

**Headline (reported):**
- n_meas and the fidelity table with P, C, F, CIs, the three predictions, and R;
- the reference arm F_M;
- C computed with Re instead of |·| (sensitivity I-1).

## 5. Controls (all must pass, else "yorumlanamaz")
- **K1:** for MIX_8 and MIX_32, the 97.5th percentile of the C_mix bootstrap is ≤ 0.05.
- **K2 (simulator, before the run):**
  - Noiseless MPS simulation of the exact transpiled circuits: F_sim ≥ 0.98 for every n, and C_mix,sim ≤ 0.05.
  - Additionally, a **bit-order positive control** (audit F8): a circuit set where one designated qubit gets an X before measurement. Its POP must show the shifted pattern, so the estimator's register handling is exercised.
- **K3 (integrity):**
  - n − 1 two-qubit gates per circuit;
  - snapshot saved and hashed;
  - freeze verified;
  - job id and counts saved; count totals equal shots;
  - M2 recomputed from the snapshot equals the saved model.

## 6. Interpretations and sensitivity (rule 4)
- **I-1:** C uses |·|, the best phase. Sensitivity: Re (nominal phase), reported.
- **I-2:** Symmetric readout error. No asymmetric data are in the snapshot. Limitation.
- **I-3:** One day, one patch, one device. The headline holds only for that.
- **I-4:** Run 1 is not pooled with run 2. Results are reported per run.

## 7. Kapı study
- `ghz2_study.py` holds H1–H3 and synthetic worlds with the schema above. It imports only numpy and kapi.
- Each criterion gets a control that models a plausible real failure.
- The analysis imports H1–H3 unchanged.

## 8. Run plan
1. Implement offline (FakeKingston), with tests, D4, K2 and the bit-order control.
2. Kapı certificates, revisions with reasons, freeze.
3. `--dry-run` on the account (read-only), then `--submit` with the author's approval.
4. `--fetch`, analysis, independent recomputation, blind audit, report.
