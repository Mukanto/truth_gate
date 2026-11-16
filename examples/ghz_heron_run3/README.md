# GHZ fidelity on Heron r2, run 3: the frozen run-2 design on a new calibration

The binding specification is [`PREREG.md`](PREREG.md) (v3). Run 2 (`../ghz_heron_run2/`, frozen, read-only) is the design; run 1
(`../ghz_heron/`, frozen) is read only by the power computation and the R table. This folder holds the code. Nothing here was run
on hardware before the freeze; the simulator was used only for the D4 smoke test and control K2, and run 1 and run 2 files were
used for the power computation. The analysis needs `../ghz_heron/` and `../ghz_heron_run2/` beside this folder.

## What is new compared with run 2

| Item | Run 2 | Run 3 (PREREG v3) |
|---|---|---|
| Question | does M2 hold on new data (the calibration had not changed) | does M2 hold on a **new calibration** (Q1: small-n accuracy, H1; Q2: overprediction at every n, H4) |
| Design (circuits, grid, 2000 shots, 368 circuits, 736000 shots, transpiler options) | as in `../ghz_heron_run2/PREREG.md` | **unchanged**; `ghz2_core.py` and `ghz2_study.py` are copied byte for byte |
| **C-1** | none | submit only if (a) the device differs or an M2 input of S_48 differs from run 2's `model.json`, **and** (b) max over n of abs(F_pred,run3 - F_pred,run2) >= 0.02. **Per question:** Q1 is a model test only if max(abs dF(4), abs dF(8)) >= 0.02 on the snapshot's predictions, else the answer carries the fixed label "small-n predictions within 0.02 of run 2's: for Q1 this run is not a model test of new predictions" (the Q1 sentences say "on this run's calibration") |
| **C-2** | the 300 s ceiling only | `--submit` needs `--quota-seconds N`; refused unless 1.15 x estimate <= N and estimate <= 300 s; N saved in `run/job.json` |
| Rule-14 check | on FakeKingston only | at submission on the new snapshot (F_pred + 0.05 < 1 at n = 4, 8), saved in `run/calibration_check.json`, rechecked in the analysis ("H1 one-sided" label) |
| Stopping rule | none | attempts (one `--submit` invocation that reached the checks), one refused attempt per UTC day (day of the snapshot), a `--dry-run` is **binding when D-7, K2 and C-1 pass, whatever C-2 says** (a passing `--submit` must follow within 2 h, measured between snapshot times); `--dry-run` prints only pass/fail and the time estimate; every dry run, submit and fetch appends a line to `run/dryrun_log.jsonl` that holds the SHA-256 of the predictions, never the predictions, and the snapshot time; a `--submit` that passes the checks appends a `submit-checks-passed` line at once, before the power computation; `job.json` anchors the log (line count and SHA-256); the analysis checks the prefix and that later lines are not dated before the submission, applies the rule to the anchored lines plus the accepted line, and lists every logged line with C-1 passed and C-2 failed with its quota |
| Power | none | `run/power_run3.json` computed by `--submit` from the new predictions before submitting (nothing printed; SHA-256 in `job.json`); the analysis recomputes it and checks its input hashes against the frozen `certs/power.json` and `FREEZE_GHZ3.json`; `certs/power.json` is the design-time stand-in on run 2's snapshot, same function |
| Atomic writes | files written, then submitted | the files go to a temporary folder next to `run/` and are moved into `run/` only after the job id is returned; if the submission raises (or is interrupted) the folder is **kept** as `attempt_<utc>`, the failure is logged (exit 8) and `--recover JOBID` completes `run/` if the job exists |
| Calibration in force | the snapshot was assumed | `--submit` records the calibration dates of every M2 input of S_48; `--fetch` saves the execution timestamps, usage, the history result with its dates and the current calibration with its dates, every attempt in its own file (`run/execution_calibration_<utc>.json`) and logs it (file name and SHA-256); the analysis uses the first **logged** fetch (its file and hash are a K3 item), accepts a history result only if its dates are at or before the execution start, calls a difference "changed" only if every differing input has a later date than at submission (PREREG section 3) |
| Criteria | H1, H2, H3 | confirmatory **H1, H4** (H4 in `ghz3_study_h4.py`); reported H2 (CI reach, interpolated crossing with CI) and H3 (exploratory); drift quantities, "within drift" labels, power readings |
| Answer | none | assembled mechanically from pre-written sentences: Q1 sentence, Q2 sentence, a joint sentence for four combinations, then the labels; "yorumlanamaz" if a control fails |
| K2 | bit-order control inside the pass condition; FakeKingston circuits | runs three times: the design check on FakeKingston's circuits (`certs/k2_sim.json`), **on the circuits about to be submitted in `--dry-run` and `--submit`** (a failure refuses the attempt like D-7: logged, a refused attempt, exit 10) and **binding in the analysis on the submitted circuits** (noiseless MPS); a missing or unreadable result is a failure; the bit-order control is reported only |
| K3 | integrity items | + code identity with run 2; C-1 recomputed; run-2 snapshot and model hashes in `calibration_check.json` equal the known values; `power_run3.json` exists with the hash of `job.json`, frozen input hashes, equal recomputation; the log prefix recorded in `job.json` is unchanged; no later log line is dated before the submission; the first logged fetch's file exists with its logged SHA-256; the job was created and started at or after `job.json`'s `submitted_utc` (from the saved metrics) |
| Manifest | `FREEZE_GHZ2.json` | `FREEZE_GHZ3.json`, listing every file of this folder (14 files, see `REQUIRED_FROZEN_3` in `ghz3_run.py`) |
| Headline | table, F_M, Re sensitivity | the same, plus the answer to Q1 and Q2, R(n) of runs 1, 2 and 3, tracking (measured vs predicted change from run 2, CI shot noise only, sigma_d,F next to it), small-n drift next to H1, C-1, the log, power at submission |
| Files | `ghz2_*.py`, `tests_ghz2.py`, `RESULTS_GHZ2.*` | `ghz3_*.py` (wrappers), `tests_ghz3.py`, `RESULTS_GHZ3.*` |

