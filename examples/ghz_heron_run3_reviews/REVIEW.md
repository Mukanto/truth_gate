# Blind pre-freeze review: GHZ run 3

Reviewer: fresh agent, blind to the design work. Inputs read: only the task folder. The only other thing used was the
venv interpreter, run on a scratch copy of `examples\`. Nothing was run against the IBM service, and no network was used.

## What I checked, and what held

- **Code identity holds.** `ghz2_core.py` and `ghz2_study.py` in run 3 are byte-identical to run 2's files. Their
  SHA-256 (5318b041… and 4bf9f2ec…) equal `FREEZE_GHZ2.json`. All 13 entries of run 2's manifest still match their files.
- **The wrapper diff list matches the code.** In `ghz3_run.py`, the functions `build_and_report`, `heron_r2_basis`,
  `pick_backend`, `cmd_fetch` and `_service` are unchanged from `ghz2_run.py`, as the README states.
- **Tests and simulator checks pass.** `tests_ghz3.py`: 38 tests, all OK. Rerunning `ghz3_d4.py` reproduces
  `certs/power.json` and `certs/k2_sim.json` byte for byte, with budget OK, K2 PASS, D4 clean and rule 14 yes on
  FakeKingston.
- **The power numbers are confirmed independently.** My own reimplementation of the power simulation reproduces
  power.json exactly with the same seed (0.2315, 0.911, 0.1425, 0.992), and agrees within Monte Carlo error with other
  seeds.
- **Both certificates re-verify.** `truth_gate verify` reproduces both body hashes: H4 ff4351e2…, H1–H3 b42bc703….
  REVISIONS.md describes the certificates correctly.
- **Code implements the text** for C-1 and C-2, K1, the two K3 additions, H4, the headline items and the power reading.
  Where the code does exactly what the text says, the defects below are defects of the text.
- **Refusal paths are correct.** Nothing is written and nothing is submitted when the freeze or code identity fails
  (exit 3), D-7 fails (4), C-1 fails or its reference is missing (5), C-2 fails (6), or the quota is missing or invalid
  (7). No credential reaches any file.

My scratch scripts are `scratch\check_power.py` and `scratch\check_c1.py`.

## Blocking

**F1. The power reading (rule 16) is misapplied: wrong for H1, fragile for H2.** The PREREG uses
P(HOLDS | expected scenario) as "power" for every criterion. A FAILS with P(HOLDS) < 0.8 then reads "not demonstrated".

- **H1.** The expected scenario already breaks H1's claim: |ΔF| = 0.045 at n = 4 and 0.055 at n = 8, against a band of
  0.05. So the 0.23 is a false-HOLDS rate, not power. Under the scenario in which H1's claim is true (truth equals the
  prediction), P(HOLDS) = 1.000. With truth inside the band (|ΔF| = 0.03), it is 0.88. Yet the rule labels any H1 FAILS
  "not demonstrated" in advance, so H1 can never be refuted. This contradicts the PREREG's own sentence that H1's band
  "covers a calibration change and run-to-run drift by design".
- **H2.** The recorded 0.911 comes from run 2's knife-edge prediction: F_pred(24) = 0.589 against the threshold
  0.5/R(24) ≈ 0.579. Scaling the predictions by k = 0.98 gives 0.43; k = 0.96 gives 0.05.
- **Size of a realistic calibration change.** FakeKingston is an earlier stored calibration of the same device, and the
  same 48 qubits are selected. There, M2's F_pred is lower by 0.05–0.10 at every n, with F_pred(24) = 0.516. Under the
  expected ratios H2 would then FAIL almost surely, and the rule would read that as a genuine failure, because 0.911 ≥ 0.8.
- **Device change.** If the least busy device is not ibm_kingston (I-6), the scenario does not apply at all.

Fix:
- Define power per criterion as P(HOLDS | the claim is true at a stated effect).
- Report P(HOLDS | expected scenario) separately, as the expected outcome, not as power.
- Compute both at `--submit` from the new snapshot's predictions: same method and seed, written to `run/power_run3.json`
  before submission, with its hash in `job.json`. The analysis reads that file.

**F2. C-1 does not guarantee a model test.** C-1 passes if any of 1132 values changes anywhere on the chip. Only 334 of
those values belong to the 48 selected qubits and their tree edges. I changed T1 on qubit 0, outside the patch, by 0.01%:
C-1 passes, and M2's predictions change by exactly 0. The run could again be a data replicate for M2, which is the
rule-2 failure this run exists to avoid. And since "model test" has no operational definition, either label could be
argued after the data.

Fix:
- Restrict C-1 to the values that enter M2: the model components of S_48 and its tree edges.
- Require a minimum change in the predictions, fixed now: for example max_n |ΔF_pred| ≥ 0.01, or ≥ 0.022 if the change
  must be visible above run-to-run drift.
- Optionally pre-register a descriptive tracking table: measured change against predicted change, run 2 → run 3, per n.

## Major

- **F3. The freeze leaves out files that decide the reading.**
  - `REQUIRED_FROZEN_3` lists six files. It omits `certs/power.json`, which decides "not demonstrated" versus a failure,
    and `certs/k2_sim.json`. It also omits `ghz3_d4.py`, the certificates, README, REVISIONS and the tests. Run 2's
    manifest had 13 files.
  - If `k2_sim.json` is missing, K2 counts as not failed and the run stays "interpretable".
  - Fix: add these files to the required list, and treat a missing K2 or power file as a failure.
- **F4. There is no verdict mapping (rule 3).**
  - No combination of H1/H2/H3/H4 outcomes answers "does M2 hold on a new calibration?". H1 and H4 can both hold, so the
    narrative can be chosen after the data.
  - Fix: a table mapping each outcome combination to one pre-written sentence.
- **F5. H1 will again be decided by drift** (run 2's audit F3, not repaired).
  - The expected deviation sits on the band edge, and the spread of F_hat is 0.012–0.014, mostly drift. P(HOLDS) is
    0.20–0.33 depending on the drift model.
  - The claim "covers drift by design" is not supported. Reporting run 2's drift next to H1 invites a post-hoc discount.
  - Fix: pre-register the expected coin-flip character and readings for both outcomes, including a "within drift" label.
- **F6. H2 tests where the grid falls** (run 2's audit F6, not repaired).
  - With M2 overpredicting F(24) by 14%, H2 still holds 91% of the time. It separates "M2 exact" from "M2 14% too high"
    with only 9% probability.
  - Its outcome is set by where F_pred(24) of the new snapshot lands, which is known before the data.
  - Fix: demote H2 to reported, or make its interpretation conditional on the expected crossing lying away from a grid
    edge, computed at submission.
- **F7. H3 stays confirmatory at 14% power.**
  - About 3× run 2's effect would be needed for 80%. The rule-15 identification is still incomplete (run 2's audit F5:
    Z-type versus X-type and leakage errors, correlated readout).
  - Fix: demote it to exploratory, or change the design, and add the list of error classes.
- **F8. The calibration at execution is not checked.**
  - The job may run after a recalibration. M2 would then describe a different calibration from the data.
  - No execution timestamps or execution-time properties are recorded, and K3 has no item for this.
  - Fix: record the job's timestamps and the properties at execution in `--fetch`, compare the M2 inputs, and add a K3
    item or a pre-registered reading.
- **F9. Submission timing is a forking path.**
  - `--dry-run` can be repeated across calibrations and leaves no record. It prints M2's predictions, which together with
    the known ratios largely predict H1 and H2. Both retry clauses allow waiting.
  - Fix: a stopping rule (submit at the first eligible dry-run) and an append-only dry-run log.
- **F10. H4 relies on shot noise only while drift is 3× larger at small n** (rule 9).
  - Under the expected ratios this is robust: a margin of about 3 drift sd, P(HOLDS) 0.99, and 0.89 with drift doubled.
  - But if the new calibration brings R(4) or R(8) near 1, drift decides the verdict. The PREREG gives no drift reading
    for H4.
  - Fix: report the H4 margin against the drift sd, with a pre-registered "holds within drift" reading.

## Minor

- **F11. The drift model in the power simulation is crude.**
  - Each sd is a single difference (1 degree of freedom), giving values near zero at large n.
  - Shot noise is counted twice.
  - Drift is independent across n and between P and C, although the qubit sets are nested.
  - It is same-calibration drift, standing in for variation between calibrations.
  - The shot-noise part is valid, and no reading changes at the stand-in predictions.
- **F12. H4's K5 dispositions are sound,** but the probes never tested vacuity.
  - H4 holds on any data below the prediction, including a fully decohered output.
  - Add an interpretation: H4 HOLDS means "M2 underestimates the error" and attributes no cause.
  - The control is plausible, H4 can fail (rule 14), and the control largely repeats the minus world.
- **F13. Rule 14 for H1 is checked on FakeKingston only,** not on the real run-3 snapshot. Run 2 required the check on
  the snapshot, with a one-sided label if it fails.
- **F14. H1 UNDEFINED: text and frozen code differ.** The text says "any F_pred"; the code checks only n = 4 and 8.
  There is no practical effect.
- **F15. C-2 wording.** The code uses the estimate computed at submission, not the dry-run estimate. No hard limit on the
  job's execution time is set.
- **F16.** The PREREG says the power uses "run-2 data only", but it also uses run 1's data.
- **F17.** The bit-order control is declared uninformative but is still inside K2's pass condition.
- **F18.** The K3 C-1 item trusts the stored flag. The independent recomputation and the run-2 snapshot hash are not
  required.
- **F19.** The redaction in `_print_usage` works by key name only. Output goes to stdout only; no secret reaches any file.
- **F20.** A submission that fails after the run/ files are written leaves them without `job.json`, and a retry
  overwrites them.

## Overall judgement

**Not freezable as is. Freezable after F1 and F2 are fixed and the major findings are resolved.**

Most fixes are text: readings, a verdict mapping, a stopping rule, demotions. The rest are small code changes: a stronger
C-1, a power file computed at submission, a fuller freeze list, and an execution-time calibration check. None needs a
change to the frozen `ghz2_core.py` or `ghz2_study.py`.

The designer's own expected scenario shows how much informativeness is at stake:

- **H1** is a coin flip decided by drift.
- **H2** is decided by where the new prediction falls on the grid.
- **H3** has 14% power.
- **H4** holds with about 99% probability.

Without these changes, only a FAILS of H4 and the descriptive R table would carry new information, and C-1 does not even
guarantee that M2's predictions differ from run 2's. With a C-1 tied to a real change in the predictions, readings
computed on the new snapshot, and a pre-registered tracking comparison, run 3 would be a genuine and interpretable model
test.
