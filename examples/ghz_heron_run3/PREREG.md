# GHZ on Heron r2, run 3: the frozen run-2 design on a new calibration

Status: **pre-registration v3 (2026-11-16), frozen in `FREEZE_GHZ3.json`.** It was revised after a blind pre-freeze
review, a second look and a third look; the revisions and their reasons are in `REVISIONS.md`. No circuit of this run
had been executed when it was frozen. After the freeze, nothing below changes.
Designer: Claude, under the author's delegation. Hardware run: the author's account, submitted with the author's approval.

## 0. Why this run exists (known vs prospective)

- **Run 2 was a data replicate, not a model test** (`../ghz_heron_run2/REPORT.md`). The device had not been
  recalibrated since run 1, so model M2 made the same predictions that had already been compared with run 1's data.
  Protocol rule 2 (extended after run 2): a replicate on the same calibration tests the data, not the model.
- **This run is the model test.** M2, with its formula and code unchanged, is evaluated against data taken under a
  calibration whose M2 inputs and predictions differ from run 2's by a pre-registered minimum (C-1, §1). "Model test" in
  this text means exactly that. For Q1 (small n) the minimum is applied at n = 4 and 8; if it is not met there, the Q1
  answer is labelled a replicate (§1).
- **Known from runs 1 and 2 (NOT evidence for this run):**
  - M2 overpredicts F at every n: R = F_meas/F_pred = 0.95, 0.94, 0.88, 0.86, 0.85, 0.84 in run 2 (n = 4 … 48). On run 1's
    data, recomputed with the frozen code, R = 0.977, 0.963, 0.874, 0.858, 0.854 (n = 4 … 48, no n = 24). The gap is
    roughly flat for n ≥ 16.
  - GME without mitigation: 16 qubits with confidence, 24 at the threshold on point values.
  - P fell short of its prediction more than C at n = 32 and 48 in all four cells of the two runs. H3 was underpowered,
    so this is not demonstrated.
  - Between runs 1 and 2, F moved by about −0.022 at n = 4 and 8 (C by about −0.03), several shot-noise σ, while n ≥ 16
    agreed within 0.004 (rule 9, extended: the noise ceiling includes run-to-run drift).
- **Prospective questions.**
  - Q1: is M2 accurate for small states on a new calibration (H1)?
  - Q2: does M2's overprediction persist at every n on a new calibration (H4)?
  - Reported, not confirmatory: the GME reach (H2) and the population-specific shortfall (H3).

## 1. Design (Claude, delegated): run 2's, unchanged, plus conditions before submission

- **D-1 to D-6 as in run 2** (`../ghz_heron_run2/PREREG.md` §1):
  - least busy operational Heron r2, with the snapshot saved and hashed before submission;
  - the same error-blind qubit selection;
  - the same circuits and transpiler options (dynamical decoupling off, twirling off, optimization_level 1,
    seed_transpiler 20261112);
  - grid n ∈ {4, 8, 16, 24, 32, 48}, 2000 shots;
  - measurements POP_n and PAR_n,j;
  - controls MIX_8 and MIX_32.
- **Code identity.** `ghz2_core.py` and `ghz2_study.py` are copied byte for byte from run 2. Their SHA-256 must equal the
  values in `../ghz_heron_run2/FREEZE_GHZ2.json` (checked by the tests and before every hardware step).