| File | Role |
|---|---|
| `ghz2_core.py` | selection, circuits, model M2 and reference M, estimators, bootstrap, snapshot, freeze check. **Run 2's file, unchanged** |
| `ghz2_study.py` | Truth_Gate study of H1-H3 (numpy + kapi/truth_gate only). **Run 2's file, unchanged** |
| `ghz3_study_h4.py` | Truth_Gate study of H4: criterion, worlds `plus` / `minus`, control (numpy + truth_gate only) |
| `ghz3_run.py` | `--selftest`, `--dry-run`, `--submit --quota-seconds N`, `--fetch`, `--recover JOBID`; C-1, C-2, rule-14 check, power function, log, atomic writes, code identity |
| `ghz3_analyze.py` | results: table, H1-H4 (imported unchanged), readings, labels, the assembled answer, K1-K3 (K2 binding), comparisons; `RESULTS_GHZ3.{json,md}` and `RESULTS_GHZ3_boot.npz` |
| `ghz3_d4.py` | pre-freeze checks: budget, K2 (design check), bit-order control, D4, rule 14, design-time power (simulator and run-1 and run-2 data only) |
| `tests_ghz3.py` | offline unit tests |
| `certs/` | Truth_Gate certificates (`cert_h4_v1.json`, `cert_h123_v1.json`), `k2_sim.json`, `power.json` |
| `REVISIONS.md` | revisions before the freeze, with reasons |

## Python

Use the venv `E:/Claude Projects/.venv-qiskit` (`Scripts/python.exe`): qiskit 2.6.2, qiskit-aer 0.18.2, qiskit-ibm-runtime 0.52.0,
numpy, scipy and **truth-gate 0.5.0**, installed editable from this repository (`pip install -e "E:\Claude Projects\kapi-oss"`).
`kapi` is the repository's deprecated shim of `truth_gate`, so `import kapi` (used by the frozen `ghz2_study.py`) gives the same
objects. (`pip list` also shows a stale `kapi 0.3.0` metadata entry from an older editable install; it is not what is imported.)
The system `py` has no qiskit. Run everything from this folder; outputs of the hardware steps go to `run/` inside it.

## Before the run (no account needed, no cost)

