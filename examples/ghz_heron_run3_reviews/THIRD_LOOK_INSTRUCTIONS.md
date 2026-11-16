# Instructions for the third look at GHZ run 3 (narrow, before the freeze)

You are a **fresh reviewer** of a pre-registered hardware study. You wrote no part of it and you are neither of the two
earlier reviewers. The study is "GHZ run 3" (`examples\ghz_heron_run3\`): the frozen design of an earlier run (run 2)
is to be run once more on IBM quantum hardware after a new device calibration, as an out-of-sample test of a
calibration-based error model (M2).

Two reviews came before you:
* `reviews\REVIEW.*`: the first review, of version 1 (findings F1–F20);
* `reviews\SECOND_LOOK.*`: the second look, of version 2 (findings N1–N9).

The designer accepted every finding, wrote version 3 of the pre-registration and had the code changed. `REVISIONS.md`
records each response. Your look is **narrow**:
1. check that N1–N9 and the partly fixed F2, F4, F8 and F9 are now fixed, in the text and in the code;
2. look for new defects in the code that changed for version 3: the stopping-rule log and its deviation report, the
   answer assembly, the execution-time calibration and its date checks, `--recover`, the power-file checks, and the
   binding K2.

Do not repeat a full review of the design.

All paths below are relative to this task folder (the folder that holds this file). Read nothing outside it, with one
exception: you may execute the Python interpreter `E:\Claude Projects\.venv-qiskit\Scripts\python.exe` (it has qiskit,
qiskit-aer, qiskit-ibm-runtime, numpy, scipy and the public package truth_gate). Do not open, list or search any other
file under `E:\Claude Projects\`. No git commands.

## What you may read

* `examples\ghz_heron_run3\` (`PREREG.md` version 3, `README.md`, `REVISIONS.md`, code, `certs\`);
* `examples\ghz_heron_run2\` and `examples\ghz_heron\` (reference);
* `reviews\`;
* `protocol\PROTOCOL.md`, `docs\GATE.md`.

To run code, copy the `examples` folder into `scratch\`, make the copy writable, and run it there. Never run against the
real IBM service: no `--dry-run`, `--submit`, `--fetch` or `--recover` against the service, and no network access.

## Output (write only these two files, in `out\`)

* `out\THIRD_LOOK.json`, with three parts:
  * `"earlier_findings"`: a list of `{"id": "N1", "status": "fixed|partly fixed|not fixed", "evidence": "..."}` for
    N1–N9 and F2, F4, F8, F9;
  * `"new_findings"`: a list of `{"id": "T1", "severity": "blocking|major|minor", "file": "...", "location": "...",
    "finding": "...", "evidence": "...", "suggested_fix": "..."}`;
  * `"freezable_as_is"`: true or false.
* `out\THIRD_LOOK.md`: the same in prose, in a few pages at most.

Severities:
* **blocking:** do not freeze;
* **major:** fix before the freeze;
* **minor:** may be fixed or recorded as a known limitation.

## Working rules

* Write nothing outside `out\` and `scratch\`.
* Context-mode tools, if present:
  * do not call `ctx_search` unless with a `source` filter naming a label you indexed yourself in this task;
  * do not call `ctx_batch_execute` or `ctx_index`.
* If the harness suggests a session scratchpad folder, do not use it; use `scratch\`.
* Do not start other agents.

## Final message

Give the counts and `freezable_as_is` in a few lines. Confirm that you ran nothing against the real IBM service, started
no agent, used no git command, and wrote no file other than your two outputs and your scratch files.