- **D-7 budget:** 368 circuits, 736000 shots, as in run 2 (which used 196 s of QPU time); the 300 s ceiling stays.
- **C-1 New calibration for M2.** The M2 inputs are, for the selected 48-qubit set S_48 and its tree: the qubit list, the
  two-qubit and one-qubit gate errors (`cz_err`, `g1_pop_err`, `g1_par_err`), the readout errors (`ro_err`), T1, T2 and
  the idle times (`idle`). These are the n = 48 components of `model.json`, which contain every smaller n.
  C-1 holds when both of the following are true:
  - (a) the device differs from run 2's, or at least one M2 input differs from run 2's (`../ghz_heron_run2/run/model.json`);
  - (b) max over n of |F_pred,run3(n) − F_pred,run2(n)| ≥ 0.02. The threshold 0.02 is several times the shot-noise sd of
    F and close to the run-1/run-2 drift at small n (0.022), so a test of the new predictions is not a test of the old
    ones.
  - **Per question.** Q2 (H4, all n) is a model test whenever C-1 holds. Q1 (H1, n = 4 and 8) is a model test only if
    max(|ΔF_pred(4)|, |ΔF_pred(8)|) ≥ 0.02, computed on the snapshot's predictions. Otherwise the Q1 answer carries
    the fixed label "small-n predictions within 0.02 of run 2's: for Q1 this run is not a model test of new
    predictions".

  The comparison is saved in `run/calibration_check.json` (inputs changed, ΔF_pred per n, the threshold, and the SHA-256
  of run 2's snapshot and model files). If C-1 fails, the run is not submitted; it may be retried after a later
  calibration (see the stopping rule).
- **C-2 Quota.** The author reads the remaining QPU time on the IBM Quantum dashboard and passes it in seconds
  (`--quota-seconds N`). The run is submitted only if 1.15 × the estimate computed at submission ≤ N; run 2's actual
  time was about 1.05 × its estimate. No execution-time limit is set on the job, because a job cut short is a K3 failure
  (yorumlanamaz) and the margin is the guard. N is saved in `run/job.json`.
- **Rule-14 check on the new snapshot.** At submission, F_pred + 0.05 < 1 is checked at n = 4 and 8 and saved in
  `run/calibration_check.json`. The analysis rechecks it on the snapshot's predictions and, if they differ (§3), on the
  predictions in use. If either check fails, H1 is reported as one-sided.
- **Stopping rule.**
  - The first `--submit` that passes D-7, K2, C-1 and C-2 is the run.
  - An *attempt* is a `--submit` that reaches these checks. Refusals for a missing freeze, invalid code identity, a
    missing or invalid quota, or an existing `job.json` are not attempts, and neither are failures before the checks
    (backend selection, circuit build).
  - At most one attempt per UTC day may be refused. Any further attempt on the same UTC day after a refused attempt is
    a deviation, whether it passes or not.
  - `--dry-run` is optional. It prints the pass/fail of D-7, K2, C-1 and C-2 and the time estimate, but no prediction.
    **A passing `--dry-run` is binding:** a dry-run passes when D-7, K2 and C-1 pass, whatever C-2 says. A passing
    `--submit` must follow within 2 hours, measured from the dry-run's snapshot time to the submit's snapshot time. A
    passing dry-run without such a submit is a deviation. Every logged line whose C-1 passed but whose C-2 failed is
    reported, with the quota given.
  - Every `--dry-run` and every `--submit` that reaches the checks appends a line to `run/dryrun_log.jsonl`. The line
    holds the UTC time, snapshot time, backend, snapshot hash, the D-7, K2, C-1 and C-2 results, the refusal reason and
    the SHA-256 of the predictions; the predictions themselves are not written. A `--submit` that passes the checks
    appends a "checks passed" line at once, before anything else, so an interrupted passing attempt is recorded. Each
    `--fetch` attempt also appends a line (file name and SHA-256 of its saved calibration).
  - At submission, `run/job.json` records the SHA-256 and the line count of the log. The analysis checks that the log
    up to that line is unchanged and reports the whole log with every deviation (as defined here). The code does not
    enforce the timing; it records it.
- **Power at submission.** Before the job is submitted, `--submit` computes the power file `run/power_run3.json` from
  the new snapshot's predictions with the method of §4 and records its SHA-256 in `run/job.json`. Nothing of it is
  printed before submission.
- **Atomic writes.** The snapshot, `circuits.qpy`, `model.json`, `calibration_check.json` and `power_run3.json` are
  written to a temporary folder and moved into `run/` only after the job id is returned. If the submission raises (or
  is interrupted), the temporary folder is kept, renamed with the attempt time, and the failure is logged (exit 8, or
  the interrupt is re-raised after logging). Before any retry, the author checks the account's job list for a job
  created at that attempt. If one exists, it is the run, and `--recover JOBID` writes `run/job.json` from the kept
  folder; no second job is submitted. `--recover` refuses unless the service confirms that the job's backend equals the
  attempt's, that it was created no earlier than 10 minutes before the attempt's snapshot time (clock difference) and
  before the logged failure plus 10 minutes, and that it has 368 circuits.
- **Calibration dates.** At submission, `run/calibration_check.json` also records the calibration dates of every M2 input
  of S_48 (from the backend's calibration properties at that time); they are used in §3.

## 2. Estimators

As in run 2, with unchanged code: P, C (with |·|) and F = (P + C)/2; joint multinomial bootstrap, B = 2000, seed
20261113, returning replicates of P, C and F per n.

## 3. Model M2 and the calibration in force at execution

- M2 is as in run 2, unchanged (`../ghz_heron_run2/PREREG.md` §3): P_pred, C_pred and F_pred computed from the
  calibration's `Target`. The reference arm is run 1's model M (F_M, reported, not a criterion).
- **Execution-time calibration.** `--fetch` saves the job's execution timestamps and usage, and the backend's calibration
  at the start of execution (the calibration history queried at that time). The analysis recomputes the M2 inputs of
  S_48 from it, with the durations and schedule of the submitted circuits. "Equal" means equal within a relative
  tolerance of 1e-6 per value; a recalibration changes values by far more.
  - The history result is accepted only if every M2-input calibration date in it is at or before the execution start.
    Otherwise it is treated as unavailable.
  - If the accepted execution-time inputs equal the snapshot's, the snapshot's predictions are used.
  - If they differ, and every differing input carries a later calibration date than at submission, the primary
    predictions are M2 on the execution-time calibration (labelled "calibration changed before execution"); the
    snapshot's predictions are reported as secondary. A difference without a later date is labelled "execution-time
    calibration not verified", and the snapshot's predictions are used.
  - `--fetch` never overwrites a saved execution calibration: every fetch attempt is kept with its time, and the first is
    used.
  - If the history query is not available, or its result cannot be accepted or used, the saved current calibration
    (which `--fetch` always records, with its calibration dates) is checked instead.
    If every M2 input of S_48 in it was calibrated before the submission time and equals the snapshot's input, the
    snapshot's predictions are used, labelled "verified: no recalibration since submission". The author runs `--fetch`
    soon after the job finishes so that this check can apply.
  - Otherwise the snapshot's predictions are used, labelled "execution-time calibration not verified".

  This rule is fixed now and applied mechanically; the M2 formula is the same in every case.

## 4. Criteria, power and readings

**Data given to the criteria:** as in run 2, six columns in GRID order: `F_pred`, `P_pred`, `C_pred`, `F_hat`, `P_hat`,
`C_hat` (each (6,)) and `F_boot`, `P_boot`, `C_boot` (each (B, 6)).

| id | Role | Claim | HOLDS | FAILS | UNDEFINED |
|---|---|---|---|---|---|
| H1 | confirmatory | M2 is accurate for small states | \|F_hat(n) − F_pred(n)\| ≤ 0.05 for n = 4 and 8 | otherwise | F_pred at n = 4 or 8 outside (0, 1) |
| H4 | confirmatory | M2 overpredicts F on a new calibration | for every n in GRID: the 97.5th percentile of F_boot(n)/F_pred(n) < 1 | otherwise | any F_pred outside (0, 1), or any F_boot ≤ 0 |
| H2 | reported | M2 predicts the GME reach | n_meas = n_pred (point values) | otherwise | n_pred = 0, or any F_pred outside (0, 1) |
| H3 | reported (exploratory) | The shortfall is population-specific | for n = 32 and 48: the 97.5th percentile of ln(P_boot/P_pred) − ln(C_boot/C_pred) < 0 | otherwise | any involved replicate or prediction ≤ 0 |

- H1–H3 are the functions of `ghz2_study.py`, imported unchanged. H4 is in `ghz3_study_h4.py`.
- **Why H2 and H3 are not confirmatory.**
  - H2's outcome is set mostly by where F_pred(24) of the new snapshot falls relative to about 0.58, which is known
    before the data. It is reported with the CI-based reach and the interpolated crossing with its CI.
  - H3 is underpowered at this shot count (§4, power). Error classes that produce its direction (P short more than C):
    T1 beyond the model, leakage, X-type (bit-flip) gate errors, and correlated readout flips that break the all-0 or
    all-1 pattern. Error classes that produce the opposite direction: Z-type (dephasing) gate errors, T2 beyond the
    model, and independent symmetric readout error beyond the model (it lowers C about twice as much as P). Gate errors
    that scale P and C alike produce neither. H3 is reported as exploratory.
- **H4 attributes no cause** (I-7). It holds whenever M2 underestimates the error on this calibration; its only safeguard
  against a broken experiment is K1–K3. Both directions are reachable (rule 14).
- **Drift.**
  - σ_rel,X: the relative between-run drift of X ∈ {P, C}, pooled over n from runs 1 and 2 and corrected for shot noise:
    σ²_rel,X = mean over n of [ln(X_run1(n)/X_run2(n))²/2 − v_X(n)], where v_X(n) is the relative shot variance from
    run 2's bootstrap. A negative value counts as 0.
  - σ_d,F(n) = ½ · sqrt((P_pred(n)·σ_rel,P)² + (C_pred(n)·σ_rel,C)²) on the predictions in use.
  - In ratio units, σ_d,R(n) = σ_d,F(n)/F_pred(n).
- **Power (rule 16), computed at submission** (`run/power_run3.json`) from the new predictions, with 2000 simulated
  datasets and seed 20261116.
  - Each simulated dataset takes the truth stated below, multiplies P and C by exp(σ_rel,X · z) with z drawn
    independently per n and component, and adds one centred row of run 2's bootstrap as shot noise. Its replicates are
    the point estimate plus all centred bootstrap rows.
  - Power of H1: P(H1 HOLDS) when the truth is P_pred − 0.03 and C_pred − 0.03 at n = 4 and 8 (so F_true = F_pred −
    0.03, inside the band), and keeps run 2's ratios elsewhere.
  - Power of H4: P(H4 HOLDS) when the truth keeps run 2's ratios to the prediction (P_true = P_pred · P_run2/P_pred,run2,
    and C likewise).
  - Expected outcome, reported separately, not power: P(HOLDS), P(FAILS) and P(UNDEFINED) of H1–H4 when the truth keeps
    run 2's ratios.
  - Sensitivity rows: drift fully correlated across n (one z per component), and drift × 2.
  - On a device change (I-6) the computation is the same, with that device's predictions, and is labelled so.
  - `certs/power.json`, computed before the freeze on run 2's snapshot as a stand-in, records the design-time values with
    the same method. It is not used to read the result.
  - The readings use the power at submission, computed on the snapshot's predictions, in every case of §3.
  - The analysis recomputes the power at submission from the snapshot's predictions (the method is deterministic) and
    requires equality with `run/power_run3.json`.
  - `run/power_run3.json` and `run/job.json` record the Python, numpy, scipy and qiskit versions and the platform. The
    analysis runs in the same environment. A version mismatch is reported as the cause if the recomputation differs.
- **Readings fixed now.**
  - A FAILS of a confirmatory criterion reads "fails" if its power at submission is ≥ 0.8, and "not demonstrated" if it
    is below 0.8.
  - "Within drift" labels; a label is attached to the verdict and never changes it:
    - H1: within drift when ||F_hat(n) − F_pred(n)| − 0.05| < 2 σ_d,F(n) at the n that decides the verdict (the n with
      the larger deviation).
    - H4 HOLDS: "holds within drift" when 1 − q97.5(n) < 2 σ_d,R(n) at some n (each n compared with its own σ_d,R(n)).
    - H4 FAILS: "fails within drift" when q97.5(n) − 1 < 2 σ_d,R(n) at every n where q97.5(n) ≥ 1.
  - The margins 1 − q97.5(n) are reported per n next to σ_d,R(n).

**Answers to Q1 and Q2 (verdict mapping, rule 3).** If a control fails (§5), the answer is "yorumlanamaz", whatever the
criteria say. Otherwise the answer is assembled mechanically:
1. the Q1 sentence for H1's outcome and reading;
2. the Q2 sentence for H4's outcome and reading;
3. the joint sentence when both are definite;
4. the labels.

| H1 outcome (reading) | Q1 sentence |
|---|---|
| HOLDS | Q1: on this run's calibration M2 is accurate within 0.05 for 4 and 8 qubits. |
| FAILS ("fails") | Q1: on this run's calibration M2 is not accurate within 0.05 for 4 or 8 qubits. |
| FAILS ("not demonstrated") | Q1: M2's accuracy within 0.05 for 4 and 8 qubits is not demonstrated (H1 failed with power below 0.8). |
| UNDEFINED | Q1 is not answered. |

| H4 outcome (reading) | Q2 sentence |
|---|---|
| HOLDS | Q2: on a new calibration M2 still overpredicts the fidelity at every n. |
| FAILS ("fails") | Q2: on a new calibration M2 does not overpredict at every n; the run-1/2 overprediction did not persist everywhere. |
| FAILS ("not demonstrated") | Q2: persistence of the overprediction at every n is not demonstrated (H4 failed with power below 0.8). |
| UNDEFINED | Q2 is not answered. |

| H1 | H4 | Joint sentence (only these four combinations) |
|---|---|---|
| HOLDS | HOLDS | Together: a small systematic bias. |
| HOLDS | FAILS ("fails") | Together: M2 is accurate at small n and does not overpredict everywhere. |
| FAILS ("fails") | HOLDS | Together: the bias persists and exceeds 0.05 at small n. |
| FAILS ("fails") | FAILS ("fails") | Together: M2 misses the small-n band and does not overpredict at every n. |

Labels, attached when they apply:
* "within drift" (H1 or H4);
* "H1 one-sided" (rule-14 check);
* the Q1 replicate label (§1, C-1 per question);
* "device change" (I-6);
* "calibration changed before execution" or "execution-time calibration not verified" (§3).

**Headline (reported):**
- n_meas and the fidelity table with P, C, F, their CIs, the predictions in use, R and F_M;
- R(n) of runs 1, 2 and 3 side by side (descriptive);
- **tracking:** per n, the measured change F_run3 − F_run2 with its CI (shot noise only, labelled so) and σ_d,F(n) next
  to it, against the predicted change F_pred,run3 − F_pred,run2 (descriptive);
- the C-1 comparison and the dry-run log;
- H2 with the CI-based reach and the interpolated crossing, and H3 (exploratory);
- C computed with Re instead of |·| (sensitivity I-1).

## 5. Controls (all must pass, else "yorumlanamaz")

- **K1:** for MIX_8 and MIX_32, the 97.5th percentile of the C_mix bootstrap is ≤ 0.05 (as in run 2).
- **K2 (simulator):** noiseless MPS simulation of the transpiled circuits, F_sim ≥ 0.98 for every n, and C_mix,sim ≤
  0.05. It runs three times:
  - before the freeze on FakeKingston's circuits (`certs/k2_sim.json`, a design check);
  - in `--dry-run` and `--submit` on the circuits about to be submitted, where a failure refuses the attempt like D-7;
  - in the analysis on the submitted circuits (`run/circuits.qpy`), which is the binding K2.

  A missing or unreadable result counts as a K2 failure. The
  bit-order control is reported, not part of K2's pass condition: P and C are invariant under bit permutations (run 2
  report).
