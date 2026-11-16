# GHZ run 3: report

One pre-registered run on 2026-11-16, four days after run 2, on a changed calibration. Job `dbtecsfasvbs73b9l4e0`,
ibm_kingston, 368 circuits × 2000 shots, no mitigation. The job used 196 s of QPU time against an estimate of 186.5 s
and a stated quota of 234 s. It was created at 11:18:09 UTC, ran from 11:18:16 to 11:22:17, and was fetched at 11:23 UTC.

## Records and checks

- **Pre-registration.** `PREREG.md` v3 (`FREEZE_GHZ3.json` core `26F508A2D4B5B4FF`) was frozen and pushed (commit
  `73e856e`) before the submission. Before the freeze it went through three reviews by fresh agents: the first blind, the
  second and third given the earlier reviews (`../ghz_heron_run3_reviews/`).
- **Sources of the numbers.**
  - The verdicts, the readings and the tables come from `RESULTS_GHZ3.json`, written by the frozen `ghz3_analyze.py`.
  - The job times come from the job record and the fetch file.
  - Numbers computed here are marked as such.
- **Independent checks.**
  - A separate script, written without reading the analysis code or the results (`../ghz_heron_run3_recompute/`),
    reproduces the point values, the four verdicts, C-1, K1 and the GME crossing.
  - The blind post-run audit (section "Post-run audit") recomputed the same items, plus the power file, K2, the drift
    labels and run 1's R under M2. Its numbers agree.

## Conditions and controls

- **C-1 (new calibration for M2) held**, by the pre-registered rule.
  - Four of the eight M2 inputs of the patch had changed since run 2: two-qubit gate errors, readout errors, T1 and T2.
  - The largest change in M2's predictions was 0.059, at n = 8, so Q1 also counted as a model test by its own small-n
    threshold.
  - *Found after the run (audit A1, checked by the designer):* that n = 8 change comes from one entry, qubit 89's
    readout error (0.0044 in run 2, 0.0513 here). With run 2's value for that entry, F_pred(8) = 0.8911 against run 2's
    0.8879, a change of +0.003, and Q1 would have carried the replicate label. At n = 4 the prediction moved by +0.006.
- **C-2 (quota) held:** 1.15 × 186.5 s = 214.5 s ≤ 234 s.
- **Calibration at execution.** For all M2 inputs it equalled the snapshot's, checked against the calibration history
  at the execution start. This shows that no recalibration happened after the submission. It does not show that the
  record was current. *Found after the run:* the M2 inputs were 86–88 h old at execution (mostly dated 2026-11-12; the
  one-qubit gate errors 2026-11-05; qubit 89's T1 2026-11-11, unchanged since run 2).
- **Controls K1, K2 and K3 passed.**
  - K1: the 97.5th percentile of C_mix was 0.029 and 0.011, against a limit of 0.05.
  - K2: passed on the submitted circuits.
  - K3: the power file recomputes equal, the log prefix is unchanged, and the job was created after the submission
    time.

  None of these controls can detect a qubit whose readout or relaxation error is far above its calibration (audit A4).
- **Stopping rule:** one attempt, accepted, no dry run; no deviation in the log.

## Pre-registered answer (assembled mechanically, PREREG §4)

| | Verdict | Reading | Deciding numbers |
|---|---|---|---|
| H1: M2 accurate within 0.05 for 4 and 8 qubits | **FAILS** | "fails" (power at submission 0.959) | \|ΔF\| = 0.037 at n = 4, **0.066** at n = 8 |
| H4: M2 overpredicts F at every n | **HOLDS** | – | 97.5th percentile of F_boot/F_pred below 1 at every n; the largest is 0.970, at n = 4 (margin 0.030) |

> Q1: on this run's calibration M2 is not accurate within 0.05 for 4 or 8 qubits. Q2: on a new calibration M2 still
> overpredicts the fidelity at every n. Together: the bias persists and exceeds 0.05 at small n.
>
> Label: **within drift (H1)**: at n = 8 the deviation exceeds the band by 0.016, less than 2σ_d,F = 0.017. Only n = 8
> exceeds the band; n = 4 is inside it.

These are the pre-registered readings and they stand. Two robustness facts limit them (*post hoc*, audit A2 and A5,
checked against `run/power_run3.json`):
- **The drift scale is from two runs 25 minutes apart, on one calibration.** This run's calibration record was 3.6 days
  old. Under the pre-registered sensitivity row "drift × 2", the power of H1 is 0.742, below 0.8, and its FAILS would read
  "not demonstrated".
- **H4 carries no "within drift" label only because σ_rel,P was clipped to 0**: its pooled estimate was negative. With
  σ_rel,P = σ_rel,C, or at drift × 1.35 or more, the n = 4 margin would fall below 2σ_d,R, and H4 would read "holds within
  drift".

Reported, not confirmatory:
- **H2 FAILS.** The measured reach is n = 8, against a predicted 24.
- **H3 FAILS.** At n = 32 and 48, P is short of its prediction *less* than C is. The point log contrasts
  ln(P/P_pred) − ln(C/C_pred), from the table's values, are +0.157 and +0.179.

| n | F | 95% CI (shot noise) | F_pred (M2) | R = F/F_pred | F run 2 | R run 2 | R run 1 (M2) |
|---|---|---|---|---|---|---|---|
| 4 | 0.906 | 0.897–0.914 | 0.942 | 0.961 | 0.892 | 0.952 | 0.977 |
| 8 | 0.762 | 0.752–0.772 | 0.829 | 0.920 | 0.833 | 0.938 | 0.963 |
| 16 | 0.490 | 0.478–0.502 | 0.655 | 0.749 | 0.613 | 0.879 | 0.874 |
| 24 | 0.363 | 0.352–0.374 | 0.565 | 0.642 | 0.509 | 0.864 | – |
| 32 | 0.278 | 0.266–0.289 | 0.426 | 0.651 | 0.384 | 0.851 | 0.858 |
| 48 | 0.163 | 0.153–0.172 | 0.305 | 0.534 | 0.243 | 0.844 | 0.854 |

## How to read it (interpretation, written after the run and corrected after the audit)

**Most of the shortfall comes from two qubits of the fixed patch.** The run's own POP counts show this (audit A1 and A3;
the designer recomputed the rates):