```text
python tests_ghz3.py          # offline unit tests, about 2 minutes (the analysis tests recompute the power; one test runs the real K2 binding)
python ghz3_d4.py             # budget, K2 design check, bit-order control, D4, rule 14, design-time power (2000 datasets x 6 simulations); about 50 s; writes certs/k2_sim.json and certs/power.json
python -m truth_gate check ghz3_study_h4.py --out certs/cert_h4_vN.json
python -m truth_gate check ghz2_study.py    --out certs/cert_h123_v1.json
```

Then the designer freezes the files (`FREEZE_GHZ3.json`, format `{"files": {name: sha256}}`, for example with
`../../protocol/tools/freeze.py`). The manifest must list every file of `REQUIRED_FROZEN_3`. `--dry-run`, `--submit`, `--fetch`,
`--recover` and `ghz3_analyze.py` refuse to run (exit code 3) if the manifest is absent, incomplete or does not match, **or** if the
SHA-256 of `ghz2_core.py` or `ghz2_study.py` differs from the values in `../ghz_heron_run2/FREEZE_GHZ2.json`.

## The author's steps

**1. The IBM account.** The account already saved for runs 1 and 2 is used (`QiskitRuntimeService()` with the default saved
account). Nothing to do; no key is ever typed, printed or stored by these scripts. If it is no longer valid, save it yourself with
the hidden-prompt command from `../ghz_heron_run2/README.md`.
*Cost:* nothing.

**2. `python ghz3_run.py --selftest`**
Offline, on `FakeKingston` only; no freeze, no account. Checks the code identity with run 2, builds and transpiles all 368 circuits,
asserts n - 1 two-qubit gates (K3), prints M2's predictions (the only mode that does), checks the model from the target equals the
model from the snapshot-rebuilt target, round-trips QPY, runs a tiny noiseless pipeline check and exercises the C-1, C-2 and power logic.
*Cost:* a few seconds of CPU, no hardware time.

**3. The stopping rule (PREREG section 1).** Read this before step 4 or 5.
- The first `--submit` that passes D-7, K2, C-1 and C-2 is the run.
- An *attempt* is a `--submit` invocation that reaches the D-7, K2, C-1 and C-2 checks (the lines of one invocation share the snapshot
  time). A missing or invalid `--quota-seconds`, an existing `run/job.json`, a missing freeze or a code-identity failure are not attempts.
- At most one attempt per UTC day (the day of its snapshot) may be refused; any further attempt that day after a refused one is a
  deviation, whether it passes or not. A K2 failure is a refused attempt like a D-7 failure.
- `--dry-run` is optional but **binding when D-7, K2 and C-1 pass, whatever C-2 says**: a passing `--submit` must follow within 2 hours
  (between the snapshot times), else it is a deviation. A dry run that fails D-7, K2 or C-1 is not binding.
- Every `--dry-run`, every `--submit` that reaches the checks and every `--fetch` appends a line to `run/dryrun_log.jsonl` (UTC time,
  snapshot time, backend, snapshot hash, the D-7, K2, C-1, C-2 results, the quota, the refusal reason, the SHA-256 of the predictions).
  A `--submit` that passes the checks appends a `submit-checks-passed` line at once, before the power computation, so that an
  interrupted passing attempt leaves a trace. The predictions are never printed or logged.
- The code records the timing and does not enforce it. At submission `run/job.json` records the SHA-256 and line count of the log;
  the analysis checks that prefix and that later lines are not dated before the submission, reports the whole log, applies the rule to
  the anchored lines plus the accepted line, and lists every logged line with C-1 passed and C-2 failed with its quota.

**4. `python ghz3_run.py --dry-run [--quota-seconds N]`** (optional; binding if it passes)
Verifies the freeze and the code identity, loads the saved account, lists the operational non-simulator backends with at least 156
qubits, selects the least busy Heron r2 one (D-1), builds and transpiles every circuit and prints **only**: the circuit and shot
counts, the time estimate, and PASS/FAIL of D-7, K2 (a noiseless simulation of the circuits just built, about 30 s), C-1 and (with
`--quota-seconds N`) C-2, and whether the dry run is binding. It prints no prediction and no difference
of predictions. It also prints the whitelisted numeric usage fields (for example `usage_remaining_seconds`) if the service offers
them, information only. It does **not** submit; its only write is one line in `run/dryrun_log.jsonl`. Exit code 0 if everything
it checked passes; 4 if the estimate exceeds 300 s, 10 if K2 fails, 5 if C-1 fails, 6 if C-2 fails (the first failing check in this order).
*Cost:* a few network calls (backend list, status, properties, usage) and about 30 s of CPU for K2; **no quantum time**.