- **K3 (integrity):** as in run 2 (n − 1 two-qubit gates per circuit; snapshot saved and hashed; freeze verified; job id
  and counts saved; count totals equal shots; M2 recomputed from the snapshot equals the saved model). Additions:
  - the SHA-256 of `ghz2_core.py` and `ghz2_study.py` equals run 2's frozen values;
  - C-1 recomputed in the analysis with the rule of §1 holds;
  - the run-2 snapshot and model hashes recorded in `run/calibration_check.json` equal the known values;
  - `run/power_run3.json` exists and its SHA-256 equals the one in `run/job.json`.
  - Its input hashes equal those in the frozen `certs/power.json` (for the run-1 and run-2 data files) and in
    `FREEZE_GHZ3.json` (for the study files).
  - Recomputing it gives the same numbers (§4).
  - A missing or mismatched power file is a K3 failure.
  - The log prefix recorded in `run/job.json` is unchanged (§1). A later line whose UTC time is earlier than the
    submission is a K3 failure. The deviation report uses the anchored lines plus the accepted line.
  - The job was created, and started running, at or after the submission time in `run/job.json`, allowing 10 minutes
    for a difference between the local clock and the service's (run 2's job, the nearest wrong one, is days older).
  - The execution calibration used is the first logged `--fetch` attempt; its file exists and its SHA-256 matches the
    log.

