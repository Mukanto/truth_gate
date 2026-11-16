# Instructions for the second look at GHZ run 3 (targeted, before the freeze)

You are a **fresh reviewer** of a pre-registered hardware study. You wrote no part of it, and you are not the first
reviewer. The study is "GHZ run 3" (`examples\ghz_heron_run3\`): the frozen design of an earlier run (run 2) is to be run
once more on IBM quantum hardware after a new device calibration, as an out-of-sample test of a calibration-based error
model (M2).

A first blind review of version 1 found 20 defects (`first_review\REVIEW.json`, `first_review\REVIEW.md`). The designer
accepted all of them, rewrote the pre-registration as version 2, and had the code changed. `REVISIONS.md` in the study
folder gives the response to each finding and the later clarifications. Your job is a targeted second look before the
freeze:
* is each fix adequate?
* did the fixes introduce new defects?

All paths below are relative to this task folder (the folder that holds this file). Read nothing outside it, with one
exception: you may execute the Python interpreter `E:\Claude Projects\.venv-qiskit\Scripts\python.exe` (it has qiskit,
qiskit-aer, qiskit-ibm-runtime, numpy, scipy and the public package truth_gate). Do not open, list or search any other
file under `E:\Claude Projects\`.

## What you may read

* `examples\ghz_heron_run3\`: `PREREG.md` (version 2, binding text under review), `README.md`, `REVISIONS.md`, the code
  and `certs\`.
* `examples\ghz_heron_run2\` and `examples\ghz_heron\`: the frozen runs 2 and 1 (reference only).
* `first_review\`: the first reviewer's outputs.
* `protocol\PROTOCOL.md`, `protocol\CHECKLIST.md`, `docs\GATE.md`.

If you want to run code, first copy the `examples` folder into `scratch\`, make the copy writable, and run it there with
the interpreter above. Never run against the real IBM service: no `--dry-run`, `--submit` or `--fetch` against the
service, and no network access. Offline tests, `ghz3_d4.py`, `--selftest` and your own checks are fine.

## What to check

1. **Each first-review finding.** For each of F1–F20, check the fix in the text and in the code. Mark it "fixed",
   "partly fixed" or "not fixed", with the evidence. Look hardest at:
   * F1: power is defined per criterion at a stated effect and computed at submission;
   * F2: C-1 uses the M2 inputs and a minimum change in the predictions;
   * F3: the freeze list and missing files;
   * F8: the execution-time calibration, including the fallback;
   * F9: the stopping rule and the log.
2. **New defects.** Look for anything the version 2 changes broke or added:
   * text and code that disagree;
   * a reading that could still be chosen after the data;
   * a refusal path that writes or submits;
   * a secret that could reach a file or the output;
   * a test that does not test what it claims.
3. **Freezability.** After your look, can the design be frozen as is? If not, what exactly must change first?

Severity for a new finding:
* **blocking:** do not freeze;
* **major:** fix before the freeze;
* **minor:** wording or a small improvement.

## Output (write only these two files, in `out\`)

* `out\SECOND_LOOK.json`, with two parts:
  * `"first_review"`: a list of `{"id": "F1", "status": "fixed|partly fixed|not fixed", "evidence": "..."}` for F1–F20;
  * `"new_findings"`: a list of `{"id": "N1", "severity": "blocking|major|minor", "file": "...", "location": "...",
    "finding": "...", "evidence": "...", "suggested_fix": "..."}`, or an empty list.
* `out\SECOND_LOOK.md`: the same in prose, and a one-paragraph judgement on freezability.

## Working rules

* Write nothing outside `out\` and `scratch\`. No git commands.
* Context-mode tools, if present:
  * do not call `ctx_search` unless with a `source` filter naming a label you indexed yourself in this task;
  * do not call `ctx_batch_execute` or `ctx_index`.
* If the harness suggests a session scratchpad folder, do not use it; use `scratch\`.
* Do not start other agents.

## Final message

Give the counts in a few lines: how many first-review findings are fixed, partly fixed and not fixed, and the new
findings per severity. Confirm that you ran nothing against the real IBM service, started no agent, and wrote no file
other than your two outputs and your scratch files.