**5. `python ghz3_run.py --submit --quota-seconds N`** (only with your approval; you may go here directly, or after a passing dry run within 2 hours)
`N` = the remaining QPU time in seconds that you read on the IBM Quantum dashboard. Same checks as `--dry-run`. It **refuses**
(nothing submitted; a line in the log) with exit code 7 if `--quota-seconds` is missing or not a positive number (not an attempt),
4 if the estimate exceeds 300 s, 10 if K2 fails (the noiseless simulation of the circuits to be submitted), 5 if C-1 fails (the
predictions did not move enough: retry after the next calibration), 6 if 1.15 x estimate > N (wait for the allocation to renew). When
the checks pass it appends the `submit-checks-passed` line, then computes the power file (nothing of it is printed), writes the
snapshot, `circuits.qpy`, `model.json`, `calibration_check.json` (with the calibration dates of the M2 inputs), `power_run3.json`
and `job.json` (which also records the versions of python, numpy, scipy, qiskit, qiskit-aer, qiskit-ibm-runtime and the platform, as
`power_run3.json` does) to a temporary folder, submits **one** SamplerV2 job (368 circuits, 2000 shots each, dynamical decoupling off,
twirling off, no execution-time limit) and moves the files into `run/` only after the job id is returned. It refuses to submit if
`run/job.json` already exists.
*Cost:* **this uses your quantum allocation**: about the estimate (run 2: 196 s actual for a 187 s estimate), 736000 shots in one job.
It cannot be undone.