## 6. Interpretations and sensitivity (rule 4)

- **I-1 to I-3** as in run 2: C with |·|, Re as sensitivity; symmetric readout error; one day, one patch, one device.
- **I-4:** runs 1, 2 and 3 are not pooled. Each is reported on its own; the side-by-side and tracking tables are
  descriptive.
- **I-5:** one new calibration gives one model test, not a rate. A verdict says what M2 did on this calibration.
- **I-6:** if the least busy Heron r2 is not ibm_kingston, the test also spans a device change, labelled as such.
- **I-7:** H4 HOLDS means "M2 underestimates the error on this calibration". It names no cause, and an experiment fault
  would push in the same direction; K1–K3 are the safeguards.

## 7. Kapı study

- `ghz2_study.py` (H1–H3, unchanged): its certificate is produced again with Truth_Gate 0.5.0 (`certs/cert_h123_v1.json`).
- `ghz3_study_h4.py` (H4): imports only numpy and truth_gate.
  - The worlds follow the schema of §4: `plus` has M2 too high by a run-2-like ratio, `minus` has M2 accurate.
  - The control `accurate_small_n_too_high_large_n` models a plausible real failure.
- The probes (noise, zeros) replace F_pred, so H4 abstains on them by its own rule. The gate therefore could not test H4
  for vacuity on the probes; the worlds and the control do (REVISIONS).
- The analysis imports H1–H4 unchanged.

## 8. Run plan

1. Implement offline (FakeKingston): wrappers, C-1, C-2, the rule-14 check, the stopping-rule log, power at submission,
   atomic writes, the execution-time calibration, the H4 study, the tests, D4 and K2. Done; the changes after each
   review are in `REVISIONS.md`.
2. Produce the Kapı certificates. A blind pre-freeze review (of v1), a targeted second look (of v2) and a narrow third
   look (of v3) were done; their findings and the responses are in `REVISIONS.md`. Then the freeze: every file of this
   folder is listed in `FREEZE_GHZ3.json`. Push the frozen pre-registration with the author's approval, before any
   submission.
3. The author runs `--submit --quota-seconds N` (optionally `--dry-run` first, which is then binding), following the
   stopping rule. Right after the submission, `run/job.json` and `run/dryrun_log.jsonl` are pushed to the public
   repository with the author's approval, so that the record of the submission is public before the data are.
4. `--fetch`, analysis, independent recomputation, blind audit by a fresh agent, report.