| Qubit | Where | Error at execution | Calibration | Run 2 |
|---|---|---|---|---|
| 89 (in every n ≥ 8) | every GHZ and MIX population circuit | reads 0 for 1 in 15–18% of shots | symmetric readout error 0.051 | 1–3% |
| 72 (in every n ≥ 16) | n ≥ 16 | reads 1 for 0 in 21–32% of shots; the rate varies between circuits run minutes apart | 0.041 | 1–5% |

The run cannot tell whether the cause was a defect, leakage or readout drift on these qubits.
- **Q1 (H1).** The n = 8 failure is within drift and plausibly qubit 89's error beyond its calibration. Putting the
  observed error of qubit 89 into M2 gives |F_hat(8) − F_pred(8)| ≈ 0.023–0.027, inside the band (the audit's
  computation). The run does not show a small-n bias of M2 above 0.05 for the patch as a whole.
- **Q2 (H4).** F was below M2's prediction at every n on this calibration. This is what H4 says (I-7), and it names no
  cause.
  - The run does not show that the flat bias of runs 1 and 2 persisted. The shape changed: R falls from 0.96 at n = 4 to
    0.53 at n = 48, where runs 1 and 2 had about 0.85 for n ≥ 16.
  - The large-n shortfall is dominated by qubit 72.
- **Large n.** F(16), F(32) and F(48) fell by 0.12, 0.11 and 0.08 from run 2. M2, fed with the changed calibration,
  predicted changes of −0.042, −0.025 and +0.017. The predicted change lies outside the 95% CI of the measured change at
  every n ≥ 16.
  - A calibration record dated 3.6 days before the run cannot contain a change after it.
  - The counts point to one qubit (72), not to a device-wide change.
- **At small n** the predicted changes (+0.006, −0.059) lie inside the CIs of the measured changes (+0.014, −0.071).
  The n = 8 prediction change itself comes from qubit 89's readout entry.
- **H3's direction reversed** (C short more than P at n = 32 and 48). Readout error beyond the model gives this
  direction (PREREG §4). Qubits 72 and 89 are such errors.
