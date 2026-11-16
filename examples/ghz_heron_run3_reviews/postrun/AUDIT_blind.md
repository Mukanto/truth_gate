# Blind post-run audit: GHZ run 3 (job dbtecsfasvbs73b9l4e0, ibm_kingston, 2026-11-16)

I did not see any of the withheld files (gate certificates, revision logs, freeze manifests, earlier audits, the separate
recomputation). I wrote part 1 below before opening `report/REPORT_draft.md`. Scripts and intermediate files are in
`scratch/`.

## Part 1: audit

### Findings (sorted by severity)

| id | severity | location | finding | verdict impact |
|---|---|---|---|---|
| A1 | high | PREREG §1 C-1 per question, §4 H1; qubit 89 (S_48[6]); calibration_check.json dates; POP counts | Both the H1 FAILS and Q1's "model test" status rest on qubit 89 alone. See the detail below the table. | The rules were applied correctly. Q1 is in substance a test of one qubit's calibration entry: with that entry corrected from the run's own data, H1 would hold, and without the change the replicate label would apply. |
| A2 | high | PREREG §4 drift, power, readings; power_run3.json sensitivity; calibration dates | σ_rel comes from runs 1 and 2, taken 25 minutes apart on one calibration. Run 3's M2 inputs were 86–88 h old at execution: cz, readout, T1 and T2 from 2026-11-12, sx errors from 11-05 (275 h), q89's T1 from 11-11 (114 h); device last update 11-13 14:57. Only 4 of 8 input fields changed since run 2. Under the PREREG's own "drift × 2" row, power of H1 = 0.742 < 0.8 (×1.5: 0.849), and H4's n = 4 margin 0.0297 < 2σ_d,R = 0.0439 (tie at ×1.35). | The official readings follow the text. Taking the drift × 2 row seriously gives H1 "not demonstrated": the Q1 sentence changes, there is no joint sentence, and H4 gets "holds within drift". The "fails" reading is not robust. |
| A3 | medium | POP counts; qubit 72 (S_48[10]); H2, H3, R and tracking tables | The n ≥ 16 results are dominated by qubit 72. Its 0→1 error at execution is 0.21–0.32 (GHZ16–48, MIX32); in run 2 it was 0.014–0.045, and the calibrated value is 0.041. It varies between circuits minutes apart. It drives R(16–48) = 0.75–0.53, puts F(16) at 0.490 (hence n_meas = 8), and explains H3's reversed direction (2.5th pct +0.088, +0.068), as PREREG §4 itself predicts for readout error beyond the model. | H4 unchanged. H2 and H3 are reported only. Readings of the R and tracking tables as "overprediction grew with n" describe one faulty qubit. |
| A4 | medium | §4 Q2 sentence, I-7, K1–K3 | H4 HOLDS only shows that F < prediction at every n. "Still overpredicts" and "persist" suggest run 1/2's bias continued, but the shape changed: R falls from 0.96 to 0.53 instead of staying flat near 0.85, and H3 reversed. K1–K3, the only safeguards I-7 names, cannot detect a qubit with 15–30 % readout or relaxation error. | Q2 may be read as "F below M2's prediction at every n on this calibration", not as persistence of M2's systematic bias. |
| A5 | medium | §4 σ_rel,X; power_run3.json sigma_detail | σ_rel,P = 0 is a clipped negative estimate (mean term −3.0e-4). The ln-ratios of P between runs 1 and 2 are all positive at n = 4–32 (+0.010 to +0.017), but equal-weight pooling with the shot variances at n = 32 and 48 cancels them. With σ_rel,P = σ_rel,C, 2σ_d,R(4) = 0.0316 > 0.0297 and H4 gets "holds within drift"; power of H1 = 0.858. | The missing H4 label is an artefact of the clip. It changes the qualifier, not the verdict. |
| A6 | medium | §4 joint sentence; power_run3.json expected_outcome | "Exceeds 0.05 at small n": only n = 8 exceeds, by 0.0163 < 2σ_d,F = 0.0174 (within drift); at n = 4 the deviation is 0.0367. Under run 2's ratios the expected P(FAILS) of H1 was 0.69, so the FAILS is what the design expected if run 2's bias merely persisted. | The sentence must carry its label and the n = 8-only qualification. |
| A7 | low | §3; RESULTS_GHZ3.md "equal, verified" | "Equal" is correct: the history calibration, the current calibration and the snapshot are identical apart from utc, and all dates are ≤ the execution start. But §3 only checks for a recalibration after submission. "Verified" is a default string, not the §3 label, and can be read as saying the device state was verified. | None (clarity). |
| A8 | low | ghz3_analyze.py tracking_table | The run-2 and run-3 bootstraps share seed 20261113 and are paired by index. The correlation of the F replicates is ≤ 0.09, so the CIs are within about 4 % of independent ones. | None. |
| A9 | low | RESULTS_GHZ3.md log section | "The whole log" sits next to "2 lines" and n_fetch = 0. The file has 3 lines; the counts use only the anchored and accepted lines. | None (clarity). |
| A10 | low | §1 D-1, C-2, public push; §5 freeze, code identity | These cannot be verified here (manifests withheld, no network, no git). The code identity holds by byte comparison with run 2's copies. Quota 234 s ≥ actual 196 s. | None found (scope limits). |
| A11 | low | §5 K2; certs/k2_sim.json | The binding K2 is bit-identical to the design-time K2: the noiseless distribution does not depend on layout. K2 therefore re-checks logic and estimator only; layout rests on K3. | None (clarity). |

