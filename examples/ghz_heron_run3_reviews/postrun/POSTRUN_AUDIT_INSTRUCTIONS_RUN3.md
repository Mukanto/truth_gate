# Blind post-run audit: GHZ run 3

You are an independent auditor of a pre-registered hardware study. You did not design it, and you have not seen any
earlier review or audit of it. The study ran once on IBM quantum hardware (job `dbtecsfasvbs73b9l4e0`, ibm_kingston,
2026-11-16). Your job:
* find defects that could change a verdict or its reading;
* recompute the verdicts from the raw data;
* then check the designer's draft report against the files.

All paths below are relative to this task folder (the folder that holds this file). Read nothing outside it, with one
exception: you may execute the Python interpreter `E:\Claude Projects\.venv-qiskit\Scripts\python.exe` (it has qiskit,
qiskit-aer, numpy, scipy). Do not open, list or search any other file under `E:\Claude Projects\`. No git commands, no
network, nothing against the IBM service.

## Files you may read

* `examples\ghz_heron_run3\`:
  * `PREREG.md` (the binding pre-registration) and the study code (`ghz2_core.py`, `ghz2_study.py`, `ghz3_*.py`,
    `tests_ghz3.py`);
  * the raw data in `run\`: counts, job record, snapshot, model, calibration check, power file, log, and the
    execution-time calibration;
  * the official results `RESULTS_GHZ3.json`, `RESULTS_GHZ3.md`, `RESULTS_GHZ3_boot.npz`, written by the frozen analysis;
  * `certs\power.json` and `certs\k2_sim.json`.
* `examples\ghz_heron_run2\` and `examples\ghz_heron\`: the earlier runs' pre-registrations, code, data, results and
  reports (reference).
* `protocol\PROTOCOL.md`.
* **Only after part 1 is written:** `report\REPORT_draft.md`, the designer's draft report.

Some files were withheld from this folder on purpose: the gate certificates, the revision logs, the freeze manifests,
the earlier audits and reviews, and a separate recomputation. If you notice a reference to one of them, ignore it. If
you see one by accident, say so at the top of your report.

If you want to run code, copy what you need into `scratch\` and run it there. The frozen analysis script refuses to run
here without its freeze manifest; write your own scripts (importing the study's `ghz2_core.py` is allowed).

## Part 1: audit (before reading the draft report)

1. **Recompute** from `run\counts.json` and `run\model.json`:
   * P, C, F per n and their predictions;
   * the four criteria H1–H4 as PREREG §4 defines them;
   * the readings (power at submission from `run\power_run3.json`; the "within drift" labels with σ_d,F and σ_d,R as
     defined);
   * the answer assembled by the §4 tables;
   * C-1 as §1 defines it.

   Do the official results follow the pre-registered rules?
2. **Conditions and controls.**
   * Were C-1, C-2, K1, K2 and K3 applied as written?
   * Was the execution-time calibration rule (§3) applied correctly? Check `run\execution_calibration_*.json` against
     the snapshot.
   * Was the stopping rule followed? Check the log against `run\job.json`.
3. **Does the verdict follow, and are the readings right?** Consider the drift label, the power reading, H2 and H3 as
   reported rather than confirmatory, and the Q1/Q2 sentences. Would a reasonable alternative reading allowed by the
   text give another answer?
4. **Anything else** that weakens what may be claimed from this run, with a concrete failure scenario.

## Part 2: the draft report

Then read `report\REPORT_draft.md`. List every statement that the files contradict or do not support (section,
statement, what you found). Separately, list any interpretation that goes beyond what the run can show.

## Output (write only these two files, in `out\`)

* `out\AUDIT.json`, with three parts:
  * `"part1"`: a list of `{"id": "A1", "severity": "high|medium|low", "location": "...", "claim": "...",
    "failure_scenario": "...", "verdict_impact": "..."}`;
  * `"recomputed"`: your verdicts and key numbers;
  * `"part2"`: a list of `{"section": "...", "statement": "...", "finding": "..."}`.
* `out\AUDIT_blind.md`, in prose:
  * the part 1 table, sorted by severity, then what you checked and found sound;
  * the part 2 list.

Severities:
* **high:** could change a verdict or its reading;
* **medium:** weakens the claim or a qualifier;
* **low:** clarity.

## Working rules

* Write nothing outside `out\` and `scratch\`.
* Context-mode tools, if present:
  * do not call `ctx_search` unless with a `source` filter naming a label you indexed yourself in this task;
  * do not call `ctx_batch_execute` or `ctx_index`.
* Do not use a session scratchpad folder.
* Do not start other agents.

## Final message

Give the counts per severity, your recomputed verdicts, and the number of part 2 items, in a few lines. Confirm that you
read the draft report only after writing part 1, ran nothing against the IBM service, started no agent, used no git, and
wrote no file other than your outputs and scratch files.