- **GME without mitigation on this day.**
  - The CI-based reach fell from 16 (runs 1 and 2) to 8.
  - The interpolated crossing of F = 0.5 moved from 23.9 (run 1) and 24.6 (run 2) to 15.7 (95% CI 15.4–16.1).
  - F(16) = 0.490 falls just below 0.5, mainly because of qubit 72. On this day the reach is a property of one qubit of
    the fixed patch more than of the device.

The run cannot separate three explanations: a different day, a calibration record 3.6 days old, and two faulty qubits.
It is one model test on one calibration (I-5).

## Deviations and limits

- **Deviation from the run plan (§8, step 3).** `run/job.json` and the log were to be pushed right after the submission,
  before the data were fetched. The data were fetched first; both are published with this report.
  - The service records the job's identity and creation time. K3 checked that the job was created after the submission.
  - The hashes inside `job.json` do not replace the public push: `job.json` and the log were local files until now.
    Third parties cannot verify that the log was complete before the data (for example that no refused attempt or dry
    run is missing).
  - The run plan relied on a manual step at the moment of most interest; the code did not enforce it.
- **A pre-run test now fails because of this report.** `tests_ghz3.py`, "every file of the folder is listed", allows
  the results files but not `REPORT.md`, which was written after the run into the frozen folder. The binding freeze check
  (`FREEZE_GHZ3.json`, 14 files) passes.
- One calibration and one day give one model test, not a rate (I-5). Runs 1, 2 and 3 are not pooled (I-4).

## Kapı's part

- Truth_Gate raised no actionable flag on H1–H4 before the freeze. The only flags were the rejected
  `K5_INCONCLUSIVE:noise` and `K5_INCONCLUSIVE:zeros`: the criteria abstain on the probes by their own domain rule.
- The decisive defects of the design were found by the reviews before the freeze:
  - power misread;
  - a new-calibration condition that did not guarantee a model test;
  - forking paths at submission;
  - no verdict mapping;
  - no check of the calibration at execution.

  The decisive facts of the result were found by the post-run audit: two faulty qubits and the age of the calibration.
  All of these lie outside Kapı's scope, as in the earlier cases.

## Post-run audit (fresh agent, blind to earlier reviews and to this report until its own audit was written)

The auditor worked on copies without the certificates, the revision log, the freeze manifests, the earlier audits and
the recomputation. It recomputed everything listed above. Its findings (`../ghz_heron_run3_reviews/postrun/`):
- **High.**
  - A1: Q1's model-test status and the H1 failure rest on qubit 89.
  - A2: the drift scale omits calibration age; the "fails" reading is not robust to the pre-registered drift × 2 row.
- **Medium.**
  - A3: qubit 72 dominates n ≥ 16, H2 and H3.
  - A4: H4 cannot show that the earlier bias persisted, and K1–K3 cannot detect such qubit faults.
  - A5: H4's missing drift label depends on the clipped σ_rel,P.
  - A6: the joint sentence must be read with its label and as "n = 8 only".
- **Low.** Clarity points: the meaning of "verified", the summary of the log, what K2 checks, and the paired bootstrap
  in the tracking table (no change).

None found a misapplied rule. The auditor also listed 18 points in the first version of this report. The designer
checked each and corrected the report. The main corrections:
- the anchoring of the submission record;
- the stated cause of the freeze-list test failure;
- the GME comparison (crossing against crossing);
- the K1 numbers;
- a rounding;
- the interpretation, which now names the two qubits and the calibration age instead of a device-wide change;
- "every number from RESULTS".

## Lessons for the protocol

- **A step meant to precede the data must be enforced by the code.** For example, `--fetch` could refuse until the
  submission record is published.
- **A model test must check the calibration record, not only that it did not change after submission.** Record its age
  at execution. Pre-register per-qubit error signatures from the population circuits (the flip rates of each qubit when
  the rest read all 0 or all 1) as a reported diagnostic, or as a control against the calibration. They cost nothing
  extra and would have flagged qubits 89 and 72.
- **A minimum change in the predictions can be met by a single input.** C-1 here rested on one readout entry. A
  condition meant to ensure "a broadly new calibration" should say how many inputs must carry the change.
- **Reviews before a freeze pay off when the design is new.** The first review found 2 blocking and 8 major defects, the
  second 4 major, the third only minor ones. A post-run audit is still needed: it found what the reviews could not, the
  state of the device on the day.