**A1 in detail.** Qubit 89's calibrated readout error rose from 0.0044 to 0.0513 on 11-12. Its T1 (184.06 µs) was
not re-measured: it is dated 11-11, before run 2. That one entry produces the entire ΔF_pred(8) = −0.059; with run 2's
value it would be +0.003, and max(|ΔF(4)|, |ΔF(8)|) = 0.006 < 0.02, so the Q1 replicate label would apply. At
execution, qubit 89's 1→0 error is 0.15–0.18 in every GHZ and MIX POP circuit (run 2: 0.01–0.03), above its
calibration. Putting that observed error into M2 gives |F_hat(8) − F_pred(8)| = 0.023–0.027 < 0.05.

### What the findings mean together

The official pipeline did what the pre-registration says, and every number in `RESULTS_GHZ3.*` reproduces. What
weakens the reading is the inputs. The calibration feeding M2 was 3.6 days old at execution, and two qubits of the fixed,
error-blind selection behaved far from their records. Qubit 89 (in S_8) decides H1 and Q1's model-test status. Qubit 72
(in S_16) dominates n ≥ 16. The drift scale σ_d comes from two runs 25 minutes apart, so it does not represent this
situation. Under the PREREG's own drift × 2 sensitivity, the Q1 reading would flip to "not demonstrated" and H4 would get
"holds within drift". The H4 verdict itself is robust: it holds at n = 4 and 8 with margins 0.030 and 0.068, and the
large-n margins are huge. But it cannot separate M2's systematic bias from stale inputs and faulty qubits (I-7).

How I attributed errors to qubits (A1, A3): for each qubit, I counted how often it reads 1 when at least 90 % of the
other qubits read 0, and how often it reads 0 when at least 90 % of the others read 1, in the POP circuits of runs 2 and
3 (same S_48). The anomaly appears at the same physical qubit for every n. With a wrong bit order it would wander between
logical positions. At n ≥ 16 qubit 89 has children in the tree, so a CNOT failure upstream of it would flip its whole
subtree; its single-qubit flips are therefore its own readout or relaxation. The F_pred(8) correction for qubit 89 uses
the conditional rates p(1|0) = 0.013 and p(0|1) = 0.149 (n = 8), or p(0|1) ≈ 0.165 (typical at n ≥ 16), in place of the
symmetric ε = 0.0513. It is an attribution estimate, not a re-analysis.

### Recomputed verdicts and key numbers

* **Controls.** K1 passes (C_mix q97.5: 0.029 at n = 8, 0.011 at n = 32). K2 passes in my own noiseless MPS
  simulation of `run/circuits.qpy` with two seeds. K3 passes on every item checkable here. Interpretable: yes.
* **H1: FAILS.** Deviations are 0.0367 (n = 4) and 0.0663 (n = 8). The reading is "fails" (power at submission 0.959). It
  is within drift: 0.0163 < 0.0174.
* **H4: HOLDS.** q97.5 of F_boot/F_pred = 0.970, 0.932, 0.766, 0.661, 0.678, 0.565. There is no within-drift label (n = 4:
  margin 0.0297 vs 2σ_d,R = 0.0220).
* **H2: FAILS** (reported). n_meas = 8, n_pred = 24. The CI-based reach is 8. The crossing is at 15.7 (CI 15.4–16.1),
  against a predicted 27.8.
* **H3: FAILS** (exploratory). q97.5 = +0.225 (n = 32) and +0.289 (n = 48). The 2.5th percentiles are +0.088 and +0.068,
  so the shortfall is clearly in the opposite direction: C falls short more than P.
* **Drift.** σ_rel,P = 0 (clipped from −3.0e-4) and σ_rel,C = 0.02235. σ_d,F = 0.0104, 0.0087, 0.0063, 0.0052, 0.0035,
  0.0022.
* **Power at submission.** Reproduced exactly by my own implementation of the §4 method: H1 0.959, H4 1.000; correlated
  0.9585/0.999; drift × 2 0.742/0.953. The expected outcomes match too.
