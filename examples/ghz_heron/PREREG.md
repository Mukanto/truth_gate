# GHZ fidelity against the device's own error model: a pre-registered hardware study

Status: **pre-registration v2 draft (2026-11-12)**. Revisions with reasons are in `REVISIONS.md`. No circuit has been run on hardware. Before the freeze, simulators may be used only for the D4 smoke test and control K2. After the freeze, nothing below changes.
Designer: Claude, under the author's delegation. Hardware run: the author, on their own IBM Quantum account.

## 1. Question
On a 156-qubit IBM Heron r2 processor, consider an independent-error model built **only from the device's own published calibration**, snapshotted at submission. Does it predict the measured fidelity of n-qubit GHZ states? And, without error mitigation, up to which n does the device show genuine multipartite entanglement (GME, F > 1/2)?

## 2. Known vs prospective
**Known (literature, not tested here):**
- GHZ fidelity falls with n.
- F > 1/2 is a GME witness for GHZ states.
- Large GHZ states have been reported on IBM hardware using error detection or mitigation.

**Prospective:**
- How the raw, unmitigated fidelity on this device, on this day, with an error-blind qubit-selection rule, compares with the calibration model.
- The GME reach under these conditions.

## 3. Design choices (Claude, delegated; each with its reason)
- **D-1 Device:** among the operational 156-qubit Heron r2 backends visible to the account, the one with the fewest pending jobs at submission. Heron r2 is identified by `processor_type` when available, otherwise by num_qubits == 156 (revision #5). Name, calibration snapshot (JSON, SHA-256) and UTC time are recorded **before** submission. *Reason: the author's account decides availability. The rule is fixed now; the choice is not.*
- **D-2 Error-blind qubit selection:**
  - The operational graph G is the coupling map minus:
    - qubits flagged non-operational or with a missing readout error or T2;
    - edges with a missing or ≥ 0.5 two-qubit error.
  - Root: the qubit with the highest closeness centrality in the largest connected component of G. Ties go to the lowest index.
  - S_n: the first n qubits in BFS order from the root, neighbours in ascending index. T_n: their BFS parent edges.
  - *Reason: choosing the best-looking qubits by the model under test would bias the comparison (winner's curse).*
- **D-3 Circuit:**
  - H on the root, then CNOT parent → child along T_n in BFS order.
  - Transpile with `initial_layout` = S_n, `optimization_level=1`, `seed_transpiler=20261112`.
  - Integrity: the transpiled two-qubit gate count must equal n − 1 (no routing).
  - Sampler options: dynamical decoupling OFF, twirling OFF, default repetition delay. *Reason: raw device behaviour; no mitigation.*
- **D-4 Grid:** n ∈ {4, 8, 16, 32, 48}; 2000 shots per circuit.
- **D-5 Measurements per n:**
  - POP_n: GHZ_n, then measure all in Z.
  - PAR_n,j: GHZ_n, then Rz(−φ_j) and H on every qubit, then measure; φ_j = jπ/(n+1), j = 0..2n+1.
- **D-6 Control circuits:** mixture twins MIX_n for n ∈ {8, 32}.
  - Same as GHZ_n, but the root is measured mid-circuit right after its H, before the CNOT tree. This gives the classical mixture (|0ⁿ⟩⟨0ⁿ| + |1ⁿ⟩⟨1ⁿ|)/2: the same populations, zero coherence.
  - Run as POP plus the full PAR set. The mid-circuit bit is ignored in the analysis.
- **D-7 Budget:** 5 + 226 GHZ circuits plus 2 + 84 MIX circuits = 317 circuits, 634k shots, submitted as a single job. It must fit the 10-minute allocation. `--dry-run` prints the estimate first.

## 4. Estimators
- **Population:** P_n = [N(0ⁿ) + N(1ⁿ)] / shots.
- **Parity:** parity_j = mean over shots of (−1)^(number of 1s among the n data bits).
- **Coherence:** C_n = (2/(2n+2)) · |Σ_j parity_j · e^{i n φ_j}|.
- **Fidelity:** F_n = (P_n + C_n)/2.
- **Uncertainty:** 95% percentile interval from a multinomial bootstrap of every circuit's counts. B = 2000, seed 20261112, resampled jointly for each n.

## 5. Model M (fixed now)
F_pred(n) = Π_{e∈T_n}(1 − ε_2q(e)) · Π_{q∈S_n}(1 − ε_ro(q)) · Π_{1q gates g}(1 − ε_1q(g)) · Π_{q∈S_n} exp(−t_q / T2(q))

- The ε values and T2 come from the snapshot's `Target`.
- t_q is the idle time of qubit q (from its first operation to its measurement, minus its own gate durations) in the ALAP-scheduled transpiled POP_n.
- Rz gates are virtual (error 0).
- M is an independent-error heuristic. It ignores crosstalk, leakage, correlated and non-Markovian errors, and drift since calibration.
- *Reason for including the idle term:* without it, "the model overestimates" would follow by construction (a tautology).

## 6. Criteria
**R(n) = F_meas(n) / F_pred(n).**

| id | Claim | HOLDS | FAILS | UNDEFINED |
|---|---|---|---|---|
| G1 | The model is accurate for small states | 0.9 ≤ R(n) ≤ 1.1 for n = 4 and n = 8 | otherwise | F_pred(n) ≤ 0 or missing |
| G2 | Excess decay grows with size (directional H: correlated errors and crosstalk are not in M) | upper end of the bootstrap 95% CI of ln R(48) − ln R(16) < 0 | otherwise | F_meas(16) or F_meas(48) equals 0 in any bootstrap draw |
| G3 | The model predicts the GME reach | n_meas = n_pred | otherwise | n_pred = 0 (revision #3) |

- n_meas: the largest n in the grid with CI_low(F_meas) > 0.5, or 0 if there is none.
- n_pred: the largest n in the grid with F_pred > 0.5, or 0 if there is none.
- **Headline (reported, not a criterion):** n_meas, with F_meas, its CI, F_pred, R, P and C for every n.

**Data given to the criteria (schema):**
- `F_pred` (5,), with columns in the fixed GRID order [4, 8, 16, 32, 48]. The grid is a design constant, not data (revision #2).
- `F_hat` (5,): the point estimates.
- `F_boot` (B, 5): the bootstrap replicates, drawn jointly per replicate.
The criteria compute R, the CIs and ln R(48) − ln R(16) from these arrays themselves. No precomputed summary statistic enters a criterion (lesson of the previous study: vacuity probes cannot judge a precomputed scalar).

## 7. Controls (all must pass, else the run is "yorumlanamaz" / uninterpretable)
- **K1 (coherence detector, hardware):** for MIX_8 and MIX_32, the upper end of the bootstrap 95% CI of C_mix is ≤ 0.05. No spurious coherence may appear on a state with none. (Revision #4: the earlier F_mix condition was ill-posed on ideal data.)
- **K2 (estimator fidelity, simulator, pre-run allowed):** noiseless matrix-product-state simulation of the exact transpiled circuits. F_sim ≥ 0.98 for every n, and C_mix,sim ≤ 0.05.
- **K3 (integrity):** before submission, all of the following hold:
  - the transpiled two-qubit gate count is n − 1 for every GHZ and MIX circuit;
  - the snapshot is saved and hashed;
  - the freeze manifest verifies.
  - After the run: the job id and raw counts are saved, and the count totals equal the shots.

## 8. Kapı study
- `ghz_study.py` holds the criterion functions G1–G3 and synthetic worlds with the same data schema.
- It never calls Qiskit or hardware.
- The analysis script imports G1–G3 from it unchanged.

## 9. Interpretations and sensitivity (protocol §1.4)
- **I-1:** The fidelity estimator is the standard population-plus-parity estimate. Opposite reading: direct fidelity estimation. That is not run; it is recorded as a limitation.
- **I-2:** Qubit selection is error-blind (D-2). Opposite reading: best-qubit selection. That is not run, because of the budget. The headline holds only for D-2.
- **I-3:** The device is chosen at run time (D-1). Results are a single-day snapshot.

## 10. Run plan
1. Implement and run tests, D4 and K2 on simulators.
2. Get a Kapı certificate and revise per flag with reasons.
3. Freeze.
4. The author runs `ghz_run.py --dry-run`, then `ghz_run.py --submit` on their own account.
5. `ghz_analyze.py` produces the results.
6. Blind audit.
7. Report.