**5b. If `--submit` ends with exit code 8 (the submission raised or was interrupted).** The attempt's files are kept in
`attempt_<utc>/` next to `run/`, `run/` has no job, and the failure is logged. **Before any retry, check the account's job list
(IBM Quantum dashboard or `QiskitRuntimeService().jobs()`) for a job created at that attempt.**
- If a job exists, it is the run: `python ghz3_run.py --recover JOBID` (add `--attempt attempt_<utc>` if there is more than one
  folder). It verifies the freeze, requires `run/job.json` absent and a logged failure line for the kept folder, and **refuses (exit 9)
  unless the service read succeeds and confirms**: the job's backend equals the attempt's, the job was created no earlier than 10 minutes
  before the attempt's snapshot time and not after the logged failure + 10 minutes (both bounds inclusive), and it has 368 circuits. Then it moves the kept files into
  `run/`, writing `job.json` (the job id, `"recovered": true`, the attempt's records and what it read from the service). It submits nothing.
- If no job exists, a new `--submit` may follow (it counts as an attempt under the stopping rule; the kept folder stays).

**6. `python ghz3_run.py --fetch [JOBID]`**  (run it **soon after the job finishes**)
Waits for the job (blocking call), saves the raw counts to `run/counts.json` (K3 totals check) and then, in a try/except that never
blocks the counts, writes a **new** file `run/execution_calibration_<utc>.json`: the job's execution timestamps and usage, the
calibration at the execution start (`backend.properties(datetime=...)`, `backend.target_history(datetime=...)`) with the calibration
date of every parameter, and the **current** calibration with its dates. Every fetch attempt is kept and **logged** (a `fetch` line with the file name and its SHA-256); the analysis uses the first logged one.
The analysis can verify "no recalibration since submission" only if the current calibration is still the snapshot's, so fetch before
the next calibration (the devices are recalibrated about daily); a late fetch ends as "execution-time calibration not verified".
*Cost:* network only; no quantum time. May block until the job has finished.

**7. `python ghz3_analyze.py`**
Offline (the K2 binding simulates the submitted circuits noiselessly, about 30 s). Verifies the freeze and the code identity,
recomputes M2 from the snapshot (and from the execution-time calibration if PREREG section 3 says so), estimates P, C, F with the joint
multinomial bootstrap (B = 2000, seed 20261113), applies H1-H4 and K1-K3, the readings (power at submission), the labels and the
assembled answer, and writes `RESULTS_GHZ3.json`, `RESULTS_GHZ3.md` and `RESULTS_GHZ3_boot.npz`.
*Cost:* about a minute of CPU.

## Notes

- **C-1** compares the n = 48 components of `model.json` (the M2 inputs: `S`, `cz_err`, `g1_pop_err`, `g1_par_err`, `ro_err`, `t1`,
  `t2`, `idle`; they contain every smaller n) of the new snapshot with `../ghz_heron_run2/run/model.json`, exactly (list equality),
  and the predictions F_pred per n. A calibration change outside S_48 changes neither and does not pass. The record in
  `run/calibration_check.json` has the inputs changed, dF_pred per n (F, P and C), the threshold, the Q1 result and label, the SHA-256
  of run 2's snapshot and model files (checked against the known values in `ghz3_run.RUN2_KNOWN`), the rule-14 check and the M2-input
  calibration dates. The Q1 label is decided on the snapshot's predictions (as C-1); the analysis also reports the Q1 test on the predictions in use if they differ.
- **M2-input calibration dates** (the same target set everywhere): T1, T2 and readout error of the qubits of S_48; every parameter
  (error and length) of the cz gates of the tree edges and of the one-qubit gates that enter g1_pop_err / g1_par_err (`sx`).
  Non-tree edges among S_48 and all other parameters are not inputs.
- **Power** (`ghz3_run.compute_power`): sigma_rel,X = sqrt(max(0, mean over n in {4, 8, 16, 32, 48} of [ln(X_run1/X_run2)^2/2 - v_X(n)])),
  v_X = var(X_boot)/X_hat^2 (sample variance, ddof = 1) of run 2's bootstrap; per dataset the truth P and C are multiplied by
  exp(sigma_rel,X z), z independent per n and component; shot noise is one centred run-2 bootstrap row; replicates = point + all
  centred rows; 2000 datasets, seed 20261116. Power of H1: truth F_pred - 0.03 at n = 4, 8 and run-2 ratios elsewhere. Power of H4 and
  the expected outcome: run-2 ratios. Sensitivity: drift fully correlated across n (one z per component), drift x 2. The readings always
  use the power at submission, computed on the snapshot's predictions.
- **Readings and the answer**: a FAILS of H1 or H4 reads "fails" if its power at submission is >= 0.8, else "not demonstrated". A missing
  or mismatched `power_run3.json` is a K3 failure (yorumlanamaz); there is no separate reading for it. H2 and H3 are reported. The
  answer is the Q1 sentence (H1 outcome and reading), the Q2 sentence (H4 outcome and reading), a joint sentence only for HOLDS/HOLDS,
  HOLDS/FAILS("fails"), FAILS("fails")/HOLDS and FAILS("fails")/FAILS("fails"), then the labels; a control failure gives "yorumlanamaz" alone.
- **H4 within-drift labels** (each n with its own sigma_d,R(n)): "holds within drift" iff 1 - q97.5(n) < 2 sigma_d,R(n) at some n;
  "fails within drift" iff q97.5(n) - 1 < 2 sigma_d,R(n) at every n with q97.5(n) >= 1. The n concerned are reported.
- **Execution-time calibration** ("equal" = every M2 input value of S_48 within a relative tolerance of 1e-6, the qubit list exact):
  the first logged fetch attempt is used (its file and SHA-256 must match the log: K3). A history result is accepted only if every M2-input date in it is at or before the execution start
  (otherwise it counts as unavailable). Accepted and equal: snapshot predictions, no label. Accepted and different, every differing
  input with a later date than at submission (qubit parameter, gate error; an idle time needs a later `gate_length` date): primary
  predictions = M2 on it, "calibration changed before execution", snapshot predictions secondary. Accepted and different without such
  dates: "execution-time calibration not verified", snapshot predictions. History unavailable, rejected or failing in any way (a hash mismatch, an unreadable result, M2 cannot be computed): the saved current calibration
  gives "verified: no recalibration since submission" (snapshot predictions) iff its M2 inputs equal the snapshot's and the date of every
  M2 input is before the job's `submitted_utc`; anything else is "not verified".
- **Environment** (T7): `power_run3.json` and `job.json` record python, numpy, scipy, qiskit, qiskit-aer, qiskit-ibm-runtime and the
  platform. The analysis compares them with its own environment (reported in the results); if the power recomputation differs and the
  environments differ, it names a version mismatch as the likely cause (the recomputation failure remains a K3 failure).
- **Job times** (K3): the job's creation and execution-start timestamps in the saved metrics must not precede `job.json`'s `submitted_utc` by more than
  10 minutes (local clock versus service clock); a single missing timestamp is reported and the other decides; both missing is a failure.
- K1: for MIX_8 and MIX_32 the 97.5th percentile of the C_mix bootstrap is <= 0.05. K2: noiseless MPS simulation, F_sim >= 0.98 for
  every n and C_mix,sim <= 0.05, on FakeKingston's circuits (design check, `certs/k2_sim.json`), on the circuits about to be submitted (`--dry-run`, `--submit`; a failure refuses
  the attempt, exit code 10) and on the submitted circuits (binding in the analysis).