* **C-1.** Satisfied. Four input fields changed (cz, readout, T1, T2); max |ΔF_pred| = 0.0592 at n = 8; Q1 is a model test
  (0.0592 ≥ 0.02).
* **Rule 14.** ok.
* **Answer (follows the §4 tables).** "Q1: on this run's calibration M2 is not accurate within 0.05 for 4 or 8 qubits. Q2:
  on a new calibration M2 still overpredicts the fidelity at every n. Together: the bias persists and exceeds 0.05 at small
  n." Label: within drift (H1).

### Checked and found sound

* **Snapshot.** The SHA-256 matches both the file and `job.json`.
* **Circuits and counts.** 368 circuits; names = manifest = counts order; every count total is 2000; every circuit has n − 1
  CZs on the tree edges and touches only S_n.
* **M2.** Recomputed from the snapshot and the submitted circuits, it equals `model.json` exactly (max difference 0).
* **Estimators.** My own P, C and F estimators agree with `ghz2_core` to 7e-16. The frozen bootstrap (B = 2000, seed
  20261113) reproduces `RESULTS_GHZ3_boot.npz` bit for bit, and every table entry and CI in `RESULTS_GHZ3.json` reproduces
  exactly.
* **Criteria.** My implementations of H1–H4 and the imported functions give the same verdicts.
* **Drift.** σ_rel recomputes to the same values. Run 1's P and C in `RESULTS_GHZ.json` equal a recomputation from run 1's
  raw counts. σ_d,F, σ_d,R and both drift labels follow §4 exactly.
* **Power file.** Its SHA-256 equals `job.json`'s. Its input hashes equal `certs/power.json` and the files in the folder.
  Its environment equals the analysis environment. My independent implementation reproduces all power and
  expected-outcome numbers with the pre-registered seed; other seeds give H1 power 0.9485–0.956.
* **C-1.** Recomputed: conditions (a) and (b) hold, and the per-question rule holds. Run 2's snapshot and model file hashes
  equal the known values. `calibration_check.json` records every M2-input date (none missing).
* **Execution-time calibration (§3).** The history snapshot hash is ok, and all M2-input dates are ≤ the execution start
  (11:18:15.9Z). History, current and submission snapshots are identical apart from utc, so "equal" is correct and the
  snapshot predictions are used with no label. The fetch was saved 54 s after the job finished, and there is a single
  attempt whose file hash matches the log.
* **Stopping rule.** There is one attempt (checks-passed line at 11:18:04Z, accepted at 11:18:09Z), no dry run, no
  refusal and no deviation. `job.json` anchors one log line, and its hash matches. The job was created at 11:18:09.7Z and
  started at 11:18:15.9Z, after the 11:17:30Z snapshot.
* **C-2 and D-7.** C-2: 1.15 × 186.5 = 214.5 ≤ 234 s. QPU time was 196 s (1.05 × the estimate). D-7: 186.5 ≤ 300 s.
* **Answer assembly.** It follows the three §4 tables and the label list. No device change, no one-sided H1, no replicate
  label and no §3 label apply.
* **Code identity.** `ghz2_core.py` and `ghz2_study.py` are byte-identical to run 2's copies.

## Part 2: the draft report

I read `report/REPORT_draft.md` only after writing part 1 above. Every number I could check matches the files except
item 4.

### Statements that the files contradict or do not support

1. **Deviations and limits.** The report says the freeze-list test "now fails because the analysis writes
   RESULTS_GHZ3.* into the folder". This is **contradicted** by `tests_ghz3.py` lines 261–275. The test removes
   FREEZE_GHZ3.json and RESULTS_GHZ3.json, .md and _boot.npz from the files it finds, and it skips run/, scratch/ and
   __pycache__/, so the stated cause cannot make it fail. If it fails, some other file in the folder is outside the
   14-file freeze list, and that file should be identified.
2. **Deviations and limits.** "The submission record is still anchored." **Not supported** for what the missed push
   was meant to protect. The hashes sit in `job.json`, which was not public before the data. `job.json` and the log
   could have been rewritten together, for example to drop a refused attempt or a dry run, and every K3 check would
   still pass. Only the job's identity and creation time are anchored by the service. Log completeness, and with it
   compliance with the stopping rule, is not independently verifiable for the period before publication.
3. **How to read it.** "Candidates … fluctuating defects, crosstalk and leakage; this run cannot tell them apart."
   **Contradicted in part.** The POP counts localize most of the excess:
   * Qubit 72 reads 1 instead of 0 in 21–32 % of shots at n = 16–48 and in MIX32 (run 2: 1.4–4.5 %; calibrated 4.1 %),
     and the rate varies between circuits run minutes apart.
   * Qubit 89 reads 0 instead of 1 in 15–18 % of shots in every GHZ and MIX circuit (run 2: 1–3 %; calibrated 5.1 %).

   The run cannot fully separate TLS, leakage and readout drift for these two qubits, but it does show the effect is
   localized. The candidate list also omits the calibration's age: 86–88 h at execution.
