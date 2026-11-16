# Revisions before the freeze, with reasons

Run 3, implementation stage (offline). Truth_Gate 0.5.0 (the repo's, `tool_version` 0.5.0, spec 0.7). The designer decides each
flag below; the coder made **no change** to `ghz3_study_h4.py` in response to a certificate and did **not** touch
`ghz2_study.py`.

## `ghz3_study_h4.py`: certificate v1

`python -m truth_gate check ghz3_study_h4.py --out certs/cert_h4_v1.json` (full mode, 200 samples per stream).
`certs/cert_h4_v1.json`, body_sha256 `ff4351e217cb9d13c8921e5d2cb9d1830a740b637d061dcee0db9bd88da5fb4f`, overall **WEAK**, no study flags.

| # | Criterion | Flag | Coder's change | Proposed disposition (designer decides) |
|---|---|---|---|---|
| 1 | H4 | K5_INCONCLUSIVE:noise (UNDEFINED on 200 of 200 noise probes) | none | **reject**, same root as run 2's rejected K5 flags (run 2 REVISIONS, flags after cert v1) |
| 2 | H4 | K5_INCONCLUSIVE:zeros (UNDEFINED on 200 of 200 zero probes) | none | **reject**, same reason |

Reason for the proposed rejection: the probes replace the data by noise or zeros, so `F_pred` leaves (0, 1) or `F_boot` is <= 0.
PREREG section 4 pre-registers UNDEFINED for exactly these inputs, so H4 abstains there by definition. The only way to clear the
flag would be to change the claim's rule (for example to return FAILS on such input), which is outside the coder's remit.
Worlds and control behave as designed: `plus` HOLDS on 200 of 200, `minus` HOLDS on 0 of 200, the control
`accurate_small_n_too_high_large_n` HOLDS on 0 of 200 (it must fail the criterion), no abstention on any of the three.

## `ghz2_study.py` (H1-H3, unchanged): certificate with Truth_Gate 0.5.0

`certs/cert_h123_v1.json`, body_sha256 `b42bc70384f93032a8c3c413dad4bebf8763682e2ae5fb70d2c6ca44c3e8baaf`, overall **WEAK**,
no study flags. `ghz2_study.py` is byte-identical to run 2's, whatever the result.

| # | Criterion | Flag | Coder's change | Note |
|---|---|---|---|---|
| 3 | H1 | K5_INCONCLUSIVE:noise (172 of 200 UNDEFINED), K5_INCONCLUSIVE:zeros (200 of 200) | none (file is frozen) | the same two flags, same cause, as run 2's frozen WEAK status |
| 4 | H2 | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros (200 of 200 each) | none | same |
| 5 | H3 | K5_INCONCLUSIVE:noise, K5_INCONCLUSIVE:zeros (200 of 200 each) | none | same |

No new flag appeared with 0.5.0 compared with run 2's cert_v3 (WEAK, only the rejected K5_INCONCLUSIVE flags); the 0.5.0
abstention rule (`None` = no claim) adds no `K1_ABSTAINED` information flag on the plus or minus worlds of any of the four criteria.

## Implementation notes that are not certificate-driven

Departures from run 2 and open choices of the coder are listed in `README.md` (diff list) and in the coder's report; none is a
change to a pre-registered rule.

## Designer's decisions on the coder's open points (Claude, under the author's delegation)

* **Flags 1–5 (`K5_INCONCLUSIVE:noise`, `K5_INCONCLUSIVE:zeros` on H1–H4): rejected, no change.** The probes replace `F_pred`
  as well, so each criterion abstains by its own pre-registered domain rule (the same root as run 2's rejected K5 flags).
  The consequence is that the gate could not test H4 for vacuity on the probes; the worlds (`plus` holds 200/200, `minus`
  0/200) and the control (0/200) do (reviewer, F12).
* **Run 1's R under M2:** the analysis uses the values recomputed with the frozen code from run 1's counts and snapshot
  (0.977, 0.963, 0.874, 0.858, 0.854). Run 2's PREREG §0 quoted 0.98, 0.96, 0.87, 0.85, 0.84; the n = 48 quote is 0.014
  lower than the recomputed value. The quoted values are a fallback only, labelled.
* **C-1 fields:** replaced by the v2 rule (F2 below).
* **C-2 float boundary:** no tolerance; the comparison is `1.15 × estimate ≤ N` as written.
* **Power and study hashes:** `ghz3_d4.py` is rerun whenever a study file changes before the freeze; the freeze lists
  `certs/power.json` (F3).
* **Exit code 4 for the time budget:** accepted (run 2 exited with code 1 and a message).

## v1 → v2: blind pre-freeze review (2026-11-16)

A fresh agent (Claude Opus 5.5) that wrote no part of the study reviewed PREREG v1 and the code. It worked on read-only
copies in a separate session and reran the tests, `ghz3_d4.py` and its own checks offline. It found 2 blocking, 8 major
and 10 minor findings, and judged the design not freezable as is. Every finding was accepted.

| # | Severity | Finding (short) | v2 response |
|---|---|---|---|
| F1 | blocking | P(HOLDS \| expected scenario) was used as power. For H1 it is a false-HOLDS rate; H2's 0.91 sits on a knife edge. | Power is now defined per criterion at a stated effect (H1: F_true = F_pred − 0.03 at n = 4, 8; H4: run-2 ratios). The expected outcome is reported separately. Both are computed at submission from the new predictions (`run/power_run3.json`, hash in `job.json`). A device change is labelled. |
| F2 | blocking | C-1 passed if any of 1132 chip-wide values changed, even with no change in M2's predictions. | C-1 now uses the M2 inputs of S_48 and its tree, and requires max_n \|ΔF_pred\| ≥ 0.02. A tracking row (measured against predicted change) is added. |
| F3 | major | The freeze list left out `power.json`, `k2_sim.json`, d4, the certificates, README, REVISIONS and the tests. A missing K2 file counted as a pass. | Every file of the folder is frozen. A missing K2 file is a K2 failure. A missing power file allows no "fails" reading. |
| F4 | major | No verdict mapping (rule 3). | A mapping table for (H1, H4), with labels. |
| F5 | major | H1 is decided by drift under the expected scenario; "covers drift by design" was unsupported. | The sentence was removed. A pre-registered "within drift" label was added, with a σ_d,F defined now. H1's power is at a stated effect. |
| F6 | major | H2 tests where the grid falls. | Demoted to reported; the CI-based reach and the interpolated crossing are reported. |
| F7 | major | H3 is underpowered and its identification (rule 15) incomplete. | Demoted to reported (exploratory). The rule-15 list of error classes is in §4. |
| F8 | major | No check that the calibration in force at execution is the snapshot's. | `--fetch` saves the execution timestamps and the execution-time properties. The analysis uses M2 on the execution-time calibration if it differs, labelled; the snapshot's predictions are then secondary. |
| F9 | major | Submission time is a forking path: `--dry-run` printed predictions and left no trace. | Stopping rule (first passing `--submit` is the run; retry at most once per UTC day; submit within 2 h of a passing dry-run). `--dry-run` prints no prediction, and every dry-run or refusal is logged to `run/dryrun_log.jsonl`. |
| F10 | major | H4's percentile reflects shot noise only; near R = 1 drift decides it. | The margins are reported next to σ_d,R(n), with "holds within drift" and "fails within drift" labels. |
| F11 | minor | The drift sd was crude (1 df, shot noise counted twice, independent across n). | Pooled relative drift, shot-noise corrected. Sensitivity rows: fully correlated drift, drift × 2. |
| F12 | minor | The K5 rejection is sound, but the gate never tested H4 for vacuity. | Recorded above and in §7; I-7 added. |
| F13 | minor | The rule-14 check for H1 ran only on FakeKingston. | Now checked at submission on the new snapshot, rechecked in the analysis; "H1 one-sided" label. |
| F14 | minor | H1's UNDEFINED text did not match the frozen code. | Text now says "F_pred at n = 4 or 8 outside (0, 1)". |
| F15 | minor | "Dry-run estimate" vs the estimate at submission; no execution-time limit. | Text says "the estimate computed at submission" and states why no execution limit is set. |
| F16 | minor | Wording: power also reads run 1's data. | Fixed in §4 (pooled drift from runs 1 and 2). |
| F17 | minor | The uninformative bit-order control was inside K2's pass condition. | It is reported, not part of K2's pass condition. |
| F18 | minor | K3 trusted the stored C-1 flag and did not check the run-2 hash. | K3 recomputes C-1 and checks the run-2 snapshot and model hashes. |
| F19 | minor | Usage output was only partly redacted. | Only a whitelist of numeric usage fields is printed. |
| F20 | minor | A failed `_submit_job` left `run/` partly written. | Atomic writes: temporary folder, moved into `run/` after the job id is returned. |

## v2 clarifications after implementation (designer, before the second look)

The coder implemented v2 and raised eight points. The designer's answers, written into PREREG v2 where they change the
text:

1. **H4 "within drift" labels.** Each n is compared with its own σ_d,R(n). "Holds within drift" applies if the margin is
   below 2σ_d,R(n) at some n. "Fails within drift" applies if, at every n where q97.5(n) ≥ 1, the excess is below
   2σ_d,R(n). The text now says so (§4).
2. **Mapping.** A row for H1 and H4 both UNDEFINED was added ("Neither Q1 nor Q2 is answered"). The "not demonstrated"
   row keeps the sentence of the row it modifies.
3. **Missing power file.** It is a K3 failure (yorumlanamaz). The earlier sentence that a missing file only restricts
   the reading contradicted the K3 item and was removed (§5).
4. **Rule-14 label.** It applies if the check fails on the snapshot's predictions or on the predictions in use (§1).
5. **Stopping rule.** The code logs the timing parts and does not enforce them; deviations are reported (§1).
6. **Log lines.** Accepted submissions and refusals for a missing quota or an existing `job.json` are also logged.
   Accepted.
7. **Coder's choices.** Relative shot variance v_X with ddof = 1. H2's interpolated crossing is linear in n, with its CI
   from the same interpolation applied to each bootstrap replicate. Accepted; run 2 reported no crossing.
8. **Relative layout.** The analysis needs `../ghz_heron/` and `../ghz_heron_run2/` beside this folder. Accepted; they are
   in the repository.

Added after the coder noted that the calibration-history query may be unavailable on the cloud service (§3). "Equal"
means within a relative tolerance of 1e-6. A fallback, used when the history query is not available, verifies "no
recalibration since submission" from the current calibration's dates.

## v2 → v3: targeted second look (2026-11-16)

A second fresh agent (Claude Opus 5.5), neither the first reviewer nor an author, checked the v2 fixes on read-only
copies. Of the 20 first-review findings it marked 16 fixed and 4 partly fixed (F2, F4, F8, F9). It added 4 major and 5
minor findings, none blocking, and judged the design freezable after the changes below. Every new finding was accepted.
(It ran one read-only `git status`, against its no-git rule; the folder is not a repository and nothing changed.)

| # | Severity | Finding (short) | v3 response |
|---|---|---|---|
| N1 (F2) | major | C-1(b) takes the maximum over all n, but H1 reads only n = 4 and 8; small-n predictions can stay run 2's. | C-1 per question: Q1 is a model test only if max(\|ΔF_pred(4)\|, \|ΔF_pred(8)\|) ≥ 0.02; otherwise a fixed replicate label. The justification of 0.02 is reworded. |
| N2 (F9) | major | The stopping rule left waiting open; predictions were logged in clear; the deviation report missed and over-reported cases; the log was not anchored. | A passing dry-run is binding (a submit within 2 h, else a deviation). Attempts and the retry limit are defined exactly. The log holds the predictions' SHA-256, not the predictions. `job.json` anchors the log's SHA-256 and line count. |
| N3 (F4) | major | The "not demonstrated" row was a meta-instruction, and H4's reading was ignored. | The answer is assembled from a Q1 sentence (H1 outcome and reading), a Q2 sentence (H4 outcome and reading), a joint sentence for the four definite combinations, and the labels. Every sentence is pre-written. |
| N4 (F8) | major | The history path had no date check; a datetime ignored by the service could make a later calibration primary; `--fetch` overwrote. | The history result is accepted only if its M2-input dates are at or before the execution start. "Changed" requires later dates than at submission (dates recorded at submission). `--fetch` keeps every attempt and uses the first. |
| N5 | minor | The power-file hashes were compared with current files; power was not recomputed; which power applies under §3 was not stated. | Hashes are compared with the frozen `certs/power.json` and `FREEZE_GHZ3.json`. The analysis recomputes power and requires equality. The readings use the submission power on the snapshot's predictions in every §3 case. |
| N6 | minor | Some tests did not test what they claimed (stubbed printing, a tautology, the freeze list); a raw quota string reached the log. | The tests are to be fixed; the parsed quota is logged. |
| N7 | minor | A submit exception was treated as "nothing submitted"; files were deleted; an interrupt was not logged. | The temporary folder is kept and renamed. BaseException is logged. Before a retry the author checks the job list, and `--recover JOBID` covers the case where a job exists. |
| N8 | minor | H3's error-class list omitted independent readout error beyond the model. | Added to the opposite-direction classes. |
| N9 | minor | Wording points: the (FAILS, FAILS) sentence, K2 on FakeKingston's circuits, a d4 docstring, the tracking CI, the REVISIONS F3 row. | The joint sentence is reworded. K2 is binding in the analysis on the submitted circuits. The docstring is to be fixed. The tracking row is labelled shot-noise-only, with σ_d,F next to it. The F3 row's "no fails reading" is superseded by clarification 3 (a missing power file is a K3 failure). |

## v3 final: narrow third look (2026-11-16)

A third fresh agent (Claude Opus 5.5) checked N1–N9 and the partly fixed F2, F4, F8 and F9, and found them all fixed. It
added 8 minor findings and judged the design freezable as is. To learn how the installed qiskit-ibm-runtime handles
calibration history, it disassembled the library code loaded in the permitted interpreter instead of opening the source
files. That code is public third-party code holding no designer knowledge; recorded here. The designer fixed all 8
findings before the freeze.

| # | Finding (short) | Response |
|---|---|---|
| T1 | A dry-run with a low quota (exit 6) was never binding; an interrupt after the checks left no trace; pre-check refusals wrote no line; the 2 h window used log-write times. | A dry-run passes on D-7, K2 and C-1, whatever C-2 says. A logged C-1 pass with a C-2 failure is reported with its quota. A "checks passed" line is written at once. The text covers only runs that reach the checks. The 2 h window runs between snapshot times. |
| T2 | Lines after the anchor were unchecked; fetch attempts left no trace. | A post-anchor line dated before the submission is a K3 failure. Each fetch is logged with its file name and hash, and the first logged attempt is required. `job.json` and the log are pushed right after submission (§8), as the anchor the author cannot rewrite. |
| T3 | `--recover` accepted any job id (for example run 2's job). | It refuses unless the backend, the creation time window and the 368 circuits match. A K3 item checks that the job was created and started after the submission. |
| T4 | Which predictions decide the Q1 label was unstated; wording. | The label is decided on the snapshot's predictions. The label and the Q1 sentences say "this run's calibration". |
| T5 | Stale "v2" strings; exit 8 vs re-raised interrupt. | Strings updated to v3 (`certs/power.json` regenerated). The text says "exit 8, or the interrupt is re-raised after logging". |
| T6 | A history result that passed the date check but could not be used did not fall through to the fallback. | Any failure of the history path falls through to the saved current calibration. |
| T7 | Exact power recomputation needs a bit-identical environment, and no versions were recorded. | Versions and platform are recorded in `power_run3.json` and `job.json`. The analysis runs in the same environment; a mismatch is reported as the cause. |
| T8 | The binding K2 ran only after the QPU time was spent. | K2 also runs in `--dry-run` and `--submit`; a failure refuses the attempt like D-7. The analysis's K2 stays binding. |

Round-4 implementation choices accepted by the designer:
* The checks run in the order D-7, K2, C-1, C-2. K2 refuses with exit 10.
* A `submit-failed` line written after the checks passed counts as a passing attempt. The "checks passed" line falls
  inside the anchor; the accepted line falls outside it.
* `--fetch` always saves the current calibration and logs every call.
* K2 takes about 30 s in `--dry-run` and `--submit`.

Added by the designer: a 10-minute clock tolerance for the job-time checks (K3 and `--recover`). The submission time is
taken from the local clock and the job times from the service; the nearest wrong job, run 2's, is days older.
