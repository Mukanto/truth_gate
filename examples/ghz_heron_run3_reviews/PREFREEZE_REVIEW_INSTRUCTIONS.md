# Instructions for the blind pre-freeze reviewer of GHZ run 3

You are the **blind pre-freeze reviewer** of a pre-registered hardware study. You wrote no part of it. The study is
"GHZ run 3" (`examples\ghz_heron_run3\`): the frozen design of an earlier run (run 2) is to be run once more on IBM
quantum hardware after a new device calibration, as an out-of-sample test of a calibration-based error model (M2). The
design is not frozen yet. Your review comes before the freeze, so a defect you find can still be fixed. Nothing has been
run on hardware for run 3.

All paths below are relative to this task folder (the folder that holds this file). Read nothing outside it, with one
exception: you may execute the Python interpreter `E:\Claude Projects\.venv-qiskit\Scripts\python.exe` (it has qiskit,
qiskit-aer, qiskit-ibm-runtime, numpy, scipy and the public package truth_gate). Do not open, list or search any other
file under `E:\Claude Projects\`.

## What you may read

* `examples\ghz_heron_run3\`: `PREREG.md` (binding text under review), `README.md`, `REVISIONS.md`, the code
  (`ghz2_core.py`, `ghz2_study.py`, `ghz3_*.py`, `tests_ghz3.py`) and `certs\` (Truth_Gate certificates, `k2_sim.json`,
  `power.json`).
* `examples\ghz_heron_run2\`: the frozen run 2: `PREREG.md`, `README.md`, `REVISIONS.md`, `REPORT.md`, `AUDIT_blind.md`,
  code, `FREEZE_GHZ2.json`, results (`RESULTS_GHZ2.*`), `certs\` and `run\`.
* `examples\ghz_heron\`: run 1, the same kinds of files.
* `protocol\PROTOCOL.md` and `protocol\CHECKLIST.md`: the methods protocol the study follows (rules 2, 4, 9, 13–16
  matter most).
* `docs\GATE.md`: the Truth_Gate documentation (flags, verdicts).

If you want to run code, first copy the `examples` folder into `scratch\` and run it there with the interpreter above.
Never run against the real IBM service: no `--dry-run`, `--submit` or `--fetch`, and no network access. Offline tests,
the simulator script `ghz3_d4.py`, `--selftest` and your own checks are fine.

## What to review

Report every defect you find, in particular:

1. **Code against text.** Does the code implement `PREREG.md` exactly? Consider:
   * the conditions C-1 (new calibration) and C-2 (quota);
   * the criteria H1–H4;
   * the controls K1–K3;
   * the analysis and its headline;
   * the power computation and its reading ("not demonstrated").

   Is any rule in the text ambiguous enough that the analysis could be bent after the data?
2. **Code identity.** `ghz2_core.py` and `ghz2_study.py` must be byte-identical to run 2's frozen files. Check the hashes
   against `examples\ghz_heron_run2\FREEZE_GHZ2.json`.
3. **H4 and its Truth_Gate study.** Check the criterion, the worlds, the control and the certificate. Can H4 fail
   (protocol rule 14)? Does the control model a plausible real failure? Are the dispositions proposed for the certificate
   flags in `REVISIONS.md` sound?
4. **Power (rule 16).** Is the expected scenario a sound and fair basis? Is the simulation a valid stand-in for
   multinomial shot noise plus between-run drift? Are the resulting readings right for each criterion?
5. **Informativeness.** Could this run again be uninformative, as run 2 turned out to be? Run 2's report lists the
   reasons: the same calibration, drift larger than shot noise, power, identification, a useless control. Does C-1
   really guarantee a new calibration? Is anything still missing that would make a HOLDS or a FAILS uninterpretable?
6. **Protocol and integrity.** Check compliance with the protocol rules; the refusal paths (nothing is submitted when a
   condition fails); and that no secret or key could end up in a file.

For each finding, give a severity:
* **blocking:** the run should not be frozen as is;
* **major:** should be fixed before the freeze;
* **minor:** wording or a small improvement.

## Output (write only these two files, in `out\`)

* `out\REVIEW.json`: a list of `{"id": "F1", "severity": "blocking|major|minor", "file": "...", "location": "...",
  "finding": "...", "evidence": "...", "suggested_fix": "..."}`. Use an empty list if there are no findings.
* `out\REVIEW.md`: the same in prose, then a short overall judgement: can the design be frozen after the fixes?

## Working rules

* Write nothing outside `out\` and `scratch\`. No git commands.
* Context-mode tools, if present:
  * do not call `ctx_search` unless with a `source` filter naming a label you indexed yourself in this task;
  * do not call `ctx_batch_execute` or `ctx_index`.
* If the harness suggests a session scratchpad folder, do not use it; use `scratch\`.
* Do not start other agents.

## Final message

Give the counts per severity and the IDs of blocking and major findings in a few lines. Confirm that you ran nothing
against the real IBM service, started no agent, and wrote no file other than your two outputs and your scratch files.