## Diff list: run 2's wrappers vs run 3's

`ghz2_core.py` and `ghz2_study.py`: **no difference** (byte for byte; SHA-256 5318b041... and 4bf9f2ec..., equal to `../ghz_heron_run2/FREEZE_GHZ2.json`).
`ghz3_study_h4.py`: new file (no change since the first certificate; `certs/cert_h4_v1.json` still reproduces, body `ff4351e2...`).

**`ghz3_run.py` vs `ghz2_run.py`**

| Change | Why |
|---|---|
| manifest `FREEZE_GHZ3.json` and the 14-file required list through `core.verify_freeze(root, manifest_name, required)`; `verify_run3_freeze` | PREREG section 8 (F3) |
| `code_identity`: SHA-256 of `ghz2_core.py` and `ghz2_study.py` against run 2's `FREEZE_GHZ2.json`, before every hardware step (also in `ghz3_analyze.py` and `--selftest`) | K3 addition |
| `c1_check` (with the per-question Q1 result), `m2_inputs`, `load_run2_reference` (known file hashes), `calibration_record`; C-1 in `--dry-run` (pass/fail only) and `--submit` (refusal, exit 5) | C-1 |
| `rule14_check`, recorded in `calibration_check.json` | rule-14 check at submission |
| `c2_check`, `parse_quota`, `--quota-seconds`, exit codes 6 and 7; `k2_noiseless` in `_checks` (exit code 10, refusal order D-7, K2, C-1, C-2); `quota_seconds` and the C-2 record in `run/job.json` | C-2 |
| `build_and_report(..., show_model=False)`: `--dry-run` and `--submit` never print predictions or the selected qubits; only `--selftest` does | stopping rule |
| `append_log`, `log_line`, `predictions_sha256`, `log_anchor`, `log_prefix_sha`: one line per `--dry-run` and `--submit` (modes dry-run, submit-checks-passed, submit-refused, submit-failed, submit-accepted, submit-not-attempt, recover, fetch) with the hash of the predictions, the snapshot time and the invocation; `job.json` records the log's line count and SHA-256 | stopping rule (N2, T1, T2) |
| `compute_power`, `power_inputs`, `drift_sigmas`, `design_time_power`; `power_run3.json` written at submission, hash in `job.json` | power at submission |
| `m2_gate_keys`, `m2_date_targets`, `m2_target_records`, `select_m2_dates`, `date_of`: the calibration dates of the M2 inputs of S_48 at submission | N4 |
| `--submit`: all files go to a temporary folder next to `run/` and are moved into `run/` after the job id is returned; any `BaseException` is logged, the folder is kept as `attempt_<utc>` (`KeyboardInterrupt` is re-raised), exit 8 | atomic writes (N7) |
| `--recover JOBID [--attempt NAME]` (`cmd_recover`, exit 9 on refusal; needs a successful service read: backend, creation time window, 368 circuits) | N7, T3 |
| `--submit` and `--dry-run` return distinct exit codes (4, 5, 6, 7, 8, 10); in run 2 `--submit` raised `SystemExit` with a message (exit 1) | distinct codes per refusal |
| `_print_usage` prints only the whitelisted numeric fields (`usage_remaining_seconds`, `usage_consumed_seconds`, `usage_limit_seconds`, `usage_allocation_seconds`) | F19 |
| `_submit_job` factored out of `cmd_submit` (same SamplerV2 options; no execution-time limit) | testability |
| `--fetch` also calls `save_execution_calibration`: metrics, job usage, `snapshot_at` (`target_history` + `properties` at the execution start, with the dates of that result) and the current calibration with its dates, always; every attempt in a new file `execution_calibration_<utc>.json`, logged with its SHA-256 | PREREG section 3 (N4, T2) |
| `environment_info` in `power_run3.json` and `job.json` | T7 |
| `cmd_selftest` also checks the code identity, C-1, C-2 and the power function | tests of the new logic |
| `main(argv, root, run2_dir)` takes the run-2 folder as a parameter (default `../ghz_heron_run2`) | tests with temporary folders |
| Unchanged: `heron_r2_basis`, `pick_backend`, `_service`, the refusal when `run/job.json` exists (now logged as a non-attempt), the D-7 check (`enforce_time_budget`) | |