4. **How to read it.** The predicted change at n = 32 is −0.02499, which rounds to −0.02, not −0.03 as written.
5. **How to read it (GME).** "15.7 … against 16 with confidence in runs 1 and 2" is a **misleading comparison**. It
   sets a crossing against a CI-based grid reach. On the same measure, the crossing was 23.9 in run 1 and 24.6 in
   run 2, so it moved by about 9 qubits. On the CI-based measure, the reach went from 16 to 8.
6. **How to read it.** For K1 the report quotes the point values 0.013 and 0.002. K1 tests the 97.5th percentile:
   0.029 and 0.011, against 0.05. It passes either way.
7. **Header.** "Frozen and pushed (commit 73e856e) … after three blind reviews": **not verifiable here** (manifest,
   reviews and git withheld). PREREG §8 describes one blind review, a "targeted second look" and a "narrow third look".
8. **Header.** "A separate script … reproduces …": not verifiable here, because that recomputation is withheld. It is
   consistent with this audit, which reproduces the same items. This audit also reproduces run 1's R under M2 (0.977,
   0.963, 0.874, 0.858, 0.854), which the report says was not independently checked.
9. **Header.** "Every number below comes from RESULTS_GHZ3.json" is **not accurate**. The job, run and fetch times
   come from the execution-calibration file and the log. The log contrasts are computed. The gate flags and review
   counts come from withheld files.
10. **Kapı's part; Lessons.** The Truth_Gate flags and the review findings and counts are **not verifiable here**
    (certificates and reviews withheld).
11. **Opening paragraph; Conditions and controls.** "On a new calibration" and "the calibration in force at execution
    equalled the snapshot's … verified" are **incomplete**. Ages of the M2 inputs at execution:

    | Inputs | Dated | Note |
    |---|---|---|
    | cz, readout, T1, T2 | 2026-11-12 | 86–88 h before execution |
    | one-qubit gate errors | 2026-11-05 | unchanged since run 2 |
    | qubit 89's T1 | 2026-11-11 | identical to run 2's |
    | device last update | 2026-11-13 | — |

    The §3 check shows only that no recalibration happened after submission. It says nothing about whether the record
    was current.

### Interpretations that go beyond what the run can show

12. **"Both questions are therefore model tests."** True by the rule, but Q1's model-test status rests on one entry:
    qubit 89's readout error, 0.0044 → 0.0513. Without that change, max(|ΔF(4)|, |ΔF(8)|) = 0.006 and the replicate
    label would apply. At n = 4 the prediction moved by only 0.006.
13. **"The overprediction persisted, and on this day it was much larger at large n."** H4 shows that F was below the
    prediction at every n. It does not show that run 1/2's systematic bias persisted. The shape changed (R falls from
    0.96 to 0.53 instead of staying flat; H3 reversed). The large n are dominated by qubit 72, and the calibration was
    3.6 days old. K1–K3 cannot detect such faults (I-7).
14. **"The device's day-to-day change at large n was not visible in the calibration data."** A change after the
    2026-11-12 calibration cannot be in it by construction. The counts point to one qubit (72), not to a device-wide
    change.
15. **"H1 still fails at n = 8, because M2's level there is about 0.066 too high"** and the joint sentence "the bias
    persists and exceeds 0.05 at small n". The 0.016 exceedance, which is within drift, is plausibly qubit 89's error
    beyond its calibration. With that error in M2, |dev(8)| = 0.023–0.027, inside the band. n = 4 is inside the band
    too (0.037). The run does not show a small-n bias above 0.05.
16. **H1 reading "fails" (power 0.959) and H4 without a label.** The report omits two things:
    * Under the pre-registered drift × 2 sensitivity, H1's power is 0.742 < 0.8, which would give "not demonstrated".
    * σ_rel comes from two runs 25 minutes apart, while this calibration was 3.6 days old.

    In addition, H4 lacks "holds within drift" only because σ_rel,P was clipped to 0. With σ_rel,P = σ_rel,C, or at
    drift ≥ ×1.35, the label would apply.
17. **"The reach is a property of the device on the day."** F(16) = 0.490 falls below 0.5 mainly because of qubit
    72's excess error. The reach on this day is a property of one qubit of the fixed patch more than of the device.
18. **Lesson: "off by far more on another day … the large-n gap had more than doubled."** The doubling is correct, but
    one run cannot separate "another day" from a 3.6-day-old calibration record and two faulty qubits. The files more
    directly support a different lesson: check the calibration's age and the per-qubit error signatures at execution.
