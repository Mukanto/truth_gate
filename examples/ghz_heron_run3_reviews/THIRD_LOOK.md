# GHZ run 3: third look before the freeze (PREREG v3)

Reviewer: a fresh agent. It wrote no part of the study and did neither of the two earlier reviews. It read only this task
folder and ran the venv interpreter on a writable copy in `scratch\examples\`.

This look is narrow. It checks the second look's findings N1–N9 and the partly fixed F2, F4, F8 and F9. It also checks the
code changed for v3: the stopping-rule log and its deviation report, the answer assembly, the execution-time calibration
and its date checks, `--recover`, the power-file checks and the binding K2.

**What was run (offline):**
- `tests_ghz3.py`: 117 tests, all pass.
- `ghz3_d4.py`: rewrites `certs/power.json` and `certs/k2_sim.json` byte for byte identical to the shipped files (power of H1 0.953, of H4 1.000; K2 passes).
- `ghz3_run.py --selftest`: OK.
- A mutation check of the printing tests.
- `scratch\check_v3_paths.py`, whose results are in `scratch\check_v3_paths_out.json`.
- A check that the n = 48 gate inputs contain those of every smaller n.
- A disassembly of the in-memory `IBMBackend` methods of qiskit-ibm-runtime 0.52.0 (`scratch\ibmbackend_dis.txt`). No library source file was opened.

Nothing was run against the IBM service. No network, no git and no agent were used.

**Summary.**
- Earlier findings: all 13 are fixed (N1–N9, F2, F4, F8, F9).
- New findings: none blocking, none major, 8 minor (T1–T8).
- **Freezable as is: yes.** T1–T3 are cheap and worth doing if any file is touched again.

## 1. Earlier findings

**N1 – fixed (closes F2).**
- What the text and code now do:
  - C-1 applies per question. Q1 counts as a model test only if max(|ΔF_pred(4)|, |ΔF_pred(8)|) ≥ 0.02. Otherwise the answer carries a fixed label, and the label's text in the PREREG equals `Q1_LABEL`.
  - `c1_check` returns the Q1 maximum and the flag. `calibration_check.json` records them, and the analysis attaches the label and also reports the value on the predictions in use.
  - The justification of 0.02 no longer claims that 0.02 exceeds the drift.
- On FakeKingston, the n = 48 POP and PAR_0 gate set (47 cz, 48 sx) contains the gates of every smaller n, and S_n ⊂ S_48. So "the n = 48 components contain every smaller n" holds for the gate and qubit inputs.
- Residual: T4.

**N2 – fixed (closes F9).** All four requested fixes are in place:
- A passing dry run is binding.
- Attempts and the same-day limit are defined, and the report implements them. The second look's cases A–F now give the results the v3 text defines.
- The log holds the predictions' SHA-256, never the predictions.
- `job.json` anchors the log's line count and hash, and the analysis checks that anchor as a K3 item.

The remaining timing freedom reveals C-1 pass or fail only, never a prediction (T1). The lines after the anchor are not validated (T2).

**N3 – fixed (closes F4).**
- The answer is assembled from a Q1 sentence (H1's outcome and reading), a Q2 sentence (H4's outcome and reading), a joint sentence for the four definite combinations, and then the labels.
- Every sentence equals the PREREG tables verbatim (checked programmatically).
- All 16 combinations are tested, and a control failure gives "yorumlanamaz" for each of them.

**N4 – fixed (closes F8).**
- The history result is saved with its calibration dates. It is accepted only if every M2-input date of S_48 is at or before the execution start.
- "Changed" requires every differing input to carry a later date than the dates recorded at submission: per edge or gate for errors, per qubit for T1, T2 and readout, and any gate length for an idle time. Otherwise the label is "not verified" and the snapshot's predictions are used.
- Every fetch writes a new file, and the analysis uses the first.
- A test covers a service that ignores the datetime.
- In qiskit-ibm-runtime 0.52.0, `target_history(datetime)` is `convert_to_target(configuration, properties(datetime=datetime))`, so the values and the dates come from the same kind of query.
- `IBMBackend.target` caches its Target, and `properties(refresh=True)` does not rebuild it. The fallback is still safe: its dates come from the refreshed properties and must all precede the submission, so a cached Target cannot produce a false "verified".
- Residuals: T2, T3 and T6.

**N5 – fixed.**
- The power file's input hashes are compared with the frozen `certs/power.json` (data files), with `FREEZE_GHZ3.json` (study files) and with the files as they are now.
- Its predictions must be the snapshot's.
- The power is recomputed from the snapshot's predictions and must be equal. Each of these is a K3 item.
- The readings use the submission power in every case of §3. Residual: T7.

**N6 – fixed.**
- My mutation (`show_model=True` in both `cmd_dry_run` and `cmd_submit`) makes three runner tests fail.
- The self-comparison is gone.
- The freeze-list test now walks the folder.
- The parsed quota is logged.

**N7 – fixed.**
- The submission block catches `BaseException`, keeps the folder as `attempt_<utc>`, logs the failure (with the job id if one came back) and re-raises an interrupt.
- `--recover` completes `run/` without submitting.
- Residuals:
  - An interrupt in the few seconds before that block is not logged (T1).
  - `--recover` does not check the job's identity (T3).

**N8 – fixed.** Independent symmetric readout error is listed among the opposite-direction classes, with the correct factor of 2 (C scales with ∏(1−2ε), P with ∏(1−ε)).

**N9 – fixed.** All five points are addressed:
- the joint (FAILS, FAILS) sentence is reworded;
- K2 is binding on `run/circuits.qpy`;
- the `ghz3_d4.py` docstring is corrected;
- the tracking rows are labelled "shot noise only", with σ_d,F next to them;
- the REVISIONS note on the F3 row is added.

Other stale "v2" strings remain (T5).

## 2. New findings (all minor)

**T1. The binding clause can be side-stepped without a reported deviation.** (`ghz3_run.py` `_refusal`, `cmd_dry_run`, `cmd_submit` lines 863–898; `ghz3_analyze.py` `stopping_rule_report`; PREREG §1)
- **Low quota.** "Passing" means exit code 0. A dry run with `--quota-seconds` below 1.15 × the estimate:
  - prints "C-1 … PASS" and logs `q1_model_test` and max |ΔF_pred|;
  - ends with exit 6, so it is not binding and never a deviation.
  - `--submit --quota-seconds 1` does the same once per UTC day, as an allowed refused attempt.
  - My check: three such submits on three days, then a real submit on day 4, give "deviations: none".
- **Interrupt.** A Ctrl-C after the PASS lines and before the `BaseException` block leaves no log line and no folder. That gap is about 3 s of power computation in `--submit` and about 1 s of usage query in `--dry-run`. An attempt that passed every check then vanishes.
- **Unlogged runs.** The text says every `--dry-run` and every `--submit` appends a line. Freeze or code-identity refusals, an invalid dry-run quota, and failures before the checks write none.
- **Window.** The 2 h window is measured between log-write times. The accepted line is written after the power computation and the upload, so a submit started just under 2 h after the dry run can be flagged.
- Why minor: no route reveals a prediction.
- Fix:
  - Call a dry run binding when D-7 and C-1 pass, whatever C-2 says, and have the report use the logged d7 and c1 results.
  - Report every line where C-1 passed but C-2 failed.
  - Log a "checks passed" line right after the checks, or widen the `BaseException` handler.
  - Align the "every line" wording with the code.
  - Measure the window from the attempt's start.

**T2. Integrity of the v3 records.** (`log_prefix_status`, `stopping_rule_report`, `execution_calibration`, `cmd_fetch`)
- **(a) Lines after the anchor.**
  - The anchor covers only the lines before the accepted submit. Later lines, the accepted line included, feed the deviation report unchecked, and their `utc` is self-reported.
  - My check: a passing dry run at 08:00 and an accepted submit at 11:00 give one deviation. After I appended a back-dated `submit-failed` line stamped 09:00, the list was empty and the anchor check still passed.
- **(b) Fetch attempts.**
  - Nothing records how many `execution_calibration_*.json` files were written, or their hashes, so "the first is used" cannot be checked. Deleting the first file would go unnoticed.
  - This matters if a recalibration falls between submission and execution. An early fetch can then give "changed" (execution-time predictions primary), and a late one "not verified" (snapshot predictions primary). That would be a choice between two sets of predictions after seeing the data.
- **(c) The anchor itself** sits in `job.json`, which the same author writes. It catches accidental edits, not deliberate ones.
- Fix:
  - Treat a post-anchor line dated before `submitted_utc` as a K3 failure.
  - Log every fetch attempt (file name and SHA-256) and use the first logged one.
  - Optionally publish `job.json` and the log right after submission.

**T3. `--recover` accepts any job id.** (`cmd_recover`; K3 block of `run_analysis`)
- `--recover` reads the job's backend and status as information only. It does not check:
  - the job's backend against the attempt's;
  - the job's creation time against the attempt time;
  - the number of pubs.
- The analysis has no K3 item that the job ran after `submitted_utc`.
- Run 2's job has 368 pubs with the same circuit names. A misread id would pass `--fetch` and K3 and be analysed as run 3, with only a "not verified" label.
- My checks:
  - a job on another backend is accepted;
  - an execution start one day before submission, with equal values, gives "equal" and no label.
- Fix:
  - In `--recover`, refuse unless the backend matches, the job was created at or after the attempt, and it has 368 pubs.
  - Add a K3 item: the job's `created` time and execution start are at or after `submitted_utc`.

**T4. The Q1 label is under-specified in the text.**
- **Which predictions.** The code decides the label on the snapshot's predictions, even when §3 makes the execution-time predictions primary. The PREREG does not say which predictions apply.
- **Wording.**
  - In the replicate case the Q1 sentence still begins "on a new calibration", next to a label that says Q1 is a replicate.
  - On a device change, the label calls the test "a replicate of run 2's small-n test", although the inputs come from another chip.
- Fix:
  - Add one sentence naming the predictions that decide the label.
  - Optionally reword the replicate case and the device-change case.

**T5. Stale strings.**
- Module docstrings still cite "PREREG.md v2".
- `compute_power` writes `"prereg": "… PREREG v2"` into `power_run3.json` and `certs/power.json`.
- The selftest prints "C-1 (v2)", and a test asserts that text.
- The analysis docstring still names `run/execution_calibration.json` and omits the binding K2.
- PREREG §1 says an interrupted submission exits with code 8, but the code re-raises the interrupt.
- Fix: update all of these. Changing the `compute_power` record changes `certs/power.json`, so `ghz3_d4.py` and the tests must be rerun.

**T6. No fallback when a history result passes the date check but cannot be used.**
- If M2 cannot be computed on the history result, or its hash does not match, `execution_calibration` returns "unavailable" without trying the saved current calibration.
- My check: with a t1 of None in the history result, the status is "unavailable". The same current calibration on its own gives "verified".
- The outcome is conservative, but a verifiable label is lost.
- Fix: fall through to the current-calibration block.

**T7. The power recomputation must be bit-exact, and no versions are recorded.**
- K3 requires the recomputed power record, including the integer tallies of 12 000 simulated datasets, to equal `power_run3.json` within 1e-9.
- A different numpy or platform at analysis time could flip one dataset and make the run "yorumlanamaz", and nothing would show why.
- Fix: record the numpy, scipy, qiskit and python versions and the platform in the power file and `job.json`, and state that the analysis runs in the same environment.

**T8. The binding K2 runs only after the QPU time is spent.**
- A transpilation defect on a new device or calibration would surface only in the analysis.
- The same noiseless check (about 30 s, no account) could also run in `--submit` before submission, as a refusal.
- Optional; FakeKingston's margins are large (F_sim ≥ 0.999, C_mix,sim ≤ 0.006).

## 3. Checks that found no problem

- Code identity with run 2 holds. Both certificates' study hashes equal the current files.
- `m2_gate_keys` walks the circuits in the same order, with the same skips, as `core._one_q_errors`. The dates are therefore checked against the right gates.
- The power-file checks are all wired into K3.
- The readings use the submission power in every case of §3.
- No refusal path submits anything. None writes outside `run/`, except the kept attempt folder after a failed submission.

## 4. Freezability

**Freezable as is.**
- There is no blocking or major finding, and N1–N9 and F2, F4, F8 and F9 are fixed in both the text and the code.
- T1–T8 may be recorded as known limitations.
- T1, T2 and T3 cost a few lines each and close holes in the records added for v3, so I recommend them if any file is touched again.
- After any change, rerun `tests_ghz3.py` and `ghz3_d4.py` before the freeze.
