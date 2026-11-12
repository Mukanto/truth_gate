# GHZ fidelity against the device's own error model (pre-registered hardware study)

The binding specification is [`PREREG.md`](PREREG.md) (v2; revisions with reasons in [`REVISIONS.md`](REVISIONS.md)). This folder holds the code. Nothing here was run on hardware before the
freeze; the simulator was used only for the D4 smoke test and control K2.

| File | Role |
|---|---|
| `ghz_core.py` | selection (D-2), circuits (D-3/5/6), model M, estimators, bootstrap, snapshot, freeze check |
| `ghz_study.py` | Kapı study: criteria G1-G3 and synthetic worlds (numpy + kapi only) |
| `ghz_run.py` | `--selftest`, `--dry-run`, `--submit`, `--fetch` |
| `ghz_analyze.py` | results: estimators, G1-G3 (imported unchanged from `ghz_study.py`), K1, K3, `RESULTS_GHZ.{json,md}` |
| `ghz_d4.py` | pre-freeze checks (budget, K2, D4), simulator only |
| `tests_ghz.py` | offline unit tests |
| `certs/` | Kapı certificates, `k2_sim.json` |

Python: any environment with `qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`, `numpy`, `scipy` and `kapi` (`pip install -e <kapi-oss>`).
Run everything from this folder.

## Before the run (no account needed, no cost)

```text
python tests_ghz.py          # offline unit tests, seconds
python ghz_d4.py             # budget (317 circuits, 634000 shots), K2 on the simulator, D4; about 35 s
python -m kapi check ghz_study.py --out certs/cert_vN.json
```

Then the designer freezes the files (`FREEZE_GHZ.json`, format `{"files": {name: sha256}}`, for example with
`protocol/tools/freeze.py`). The manifest must list `PREREG.md`, `ghz_core.py`, `ghz_study.py`, `ghz_run.py` and `ghz_analyze.py`.
`--dry-run`, `--submit`, `--fetch` and `ghz_analyze.py` refuse to run if the manifest is absent, incomplete or does not match.

## The author's steps

**1. Save the IBM account yourself (once).** The key is typed into a hidden prompt; it never appears in a file in this folder, in a
log or in the scripts. Placeholders only:

```text
python -c "import getpass; from qiskit_ibm_runtime import QiskitRuntimeService as S; S.save_account(token=getpass.getpass('IBM Quantum API key: '), instance='<YOUR_INSTANCE_CRN>', set_as_default=True, overwrite=True)"
```

Add `channel='<YOUR_CHANNEL>'` if your account needs it (see the qiskit-ibm-runtime documentation). The scripts only call
`QiskitRuntimeService()` (the default saved account) and never print or store the token.
*Cost:* nothing; no network call is made by `save_account`.

**2. `python ghz_run.py --selftest`**
Offline, on `FakeKingston` only; no freeze, no account. Builds and transpiles all 317 circuits, asserts n - 1 two-qubit gates (K3),
computes model M both from the target and from the snapshot-rebuilt target, round-trips QPY, runs a tiny noiseless pipeline check.
*Cost:* a few seconds of CPU, no hardware time.

**3. `python ghz_run.py --dry-run`**
Verifies the freeze, loads the saved account, lists the operational non-simulator backends with at least 156 qubits (name, qubits,
pending jobs, processor type), selects the Heron r2 one with the fewest pending jobs (D-1: Heron r2 by `processor_type` when present, otherwise `num_qubits == 156`; the basis is printed and recorded in `run/job.json`), takes its calibration data, builds and
transpiles every circuit, prints the circuit count, the shot total, the model prediction F_pred(n) and a rough quantum-time
estimate. It does **not** submit and writes nothing.
*Cost:* a few network calls (backend list, status, properties); **no quantum time**. The estimate is
`sum over circuits of 2000 x (rep_delay + circuit duration)`; compare it with your remaining allocation (D-7: 10 minutes).
On FakeKingston it is about 160 s (2.7 min); the real device's rep_delay and durations decide the real figure.
Real wall-clock time also includes queueing and per-job overheads that this estimate does not.

**4. `python ghz_run.py --submit`**
Everything in `--dry-run`, then, in this order: saves `run/snapshot_<backend>_<utc>.json` (with its SHA-256), `run/circuits.qpy`
(the exact submitted circuits) and `run/model.json`; submits **one** SamplerV2 job (317 circuits, 2000 shots each, dynamical
decoupling off, twirling off); writes `run/job.json` (job id, backend, UTC, snapshot hash, circuit manifest in order).
It refuses to submit if `run/job.json` already exists.
*Cost:* **this uses your quantum allocation**: about the estimate printed by `--dry-run`, 634000 shots in one job. It cannot be undone.

**5. `python ghz_run.py --fetch [JOBID]`**
Waits for the job (blocking call), saves the raw counts per circuit and register (`meas`, `mid`) to `run/counts.json` and checks that
every count total equals the shots (K3). The job id defaults to the one in `run/job.json`.
*Cost:* network only; no quantum time. May block until the job has finished.

**6. `python ghz_analyze.py`**
Offline. Reads `run/job.json`, `run/counts.json`, the snapshot, `run/circuits.qpy` and `run/model.json`; recomputes model M from the
snapshot, estimates P, C, F with the joint multinomial bootstrap (B = 2000, seed 20261112), applies G1-G3 (imported from
`ghz_study.py`) and K1/K3, and writes `RESULTS_GHZ.json` and `RESULTS_GHZ.md`.
*Cost:* a few seconds of CPU.

## Notes

- Controls: K1 (hardware, in `ghz_analyze.py`; PREREG v2: upper end of the bootstrap 95% CI of C_mix <= 0.05 for MIX_8 and MIX_32), K2 (simulator, `ghz_d4.py`, written to `certs/k2_sim.json`, read by the analysis if present),
  K3 (integrity, before and after the run). If one fails the result is "yorumlanamaz" (uninterpretable).
- Interpretation choices made in the code are listed in the headers of `ghz_core.py` and `ghz_run.py`. The bootstrap resamples reduced
  categories (POP: 0^n, 1^n, other; PAR: even, odd), which is distributionally identical to resampling full outcomes.
