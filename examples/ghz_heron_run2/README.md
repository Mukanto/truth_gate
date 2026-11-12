# GHZ fidelity on Heron r2, run 2: testing the corrected model on new data

The binding specification is [`PREREG.md`](PREREG.md). Run 1 (`../ghz_heron/`, frozen) is the training data; this run is the test.
This folder holds the code. Nothing here was run on hardware before the freeze; the simulator was used only for the D4 smoke
test and control K2.

## What is new compared with run 1

| Item | Run 1 | Run 2 |
|---|---|---|
| Grid | n = 4, 8, 16, 32, 48 | n = 4, 8, 16, **24**, 32, 48 |
| Budget | 317 circuits, 634000 shots | **368 circuits, 736000 shots**; refused if the rough quantum-time estimate exceeds **300 s** (D-7) |
| Model | one formula M for F | **M2**: P_pred, C_pred and F_pred predicted separately (T1 term on P, T2 term on C, readout twice in C); run 1's M kept as a reference arm F_M (reported, not a criterion) |
| Criteria | G1-G3 | **H1** (|F_hat - F_pred| <= 0.05 at n = 4, 8), **H2** (point-value GME reach = predicted reach), **H3** (P short more than C at n = 32 and 48) |
| Bootstrap | seed 20261112 | seed **20261113**; also returns P and C replicates, and C with Re (sensitivity I-1) |
| Controls | K1, K2, K3 | K1 unchanged; K2 adds a **bit-order positive control**; K3 adds "M2 recomputed from the snapshot equals the saved model" |
| Files | `ghz_*.py`, `FREEZE_GHZ.json` | `ghz2_*.py`, `tests_ghz2.py`, `FREEZE_GHZ2.json`, `RESULTS_GHZ2.*` |

| File | Role |
|---|---|
| `ghz2_core.py` | selection, circuits, model M2 and reference M, estimators, bootstrap, snapshot, freeze check |
| `ghz2_study.py` | Kapı study: H1-H3, synthetic worlds and controls (numpy + kapi only) |
| `ghz2_run.py` | `--selftest`, `--dry-run`, `--submit`, `--fetch` |
| `ghz2_analyze.py` | results: table with P, C, F, CIs, predictions, R, F_M; H1-H3 (imported unchanged); K1, K3; `RESULTS_GHZ2.{json,md}` and `RESULTS_GHZ2_boot.npz` |
| `ghz2_d4.py` | pre-freeze checks: budget, K2, bit-order control, D4, rule 14 (simulator only) |
| `tests_ghz2.py` | offline unit tests |
| `certs/` | Kapı certificates and `k2_sim.json` |

Python: any environment with `qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`, `numpy`, `scipy` and `kapi` (`pip install -e <kapi-oss>`).
Run everything from this folder. Outputs of the hardware steps go to `run/` inside this folder.

## Before the run (no account needed, no cost)

```text
python tests_ghz2.py          # offline unit tests, seconds
python ghz2_d4.py             # budget (368 circuits, 736000 shots), K2, bit-order control, D4, rule 14; about 40 s
python -m kapi check ghz2_study.py --out certs/cert_vN.json
```

Then the designer freezes the files (`FREEZE_GHZ2.json`, format `{"files": {name: sha256}}`, for example with
`../../protocol/tools/freeze.py`). The manifest must list `PREREG.md`, `ghz2_core.py`, `ghz2_study.py`, `ghz2_run.py` and
`ghz2_analyze.py`. `--dry-run`, `--submit`, `--fetch` and `ghz2_analyze.py` refuse to run if the manifest is absent,
incomplete or does not match.

## The author's steps

**1. The IBM account.** If the account saved for run 1 is still valid, nothing to do. Otherwise save it yourself (once); the key is
typed into a hidden prompt and never appears in a file here, in a log or in the scripts. Placeholders only:

```text
python -c "import getpass; from qiskit_ibm_runtime import QiskitRuntimeService as S; S.save_account(token=getpass.getpass('IBM Quantum API key: '), instance='<YOUR_INSTANCE_CRN>', set_as_default=True, overwrite=True)"
```

*Cost:* nothing; no network call is made by `save_account`.

**2. `python ghz2_run.py --selftest`**
Offline, on `FakeKingston` only; no freeze, no account. Builds and transpiles all 368 circuits, asserts n - 1 two-qubit gates (K3),
prints M2's P_pred, C_pred, F_pred (and the reference F_M) per n, checks that the model from the target equals the model from the
snapshot-rebuilt target, round-trips QPY and runs a tiny noiseless pipeline check.
*Cost:* a few seconds of CPU, no hardware time.

**3. `python ghz2_run.py --dry-run`**
Verifies the freeze, loads the saved account, lists the operational non-simulator backends with at least 156 qubits, selects the
least busy Heron r2 one (D-1: Heron r2 by `processor_type` when present, otherwise `num_qubits == 156`; the basis is printed and
recorded in `run/job.json`), builds and transpiles every circuit, prints the circuit count, the shot total, the model prediction
and the rough quantum-time estimate `sum over circuits of 2000 x (rep_delay + circuit duration)`. It says whether the estimate is
within the **300 s** limit of D-7 (exit code 4 if not). It does **not** submit and writes nothing.
*Cost:* a few network calls (backend list, status, properties); **no quantum time**. On FakeKingston the estimate is about 187 s
(3.1 min); the real device's rep_delay and durations decide the real figure. About 430 s of the month's allocation remains.

**4. `python ghz2_run.py --submit`** (only with your approval)
Everything in `--dry-run`; it **refuses** if the estimate exceeds 300 s. Otherwise, in this order: saves
`run/snapshot_<backend>_<utc>.json` (with its SHA-256), `run/circuits.qpy` (the exact submitted circuits) and `run/model.json`
(M2 components per n); submits **one** SamplerV2 job (368 circuits, 2000 shots each, dynamical decoupling off, twirling off);
writes `run/job.json`. It refuses to submit if `run/job.json` already exists.
*Cost:* **this uses your quantum allocation**: about the estimate printed by `--dry-run`, 736000 shots in one job. It cannot be undone.

**5. `python ghz2_run.py --fetch [JOBID]`**
Waits for the job (blocking call), saves the raw counts per circuit and register (`meas`, `mid`) to `run/counts.json` and checks that
every count total equals the shots (K3). The job id defaults to the one in `run/job.json`.
*Cost:* network only; no quantum time. May block until the job has finished.

**6. `python ghz2_analyze.py`**
Offline. Recomputes M2 from the snapshot (and checks it equals the saved model), estimates P, C, F with the joint multinomial
bootstrap (B = 2000, seed 20261113), applies H1-H3 (imported from `ghz2_study.py`) and K1/K3, and writes `RESULTS_GHZ2.json`,
`RESULTS_GHZ2.md` and `RESULTS_GHZ2_boot.npz` (the bootstrap arrays, so every interval can be recomputed).
*Cost:* a few seconds of CPU.

## Notes

- K1: for MIX_8 and MIX_32 the 97.5th percentile of the C_mix bootstrap is <= 0.05. K2 (simulator, `ghz2_d4.py`, written to
  `certs/k2_sim.json` and read by the analysis if present) includes the bit-order positive control. K3 is checked before and after the run.
  If one control fails the result is "yorumlanamaz" (uninterpretable).
- H2 uses point values on both sides (n_meas = largest n with F_hat > 0.5); whether the 95% CI at n_meas excludes 0.5 is reported only.
- The bootstrap resamples reduced categories (POP: 0^n, 1^n, other; PAR: even, odd), which is distributionally identical to resampling
  full outcomes.
