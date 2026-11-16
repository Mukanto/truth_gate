# Independent recomputation of GHZ run 3

`recompute_run3.py` recomputes the main numbers of run 3 (P, C, F, M2 predictions, bootstrap CIs,
H1-H4, K1, R(n), C-1, the F = 0.5 crossing) from the raw data in `../ghz_heron_run3/run/` and the
written specifications only (run 3, run 2 and run 1 PREREG.md).

How it was written: by a coding subagent that did not open or import any analysis, run or core code
of runs 1-3 and never opened RESULTS_GHZ3.json / .md / _boot.npz. Inputs read: PREREG files, counts.json,
job.json (manifest), model.json (run 3 and run 2), circuits.qpy (phase and ideal-parity check only),
calibration_check.json and the execution-calibration / snapshot files (only for comparison and the section-3
recheck), RESULTS_GHZ2.json and RESULTS_GHZ.json (stored R table only). No network, no IBM call.

Run with `E:/Claude Projects/.venv-qiskit/Scripts/python.exe -I recompute_run3.py`; the output of the run
is in `recompute_run3_output.txt`. The bootstrap uses its own seed (20261117), B = 2000.
