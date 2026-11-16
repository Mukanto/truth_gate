# GHZ run 3: second look before the freeze (PREREG v2)

Reviewer: a fresh agent. It wrote no part of the study and did not do the first review. It read only this task folder.

What was run, all offline, on a writable copy in `scratch\examples\`:
- `tests_ghz3.py`: 89 tests, all pass.
- `ghz3_d4.py`: rewrites `certs/power.json` and `certs/k2_sim.json` byte for byte identical to the shipped files.
- `ghz3_run.py --selftest`: OK.
- Four checks of my own in `scratch\`: `check_stopping_rule.py`, `check_c1_profile.py`, `check_print_test.py` and `check_tracking_seed.py`.

Nothing was run against the IBM service.

**Summary.**
- First-review findings: 16 of 20 fixed, 4 partly fixed (F2, F4, F8, F9), none not fixed.
- New findings: 0 blocking, 4 major (N1–N4), 5 minor (N5–N9).

## 1. First-review findings

**F1 (power) – fixed.**
- Power is now defined per criterion at a stated effect:
  - H1: truth F_pred − 0.03 at n = 4, 8, which is inside the band.
  - H4: truth with run 2's ratios.
- The expected outcome is reported separately, not as power.
- `--submit` computes `run/power_run3.json` from the new predictions before the job goes out. It is written to the temporary folder, nothing of it is printed, and its SHA-256 goes into `job.json`.
- The analysis reads only that file. A device change is labelled.
- H2's knife edge no longer matters, because H2 is now only reported.
- Design-time values (reproduced): power of H1 0.953, power of H4 1.000, expected P(H1 HOLDS) 0.218.
- If the drift is estimated from n = 4 and 8 only (σ_P 0.006, σ_C 0.027), H1's power is still 0.90. The "fails" reading is robust.
- Residuals: see N5.

**F2 (C-1) – partly fixed.**
- What is fixed:
  - C-1 now compares the M2 inputs of S_48 (the n = 48 fields of `model.json`).
  - It requires max_n |ΔF_pred| ≥ 0.02.
  - A change outside the patch is refused.
  - This removes the "any of 1132 values" hole and makes H4 (Q2) a real model test.
- What is not: H1 (Q1) reads only n = 4 and 8, and in practice the maximum is reached at n ≥ 16. For Q1 the run can again be a data replicate. See N1.

**F3 (freeze list) – fixed.**
- `REQUIRED_FROZEN_3` lists all 14 files of the folder, and the freeze check refuses a manifest that omits one.
- A missing K2 file is a K2 failure. A missing or mismatched power file is a K3 failure.
- Residuals:
  - The REVISIONS table row for F3 is stale; clarification 3 supersedes it.
  - The input hashes are compared with the current files, not with frozen values (N5).

**F4 (verdict mapping) – partly fixed.**
- The (H1, H4) table, the control row, the UNDEFINED rows and the labels are all there.
- The "not demonstrated" readings are not mapped to definite sentences, and H4's own reading is ignored (N3).

**F5 (H1 and drift) – fixed.**
- The unsupported sentence is gone.
- σ_rel, σ_d,F and σ_d,R are defined, and the "within drift" label is pre-registered.
- H1's power is computed at a stated effect.
- With σ_d,F(4) ≈ 0.010, the label will almost surely attach under run-2 ratios. That is informative, not a defect.

**F6 (H2) – fixed.** H2 is demoted to reported, with the CI-based reach and the interpolated crossing with its CI.

**F7 (H3) – fixed.**
- H3 is demoted to exploratory, and the rule-15 list is added.
- Minor gap: one class is missing from the list (N8).

**F8 (calibration at execution) – partly fixed.**
- What is fixed:
  - `--fetch` saves the timestamps, the usage, and a snapshot from `properties(datetime=start)` and `target_history(datetime=start)`. Both methods exist in qiskit-ibm-runtime 0.52.0.
  - There is a fallback: the current calibration with its dates.
  - The analysis applies a mechanical four-way rule with tolerance 1e-6 and labels.
- What is not:
  - The history path itself is not date-verified.
  - `--fetch` overwrites the record.
  - The PREREG does not say which power applies when the execution-time predictions are primary.
- See N4 and N5.

**F9 (stopping rule and log) – partly fixed.**
- What is fixed: the predictions are no longer printed, and every dry-run and every submit attempt is logged.
- What is not:
  - The rule still permits waiting: a passing dry-run may go unused "or not at all that day" on any number of days.
  - The predictions are readable in the log.
  - The analysis's deviation check both misses and invents deviations.
  - The log is not anchored in `job.json`.
- See N2.

**F10 (H4 and drift) – fixed.** The margins are reported next to σ_d,R(n). The "holds within drift" and "fails within drift" labels compare each n with its own σ, and they never change the verdict.

**F11 (drift model) – fixed.**
- The drift is pooled, relative and corrected for shot noise. Sensitivity rows give correlated drift and drift × 2.
- Note: the pooled P term is negative, so σ_rel,P = 0. No sensitivity row contains any P drift, and the drift × 2 row gives H1 power 0.732.

**F12 (H4 vacuity) – fixed.** It is recorded in REVISIONS and §7, and I-7 is added.

**F13 (rule 14) – fixed.** The check runs at submission and is saved. The analysis rechecks it on the snapshot's predictions and on the predictions in use, and attaches the "H1 one-sided" label if either fails.

**F14 (H1 UNDEFINED text) – fixed.** The text now matches `ghz2_study` (n = 4, 8 only).

**F15 (C-2 wording) – fixed.** It now says "estimate computed at submission" and gives the reason for not setting an execution-time limit.

**F16 (wording) – fixed.** The first docstring line of `ghz3_d4.py` still says "run-2 data only" (N9).

**F17 (bit-order control) – fixed.** It is no longer part of K2's pass condition.

**F18 (K3 and C-1) – fixed.** K3 recomputes C-1 and checks the known run-2 hashes.

**F19 (redaction) – fixed.**
- Only whitelisted numeric usage fields are printed.
- The execution record stores only timestamps, usage and exception type names.
- Trivial leftover: the raw `--quota-seconds` string is logged in one refusal path (N6).

**F20 (atomic writes) – fixed.**
- The files go to a temporary folder and are moved into `run/` only after the job id is returned, with `job.json` last.
- Residual: a "failed" submission that the service actually accepted (N7).

## 2. New findings

**N1 (major): C-1 does not make Q1 a model test.**
- The rule: C-1(b) takes the maximum of |ΔF_pred| over all n. H1 reads only n = 4 and 8.
- My simulation (`check_c1_profile.py`):
  - Method: random, independent recalibrations of run 2's snapshot. Every qubit's readout, sx/x, T1 and T2, and every edge's cz error got a lognormal factor. The circuits stay the same, because the selection is error-blind. The rebuilt model equals `model.json`.
  - With σ = 0.2, C-1(b) passes in 35% of the draws. In 98% of those, the predictions at both n = 4 and n = 8 moved by less than 0.02.
  - With σ = 0.3, C-1(b) passes in 78% of the draws, and 88% of those have small-n changes below 0.02.
  - The maximum falls at n = 16–48 in more than 90% of the draws.
  - Median small-n changes are about 0.004–0.008. That is below the run-1/run-2 drift (0.022) and about 1–2 shot-noise σ of F.
- A correlated shift, like FakeKingston's earlier calibration (ΔF(4) ≈ −0.05), would move small n too. So the outcome depends on the kind of recalibration, and C-1 does not guarantee it.
- Consequence: Q1 would be reported as answered "on a new calibration" when, for the columns it reads, the run is again a data replicate (rule 2).
- The justification is also inconsistent:
  - It ties 0.02 to the small-n drift, "so that the new predictions differ by more than the drift", but 0.02 < 0.022.
  - It applies the threshold wherever the maximum falls, including n ≥ 16, where the drift was ≤ 0.004.
- Fix:
  - Pre-register that Q1 counts as a model test only if max(|ΔF_pred(4)|, |ΔF_pred(8)|) ≥ 0.02 (or a justified threshold). Otherwise the Q1 answer carries a fixed label and sentence, such as "small-n predictions unchanged from run 2: Q1 is a data replicate". The data for this are already in `calibration_check.json`.
  - Alternatively, require (b) at n = 4 or 8 before submitting, at the cost of longer waiting.
  - Fix the justification sentence.

**N2 (major): the stopping rule still permits waiting, and its report does not implement it.**
- Waiting is permitted:
  - A passing `--dry-run` may go unused "or not at all that day", on any number of days, and dry-runs are unlimited.
  - The predictions are in clear in `run/dryrun_log.jsonl`, so not printing them is no protection.
  - A deliberately low `--quota-seconds` gives a C-2 refusal that also logs the predictions, and it may be retried the next day.
  - None of this is a deviation under the text. On such logs the analysis reports "none" (`check_stopping_rule.py`, cases B and F).
- `stopping_rule_report` misses a deviation the text defines. Case A: a passing dry-run at 02:00 is skipped, then a passing dry-run at 12:00 and a submit at 13:00, all on the same UTC day. The report says "none", because the 2 h gap is measured only from the latest passing dry-run.
- It also reports deviations that are not ones. It counts every submit line, so these are all flagged as "2 --submit attempts on one UTC day":
  - C: one same-day retry after a C-1 refusal, which "a second retry on the same UTC day" permits;
  - D: a quota typo (exit 7) followed by a submit;
  - E: an accidental second `--submit` after acceptance.
- `job.json` does not record the log's hash or line count, so earlier lines can be removed without trace.
- The tests cover none of these cases.
- Fix:
  - Drop `--dry-run` from the plan (`--submit` already checks everything and refuses safely), or make the first passing dry-run binding: `--submit` within 2 h, and any unused passing dry-run is a reported deviation.
  - Count only C-1, C-2 (and D-7) refusals as attempts, and state the retry limit unambiguously.
  - Anchor the log in `job.json` (hash and line count) and check it in the analysis.
  - Implement the deviations exactly as written, and add tests for cases A–F.

**N3 (major): the verdict mapping is not mechanical for "not demonstrated" readings.**
- The H1 "not demonstrated" row says to take "the row above with 'fails' replaced by …". That cannot be applied literally:
  - the H4 HOLDS base sentence contains no "fails";
  - in the H4 FAILS base sentence the substitution gives an ungrammatical sentence, and "misses the small-n band" remains.
- The code returns the instruction itself plus the base sentence, so the final wording is written after the data.
- The readings rule applies to every confirmatory criterion, but the mapping uses only H1's reading. An H4 FAILS read "not demonstrated" gets the "fails" sentences ("did not persist at every n", "not by overpredicting at every n").
- A test asserts this: with power H1 0.8 and H4 0.1, the answer is `ANSWERS[('FAILS','FAILS')]`.
- These rows are unlikely at the design-time power, but rule 3 needs every combination mapped.
- Fix: write a full sentence for each combination of outcome and reading of H1 and H4, pass both readings to the mapping, and test every row.

**N4 (major): the history path of the execution-time calibration is not verified.**
- The history path saves no calibration dates. Whenever an M2 input differs by more than 1e-6, the analysis declares "calibration changed before execution" and makes M2 on that calibration primary. The fallback path, by contrast, is date-checked.
- First failure scenario:
  - the service ignores or approximates the datetime and returns the latest calibration;
  - the author fetches after the next recalibration (the README notes the devices recalibrate about daily);
  - the primary predictions then come from a calibration that never applied to the data.
- Second failure scenario: a systematic difference between `target_history()` and `backend.target` would trigger "changed" spuriously.
- `--fetch` also overwrites `execution_calibration.json` on every call.
- The tests' fake backend returns the same target for any datetime, so they cannot catch this.
- Fix:
  - Save the dates in the history path too.
  - Accept "equal" or "changed" only if every M2-input date of S_48 is at or before the execution start, and, for "changed", the differing parameters are dated after their snapshot dates. Otherwise label "not verified" and keep the snapshot's predictions.
  - Make `--fetch` refuse to overwrite the record, or keep every attempt and use the first.
  - Add a test where `target_history` ignores the datetime.

**N5 (minor): integrity of the power file.**
- K3's check of the input hashes compares them with the current files. The PREREG says "the frozen files".
- The run-1/run-2 data files are not in `FREEZE_GHZ3.json`, although their design-time hashes are in the frozen `certs/power.json`.
- The deterministic power is not recomputed in the analysis, so the numbers that decide "fails" or "not demonstrated" rest on a file anchored only by a hash in `job.json`, which the same process writes.
- The PREREG does not say that the snapshot-based power still applies when the execution-time predictions are primary.
- Fix: compare with `certs/power.json`'s input hashes, recompute the power in the analysis or in the independent recomputation step, and state the rule for §3 cases.

**N6 (minor): tests that do not test what they claim.**
- The tests that `--dry-run` and `--submit` print no prediction replace `build_and_report` with a stub that never prints. A mutation in which both modes call it with `show_model=True` still passes both tests (`check_print_test.py`).
- `assertEqual(pw['power']['H1'], pw['power']['H1'])` compares a value with itself.
- The test named "required list is every file of the folder" checks only that each listed file exists, not that the folder holds no unlisted file.
- A related leftover: the job.json-exists refusal logs the raw `--quota-seconds` string unparsed.

**N7 (minor): a submission that fails after the service accepted it.**
- Every exception from `_submit_job` leads to deleting the temporary snapshot, model and power files and an invitation to retry.
- If the service had in fact accepted the job, it runs on but cannot be analysed: the files are gone, and `--fetch` needs `job.json`. A retry would then create a second dataset, and nothing pre-registered says which job is the run.
- A KeyboardInterrupt, which is not an Exception, leaves the temporary folder and no log line.
- Fix:
  - Keep the temporary folder on failure, and catch BaseException for logging.
  - Pre-register a check of the account's job list before any retry; a job found there is the run.

**N8 (minor): a class missing from H3's rule-15 list.** The list reads as closed but omits independent readout error beyond the model. That class lowers C about twice as much as P, the opposite direction to H3. Run 2's PREREG listed it.

**N9 (minor): wording.**
- The (FAILS, FAILS) sentence, "M2 fails the model test without the run-1/2 pattern", overstates the case when H1 fails by overprediction and H4 fails at one large n.
- K2's "exact transpiled circuits" are FakeKingston's, as in run 2. After a device change they are not the circuits that were submitted.
- The first docstring line of `ghz3_d4.py` still says "run-2 data only".
- The tracking row's "predicted inside CI" uses a shot-noise-only interval, while the small-n drift (about 0.010) is comparable to its half-width (about 0.012).
- The REVISIONS row for F3 is stale.

Checks that found no problem:
- The shared bootstrap seed of runs 2 and 3 does not correlate their replicates (|r| ≤ 0.05; `check_tracking_seed.py`), so the tracking interval is sound.
- The certificates' study hashes equal the current files.
- No refusal path submits anything. The only file a refusal writes is the log line the text requires.

## 3. Freezability

The design cannot be frozen as is, but nothing found here blocks it: none of the four major findings requires a change to the circuits, the estimators, the frozen `ghz2_core.py` or `ghz2_study.py`, H4's study, or the budget.

Before the freeze, four things must change:
- N1: tie Q1's model-test status to the small-n predictions, by a label or a condition on ΔF_pred(4) and ΔF_pred(8), and correct the C-1(b) justification.
- N2: make the stopping rule binding, or drop `--dry-run`; anchor the log in `job.json`; and implement the deviations exactly as written.
- N3: write definite sentences for the "not demonstrated" readings of both H1 and H4.
- N4: date-verify the history path of the execution-time calibration, and stop `--fetch` from overwriting it.

These are text changes plus small code and test changes. The minor findings N5–N9 should be fixed in the same pass, since they cost little.

Once they are made, the tests and `ghz3_d4.py` should be rerun. `certs/power.json` will change only if a study file changes. A short targeted check of the changed lines should follow, because in earlier rounds the new defects sat in the repair text. After that, the design can be frozen.