**`ghz3_analyze.py` vs `ghz2_analyze.py`**

| Change | Why |
|---|---|
| `CRITERIA` has H1-H3 from `ghz2_study` and H4 from `ghz3_study_h4`, imported unchanged; `ROLES` (H1, H4 confirmatory; H2, H3 reported) | PREREG section 4 |
| K2: the design check `certs/k2_sim.json` (missing or unreadable = failure; bit-order control reported only) **and** `k2_noiseless` on the submitted circuits (binding) | N9, F3, F17 |
| K3 additions: code identity; C-1 recomputed; run-2 hashes in `calibration_check.json` equal the known values; `power_file_status` (hash equals job.json's, input hashes equal the frozen `certs/power.json` and `FREEZE_GHZ3.json`, recomputation equal, environment compared); `log_prefix_status` (prefix and post-anchor times); `first_logged_fetch_status`; `job_time_status` | PREREG section 5 (N2, N5, T2, T3, T7) |
| `execution_calibration`: first logged fetch attempt; any failure of the history path falls through to the current calibration; history result accepted only with M2-input dates at or before the execution start; "changed" needs later dates (`differing_input_dependencies`, `changed_inputs_have_later_dates`); fallback by dates (`dates_before_submission`); labels, secondary predictions and criteria | PREREG section 3 (N4) |
| `drift_quantities` (sigma_d,F, sigma_d,R), `h1_drift_label`, `h4_margins`, `power_reading`, `build_labels` (with the Q1 replicate label), `assemble_answer` (replaces the old mapping) | PREREG section 4 (N1, N3) |
| `h2_report` (CI-based reach, interpolated crossing with CI), `interp_crossing` | PREREG section 4 |
| `tracking_table` (CI labelled shot noise only, sigma_d,F next to it), `read_log`, `read_log_split`, `stopping_rule_report` (invocations, binding dry run from the logged D-7/K2/C-1, snapshot-time window, C-1 pass and C-2 fail lines), rule-14 recheck, C-1 summary | headline (N2, N9) |
| `comparison_with_earlier_runs` (R of runs 1, 2, 3; small-n drift; run 1 under M2 recomputed from run 1's files, quoted values only as a labelled fallback) | headline |
| outputs `RESULTS_GHZ3.*`; extra parameters `run2_dir`, `run1_dir`, `code_dir`, `certs_dir`, `power_n_datasets` (defaults: the real folders and the registered 2000 datasets) | naming and tests |

**`ghz3_d4.py` vs `ghz2_d4.py`**

| Change | Why |
|---|---|
| D4 covers H1-H4 (H1-H3 on `ghz2_study` worlds, H4 on `ghz3_study_h4` worlds); "covered" also requires that the analysis applies no criterion that is in no study | PREREG section 7 |
| rule 14 additionally requires every F_pred in (0, 1) | H4 can fail |
| `power()` calls `ghz3_run.design_time_power` (the function `--submit` uses) and writes `certs/power.json` | F1 |
| K2's pass condition is the estimator fidelity only; the bit-order control is recorded in `k2_sim.json` with a note; this K2 is the design check, the binding K2 runs in the analysis | F17, N9 |
| Budget, K2 seeds and thresholds are unchanged | |
