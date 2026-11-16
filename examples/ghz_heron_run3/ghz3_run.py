"""ghz3_run.py -- runner of the GHZ run-3 study, for the author (PREREG.md v3: section 1 D-1/D-3/D-7, K2, C-1, C-2, rule-14
check, stopping rule, power at submission, atomic writes; section 3 execution-time calibration; section 5 K3; section 8).

Derived from ghz2_run.py (run 2) with the changes listed in README.md ("Diff list").  Modes
  --selftest        FakeKingston only: snapshot, selection, build + transpile all 368 circuits, integrity (K3), model M2 and
                    reference M, QPY round trip, a tiny noiseless pipeline check, plus offline checks of the code identity,
                    C-1, C-2 and the power function.  No freeze needed, no account, no network.
  --dry-run         (freeze + code identity verified)  load the saved IBM account, list the operational >=156-qubit backends,
                    pick the least busy Heron r2 one (D-1), build and transpile every circuit and print ONLY the pass/fail of
                    D-7, K2 (noiseless simulation of the circuits about to be submitted), C-1 and (with --quota-seconds N) C-2
                    and the time estimate: no prediction, no difference of predictions.  Appends one line to
                    run/dryrun_log.jsonl (stopping rule).  The dry run is BINDING when D-7, K2 and C-1 pass, whatever C-2
                    says.  Does NOT submit.
  --submit          (freeze + code identity verified)  requires --quota-seconds N.  REFUSES (nothing submitted; only a log line
                    is written) if the estimate exceeds 300 s (exit 4), K2 fails (10), C-1 fails (5), C-2 fails (6) or
                    --quota-seconds is missing/invalid (7).  A --submit that passes the checks appends a "checks passed" line
                    to the log at once.  Then it computes run/power_run3.json (nothing of it is printed), writes the snapshot,
                    circuits.qpy, model.json, calibration_check.json, power_run3.json and job.json to a temporary folder,
                    submits ONE SamplerV2 job and moves the files into run/ only after the job id is returned.  If the
                    submission raises (or is interrupted) the temporary folder is KEPT, renamed attempt_<utc>, and the failure
                    is logged (exit 8, or the interrupt is re-raised after logging): before any retry the author checks the
                    account's job list for a job created at that attempt; if one exists it is the run and --recover JOBID
                    completes run/.
  --recover JOBID   (freeze verified)  no new submission: requires run/job.json absent and exactly one attempt_* folder (or
                    --attempt NAME) and REFUSES unless the service read succeeds and confirms that the job's backend equals the
                    attempt's, that it was created at or after the attempt's snapshot time and not after the logged failure
                    + 10 minutes, and that it has 368 circuits.  Then it moves the files into run/ and writes job.json (job id,
                    "recovered": true, the attempt's records).
  --fetch [JOBID]   (freeze + code identity verified)  retrieve the result, save raw counts per circuit and register to
                    run/counts.json (K3 totals check), and save the job's execution timestamps, usage, the backend's
                    calibration at the execution start (history query) AND the current calibration, each with the calibration
                    date of every parameter, to run/execution_calibration_<utc>.json (PREREG section 3).  Every fetch attempt
                    is kept (never overwritten) and logged with the file's SHA-256; the analysis uses the first logged one.
                    Run --fetch soon after the job finishes.
Exit codes: 0 ok, 1 selftest failure / job.json exists, 2 K3 count totals failed (fetch), 3 freeze or code identity failed,
4 time budget (D-7), 5 C-1 not satisfied, 6 C-2 not satisfied, 7 --quota-seconds missing/invalid, 8 submission failed,
9 --recover refused, 10 K2 (noiseless simulation of the circuits to be submitted) failed.
Outputs go to run/ inside this folder (FREEZE_GHZ3.json is the manifest).

Hardware / network is only touched inside _service() (QiskitRuntimeService is imported lazily, and only after the freeze
and the code identity have been verified).  No credential is ever printed or stored by this script.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import sys
import tempfile
import time

import numpy as np

import ghz2_core as core
import ghz2_study
import ghz3_study_h4

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_DIR = "run"
MIN_QUBITS = 156

MANIFEST_NAME = "FREEZE_GHZ3.json"
# PREREG section 8 / review F3: every file of the folder at the freeze
REQUIRED_FROZEN_3 = ("PREREG.md", "README.md", "REVISIONS.md", "ghz2_core.py", "ghz2_study.py", "ghz3_study_h4.py",
                     "ghz3_run.py", "ghz3_analyze.py", "ghz3_d4.py", "tests_ghz3.py", "certs/cert_h4_v1.json",
                     "certs/cert_h123_v1.json", "certs/k2_sim.json", "certs/power.json")
CODE_IDENTITY_FILES = ("ghz2_core.py", "ghz2_study.py")      # K3 addition: must equal run 2's frozen values

RUN1_DIR = os.path.normpath(os.path.join(HERE, "..", "ghz_heron"))
RUN2_DIR = os.path.normpath(os.path.join(HERE, "..", "ghz_heron_run2"))
RUN2_MANIFEST = "FREEZE_GHZ2.json"
RUN2_SNAPSHOT_FILE = os.path.join("run", "snapshot_ibm_kingston_20261111T235843Z.json")
RUN2_MODEL_FILE = os.path.join("run", "model.json")
# the known values of run 2's reference files (file SHA-256; run 2 is frozen); K3 checks calibration_check.json against them
RUN2_KNOWN = {"snapshot_file_sha256": "cc459a62b16dc003fbc59e23fb9aa04c271bfc632d05c326880df3e88e0fe023",
              "model_file_sha256": "6cd01966019af169c0fb85a094bc58c0e0e9fa9d8b64223f99a8ea08f074b7f8",
              "snapshot_content_sha256": "104fb995b806e2aa5e2cc139fa6f3e24ba2fba403ce3e3868c20b64a1f0dbacb"}

C1_THRESHOLD = 0.02                                           # PREREG C-1 (b)
C1_FIELDS = ("S", "cz_err", "g1_pop_err", "g1_par_err", "ro_err", "t1", "t2", "idle")      # M2 inputs of S_48
C1_N = 48
C2_MARGIN = 1.15                                              # PREREG C-2
RULE14_BAND = 0.05
EXIT_TIME, EXIT_C1, EXIT_C2, EXIT_QUOTA, EXIT_SUBMIT_FAILED, EXIT_RECOVER, EXIT_K2 = 4, 5, 6, 7, 8, 9, 10
LOG_FILE = "dryrun_log.jsonl"
EXEC_PREFIX = "execution_calibration_"
Q1_THRESHOLD = 0.02
Q1_LABEL = "small-n predictions within 0.02 of run 2's: for Q1 this run is not a model test of new predictions"
RECOVER_WINDOW_SECONDS = 600                                   # --recover: the job was created before the logged failure + 10 minutes
CLOCK_TOLERANCE_SECONDS = 600                                  # local clock vs service clock (--recover lower bound, K3 job times)
SIM_SEED = 20261113                                            # K2 (as in ghz3_d4.py and the analysis)
F_SIM_MIN = 0.98
C_MIX_SIM_MAX = 0.05
ATTEMPT_PREFIX = "attempt_"
DATE_PARAMS_QUBIT = ("T1", "T2", "readout_error")                # the calibration dates of the qubit inputs of M2

USAGE_WHITELIST = ("usage_remaining_seconds", "usage_consumed_seconds", "usage_limit_seconds", "usage_allocation_seconds")

POWER_SEED = 20261116
POWER_DATASETS = 2000
POWER_MIN = 0.8
POWER_H1_EFFECT = 0.03
DRIFT_NS = (4, 8, 16, 32, 48)                                 # grid common to runs 1 and 2


class CalibrationError(RuntimeError):
    """C-1: the reference (run 2) snapshot or model is missing or inconsistent."""


def environment_info():
    """T7: versions and platform recorded in power_run3.json and job.json (the power recomputation needs the same environment)."""
    def v(name):
        try:
            return importlib.metadata.version(name)
        except Exception:  # noqa: BLE001
            return None
    return {"python": platform.python_version(), "numpy": v("numpy"), "scipy": v("scipy"), "qiskit": v("qiskit"),
            "qiskit-aer": v("qiskit-aer"), "qiskit-ibm-runtime": v("qiskit-ibm-runtime"), "platform": platform.platform()}


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt_s(seconds):
    return f"{seconds:.1f} s = {seconds / 60:.2f} min"


def _by_str(comps):
    return {str(k): v for k, v in comps.items()}


# ------------------------------------------------------------------------------------------- freeze + code identity (K3)
def code_identity(code_dir, run2_dir=None):
    """K3 addition: the SHA-256 of ghz2_core.py and ghz2_study.py in ``code_dir`` equal run 2's frozen values
    (``run2_dir``/FREEZE_GHZ2.json). Raises core.FreezeError otherwise. Returns {name: sha256}."""
    run2_dir = run2_dir or RUN2_DIR
    path = os.path.join(run2_dir, RUN2_MANIFEST)
    if not os.path.isfile(path):
        raise core.FreezeError(f"run 2's {RUN2_MANIFEST} not found in {run2_dir}: cannot check the code identity")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            files = {str(k).replace("\\", "/"): v for k, v in json.load(fh)["files"].items()}
    except Exception as exc:  # noqa: BLE001
        raise core.FreezeError(f"run 2's {RUN2_MANIFEST} is malformed ({type(exc).__name__})") from None
    out, bad = {}, []
    for name in CODE_IDENTITY_FILES:
        fpath = os.path.join(code_dir, name)
        if name not in files:
            bad.append(f"{name} (not in run 2's manifest)")
        elif not os.path.isfile(fpath):
            bad.append(f"{name} (missing)")
        else:
            out[name] = core.sha256_file(fpath)
            if out[name] != files[name]:
                bad.append(f"{name} (differs from run 2's frozen SHA-256)")
    if bad:
        raise core.FreezeError("code identity with run 2 failed: " + ", ".join(bad))
    return out


def verify_run3_freeze(root, run2_dir=None):
    """FREEZE_GHZ3.json verified (core.verify_freeze with the run-3 required list) and the code identity checked."""
    core.verify_freeze(root, manifest_name=MANIFEST_NAME, required=REQUIRED_FROZEN_3)
    code_identity(root, run2_dir)
    return True


# ------------------------------------------------------------------------------------------------------- C-1 (PREREG 1, v2)
def m2_inputs(comps):
    """The M2 inputs of S_48 (the n = 48 components of model.json) as {field: value}."""
    c = _by_str(comps)[str(C1_N)]
    return {k: c[k] for k in C1_FIELDS}


def _n_differing(a, b):
    if isinstance(a, list) and isinstance(b, list):
        return abs(len(a) - len(b)) + sum(1 for x, y in zip(a, b) if x != y)
    return 0 if a == b else 1


def c1_check(old_comps, new_comps, device_old, device_new, threshold=C1_THRESHOLD):
    """C-1 (PREREG v3): holds iff (a) the device differs or at least one M2 input of S_48 differs from run 2's, AND
    (b) max over n of |F_pred,run3(n) - F_pred,run2(n)| >= threshold. Inputs are compared exactly.
    ``old_comps`` / ``new_comps``: {n: components} (model.json layout; keys int or str). Returns a JSON-serialisable dict."""
    o, nw = m2_inputs(old_comps), m2_inputs(new_comps)
    inputs_changed = {k: {"changed": bool(o[k] != nw[k]), "n_differing": int(_n_differing(o[k], nw[k]))} for k in C1_FIELDS}
    n_changed = sum(1 for v in inputs_changed.values() if v["changed"])
    device_differs = str(device_old) != str(device_new)
    a = bool(device_differs or n_changed > 0)
    oc, nc = _by_str(old_comps), _by_str(new_comps)
    delta = {}
    for n in core.GRID:
        row = {}
        for k in ("F_pred", "P_pred", "C_pred"):
            x3, x2 = float(nc[str(n)][k]), float(oc[str(n)][k])
            row[k] = {"run3": x3, "run2": x2, "diff": x3 - x2}
        delta[str(n)] = row
    max_abs = max(abs(delta[str(n)]["F_pred"]["diff"]) for n in core.GRID)
    b = bool(max_abs >= threshold)
    q1_max = max(abs(delta[str(n)]["F_pred"]["diff"]) for n in (4, 8))
    return {"q1_max_abs_delta_F_pred_4_8": q1_max, "q1_model_test": bool(q1_max >= Q1_THRESHOLD),"device_old": device_old, "device_new": device_new, "device_differs": device_differs,
            "inputs_changed": inputs_changed, "n_inputs_changed": n_changed, "condition_a": a,
            "delta_pred": delta, "max_abs_delta_F_pred": max_abs, "threshold": threshold, "condition_b": b,
            "c1_satisfied": bool(a and b)}


def rule14_check(model):
    """PREREG section 1: F_pred + 0.05 < 1 at n = 4 and 8 on the new predictions (else H1 is reported as one-sided)."""
    m = _by_str(model)
    vals = {str(n): float(m[str(n)]["F_pred"]) for n in (4, 8)}
    return {"F_pred": vals, "band": RULE14_BAND, "ok": bool(all(v + RULE14_BAND < 1.0 for v in vals.values()))}


def load_run2_reference(run2_dir=None):
    """Run 2's reference files, integrity-checked: {snap, snapshot_file, snapshot_file_sha256, snapshot_sha256, model_file,
    model_file_sha256, comps}. The file SHA-256 must equal RUN2_KNOWN."""
    run2_dir = run2_dir or RUN2_DIR
    sp, mp = os.path.join(run2_dir, RUN2_SNAPSHOT_FILE), os.path.join(run2_dir, RUN2_MODEL_FILE)
    for p in (sp, mp):
        if not os.path.isfile(p):
            raise CalibrationError(f"run 2 reference file not found: {p}")
    hs, hm = core.sha256_file(sp), core.sha256_file(mp)
    if RUN2_KNOWN and (hs != RUN2_KNOWN["snapshot_file_sha256"] or hm != RUN2_KNOWN["model_file_sha256"]):
        raise CalibrationError("run 2's snapshot or model file does not match its known SHA-256")
    with open(sp, "r", encoding="utf-8") as fh:
        sf = json.load(fh)
    snap = sf["snapshot"]
    if core.snapshot_hash(snap) != sf["sha256"]:
        raise CalibrationError("run 2's snapshot file does not match its own SHA-256")
    with open(mp, "r", encoding="utf-8") as fh:
        mf = json.load(fh)
    if mf.get("snapshot_sha256") != sf["sha256"]:
        raise CalibrationError("run 2's model.json does not belong to run 2's snapshot")
    return {"snap": snap, "snapshot_file": os.path.basename(sp), "snapshot_file_sha256": hs, "snapshot_sha256": sf["sha256"],
            "model_file": os.path.basename(mp), "model_file_sha256": hm, "comps": mf["components"]}


def calibration_record(c1, ref, new_snap_file, new_hash, rule14, m2_dates=None, m2_dates_error=None):
    """The content of run/calibration_check.json."""
    return {
        "prereg": "run 3 section 1, C-1 (v3) and rule-14 check", "c1_satisfied": bool(c1["c1_satisfied"]),
        "condition_a_device_or_input_differs": c1["condition_a"], "condition_b_max_abs_dF_ge_threshold": c1["condition_b"],
        "threshold": c1["threshold"], "max_abs_delta_F_pred": c1["max_abs_delta_F_pred"],
        "q1_model_test": c1["q1_model_test"], "q1_max_abs_delta_F_pred_4_8": c1["q1_max_abs_delta_F_pred_4_8"],
        "q1_replicate_label": None if c1["q1_model_test"] else Q1_LABEL,
        "device_run2": c1["device_old"], "device_run3": c1["device_new"], "device_differs": c1["device_differs"],
        "inputs_changed": c1["inputs_changed"], "n_inputs_changed": c1["n_inputs_changed"],
        "inputs_compared": list(C1_FIELDS) + [f"(components of n = {C1_N}, which contain every smaller n)"],
        "delta_pred_run3_minus_run2": c1["delta_pred"],
        "run2_snapshot_file": ref["snapshot_file"], "run2_snapshot_file_sha256": ref["snapshot_file_sha256"],
        "run2_snapshot_sha256": ref["snapshot_sha256"],
        "run2_model_file": ref["model_file"], "run2_model_file_sha256": ref["model_file_sha256"],
        "run3_snapshot_file": new_snap_file, "run3_snapshot_sha256": new_hash,
        "rule14": rule14,
        "m2_input_dates": m2_dates, "m2_input_dates_error": m2_dates_error,
    }


# ------------------------------------------------------------------------------------- M2 input dates (PREREG 1 and 3)
def m2_gate_keys(entries):
    """The gates behind the M2 gate-error lists of S_48, in the order of the lists (the iteration of core._one_q_errors over the
    transpiled GHZ_48 POP and PAR_0 circuits): {"cz": [(a, b)], "g1_pop": [(name, q)], "g1_par": [(name, q)]}."""
    def scan(tc):
        cz, g1 = [], []
        for inst in tc.data:
            name = inst.operation.name
            if name in ("measure", "barrier", "delay", "rz"):
                continue
            qs = tuple(int(tc.find_bit(x).index) for x in inst.qubits)
            (cz if len(qs) == 2 else g1).append((qs[0], qs[1]) if len(qs) == 2 else (name, qs[0]))
        return cz, g1
    out = {"cz": [], "g1_pop": [], "g1_par": []}
    for e in entries:
        if e["family"] == "GHZ" and e["n"] == C1_N:
            if e["kind"] == "POP":
                out["cz"], out["g1_pop"] = scan(e["circuit"])
            elif e["kind"] == "PAR" and e["j"] == 0:
                out["g1_par"] = scan(e["circuit"])[1]
    return out


def m2_date_targets(entries):
    """The calibration parameters that are M2 inputs of S_48: the tree edges T_48 (cz gates) and the one-qubit gates that enter
    g1_pop_err / g1_par_err, as (gate name, physical qubit). Non-tree edges among S_48 are not inputs.
    Returns (tree edges, one-qubit gates)."""
    keys = m2_gate_keys(entries)
    T = []
    for e in entries:
        if e["family"] == "GHZ" and e["n"] == C1_N:
            T = [tuple(int(x) for x in t) for t in e["T"]]
            break
    return T, set(keys["g1_pop"]) | set(keys["g1_par"])


def m2_target_records(dates, S, edges, ones):
    """The calibration-date records of every M2 input of S_48 found in ``dates`` (calibration_dates layout): T1, T2 and
    readout_error of the qubits of S; every parameter (error and length) of the cz gates of the tree ``edges`` (any direction)
    and of the one-qubit gates ``ones`` ({(name, qubit)}). Returns (records, missing): records = [{"gate", "qubits", "param",
    "date"}] (gate None for qubit parameters), missing = descriptions of inputs without any record."""
    recs, missing = [], []
    for q in S:
        params = (dates.get("qubits") or {}).get(str(q)) or {}
        for need in DATE_PARAMS_QUBIT:
            if need in params:
                recs.append({"gate": None, "qubits": [int(q)], "param": need, "date": params[need]})
            else:
                missing.append(f"qubit {q} {need}")
    index = {}
    for g in dates.get("gates") or []:
        index.setdefault((g["gate"], frozenset(int(x) for x in g["qubits"])), []).append(g)
    wanted = [("cz", frozenset(int(x) for x in e)) for e in edges] + [(name, frozenset([int(q)])) for name, q in sorted(ones)]
    if not edges:
        missing.append("the tree edges of S_48 are unknown")
    for key in wanted:
        gs = index.get(key)
        if not gs:
            missing.append(f"gate {key[0]}{sorted(key[1])}")
        else:
            recs.extend({"gate": g["gate"], "qubits": [int(x) for x in g["qubits"]], "param": g["param"], "date": g["date"]}
                        for g in gs)
    return recs, missing


def select_m2_dates(dates, S, edges, ones):
    """The compact calibration-date structure of the M2 inputs of S_48 (same layout as calibration_dates, restricted to the
    targets of m2_target_records), as recorded in run/calibration_check.json at submission."""
    recs, missing = m2_target_records(dates, S, edges, ones)
    out = {"qubits": {}, "gates": [], "missing": missing}
    for r in recs:
        if r["gate"] is None:
            out["qubits"].setdefault(str(r["qubits"][0]), {})[r["param"]] = r["date"]
        else:
            out["gates"].append(r)
    return out


def _parse_dt(d):
    if d is None:
        return None
    dt = datetime.datetime.fromisoformat(str(d).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


def date_of(dates, key):
    """The date (aware datetime, or None) of one M2 input in a calibration-date structure: key = ("q", qubit, param) or
    ("g", gate name, (qubits), param); for gates with records in both directions the latest."""
    if key[0] == "q":
        return _parse_dt(((dates.get("qubits") or {}).get(str(key[1])) or {}).get(key[2]))
    ds = [_parse_dt(g["date"]) for g in dates.get("gates") or []
          if g["gate"] == key[1] and frozenset(g["qubits"]) == frozenset(key[2]) and g["param"] == key[3]]
    ds = [d for d in ds if d is not None]
    return max(ds) if ds else None


# ------------------------------------------------------------------------------------------------------- C-2 (PREREG 1)
def c2_check(est, quota, limit=core.MAX_QUANTUM_SECONDS):
    """C-2: submit only if C2_MARGIN * est <= quota and est <= limit (the 300 s ceiling). Returns a dict."""
    need = C2_MARGIN * est
    ok_quota = bool(need <= quota)
    ok_cap = bool(est <= limit)
    return {"estimate_seconds": est, "quota_seconds": quota, "margin": C2_MARGIN, "required_seconds": need,
            "limit_seconds": limit, "quota_ok": ok_quota, "cap_ok": ok_cap, "c2_satisfied": bool(ok_quota and ok_cap)}


def parse_quota(value):
    """float quota in seconds, or None if missing / not finite / not > 0."""
    if value is None:
        return None
    try:
        q = float(value)
    except (TypeError, ValueError):
        return None
    return q if math.isfinite(q) and q > 0 else None


# -------------------------------------------------------------------------------------------- power (PREREG section 4)
def power_inputs(run1_dir=None, run2_dir=None):
    """The data files of the power computation: run 1's per-n P and C (RESULTS_GHZ.json table[n].P, .C), run 2's P_hat, C_hat,
    P_boot, C_boot (RESULTS_GHZ2_boot.npz) and run 2's M2 predictions (run/model.json). Returns a dict (arrays + file list)."""
    run1_dir, run2_dir = run1_dir or RUN1_DIR, run2_dir or RUN2_DIR
    f1 = os.path.join(run1_dir, "RESULTS_GHZ.json")
    f2 = os.path.join(run2_dir, "RESULTS_GHZ2.json")
    fb = os.path.join(run2_dir, "RESULTS_GHZ2_boot.npz")
    fm = os.path.join(run2_dir, "run", "model.json")
    with open(f1, "r", encoding="utf-8") as fh:
        t1 = {row["n"]: row for row in json.load(fh)["table"]}
    with open(f2, "r", encoding="utf-8") as fh:
        t2 = {row["n"]: row for row in json.load(fh)["table"]}
    with open(fm, "r", encoding="utf-8") as fh:
        comps2 = json.load(fh)["components"]
    z = np.load(fb)
    grid = list(core.GRID)
    if [int(x) for x in z["n"]] != grid:
        raise ValueError("run 2's bootstrap file has another grid")
    inp = {"grid": grid, "t1": t1, "P2": np.asarray(z["P_hat"], float), "C2": np.asarray(z["C_hat"], float),
           "P_boot": np.asarray(z["P_boot"], float), "C_boot": np.asarray(z["C_boot"], float),
           "pred2": {k: np.array([comps2[str(n)][k] for n in grid], float) for k in ("F_pred", "P_pred", "C_pred")}}
    for i, n in enumerate(grid):            # the npz point estimates must be the ones in RESULTS_GHZ2.json
        if abs(inp["P2"][i] - t2[n]["P"]) > 1e-12 or abs(inp["C2"][i] - t2[n]["C"]) > 1e-12:
            raise ValueError("run 2's RESULTS_GHZ2.json and RESULTS_GHZ2_boot.npz disagree")
    inp["files"] = [
        (f1, "run 1 per-n P and C: table[n].P and table[n].C for n = 4, 8, 16, 32, 48 (pooled drift)"),
        (f2, "cross-check of run 2's P and C point estimates (table[n].P, table[n].C)"),
        (fb, "keys n, P_hat, C_hat (truth ratios, drift), P_boot, C_boot (relative shot variance, centred shot-noise rows)"),
        (fm, "run 2's M2 predictions F_pred, P_pred, C_pred per n (components[n])"),
    ]
    return inp


def drift_sigmas(inp):
    """sigma_rel,X (X = P, C), PREREG section 4: sigma^2 = mean over n in {4, 8, 16, 32, 48} of
    [ln(X_run1(n)/X_run2(n))^2 / 2 - v_X(n)], v_X(n) = var(X_boot)/X_hat^2 of run 2's bootstrap (ddof = 1); a negative
    value counts as 0. Returns {"P": sigma, "C": sigma, "detail": {...}}."""
    grid = inp["grid"]
    out, detail = {}, {}
    for X, hat, boot in (("P", inp["P2"], inp["P_boot"]), ("C", inp["C2"], inp["C_boot"])):
        terms, rows = [], {}
        for n in DRIFT_NS:
            i = grid.index(n)
            lr = math.log(inp["t1"][n][X] / hat[i])
            v = float(np.var(boot[:, i], ddof=1) / hat[i] ** 2)
            terms.append(lr * lr / 2.0 - v)
            rows[str(n)] = {"ln_ratio": lr, "v_shot": v, "term": terms[-1]}
        var = max(0.0, float(np.mean(terms)))
        out[X] = math.sqrt(var)
        detail[X] = {"mean_term": float(np.mean(terms)), "sigma_rel": out[X], "per_n": rows}
    out["detail"] = detail
    return out


def _simulate(pred, truth_P, truth_C, sig, mode, inp, n_datasets, seed):
    """One power simulation; returns {criterion id: {"HOLDS": k, "FAILS": k, "UNDEFINED": k}} over n_datasets datasets.
    mode: "base" (z independent per n and component), "correlated" (one z per component), "drift_x2" (sigma x 2)."""
    crits = {"H1_small_n_accuracy": ghz2_study.H1_small_n_accuracy, "H2_gme_reach_matches": ghz2_study.H2_gme_reach_matches,
             "H3_population_specific": ghz2_study.H3_population_specific,
             "H4_overprediction_every_n": ghz3_study_h4.H4_overprediction_every_n}
    devP = inp["P_boot"] - inp["P_boot"].mean(axis=0, keepdims=True)
    devC = inp["C_boot"] - inp["C_boot"].mean(axis=0, keepdims=True)
    B, k = devP.shape
    mult = 2.0 if mode == "drift_x2" else 1.0
    rng = np.random.default_rng(seed)
    tally = {cid: {"HOLDS": 0, "FAILS": 0, "UNDEFINED": 0} for cid in crits}
    for _ in range(n_datasets):
        if mode == "correlated":
            zp, zc = rng.normal(), rng.normal()
        else:
            zp, zc = rng.normal(size=k), rng.normal(size=k)
        b = int(rng.integers(0, B))
        p_hat = truth_P * np.exp(mult * sig["P"] * zp) + devP[b]
        c_hat = truth_C * np.exp(mult * sig["C"] * zc) + devC[b]
        p_b, c_b = p_hat[None, :] + devP, c_hat[None, :] + devC
        d = {"F_pred": pred["F_pred"], "P_pred": pred["P_pred"], "C_pred": pred["C_pred"],
             "F_hat": (p_hat + c_hat) / 2.0, "P_hat": p_hat, "C_hat": c_hat,
             "F_boot": (p_b + c_b) / 2.0, "P_boot": p_b, "C_boot": c_b}
        for cid, fn in crits.items():
            v = fn(d)
            tally[cid]["HOLDS" if v is True else "FAILS" if v is False else "UNDEFINED"] += 1
    return tally


def _probs(tally, n_datasets):
    return {cid: {"counts": t, "P_HOLDS": t["HOLDS"] / n_datasets, "P_FAILS": t["FAILS"] / n_datasets,
                  "P_UNDEFINED": t["UNDEFINED"] / n_datasets} for cid, t in tally.items()}


def compute_power(pred_new, run1_dir=None, run2_dir=None, base_dir=None, n_datasets=POWER_DATASETS, seed=POWER_SEED,
                  label="", snapshot_sha256=None, device_change=False):
    """PREREG section 4: the power file. ``pred_new``: {"F_pred","P_pred","C_pred"} arrays over core.GRID (the predictions of
    the calibration in use at submission).

    Per simulated dataset (``n_datasets``, seed ``seed``): truth P, C (stated below) are multiplied by exp(sigma_rel,X * z)
    (z independent per n and component), one centred row of run 2's bootstrap (P and C jointly) is added as shot noise, and the
    replicates are the point estimate plus all centred rows; F = (P + C)/2. H1-H3 (ghz2_study) and H4 (ghz3_study_h4) are applied.
      power of H1     : P(H1 HOLDS) when the truth is P_pred - 0.03 and C_pred - 0.03 at n = 4, 8 (F_true = F_pred - 0.03)
                        and keeps run 2's ratios elsewhere
      power of H4     : P(H4 HOLDS) when the truth keeps run 2's ratios (P_true = P_pred * P_run2 / P_pred,run2, C likewise)
      expected outcome: P(HOLDS), P(FAILS), P(UNDEFINED) of H1-H4 under run 2's ratios (reported, not power)
      sensitivity     : drift fully correlated across n (one z per component), and drift x 2."""
    base_dir = base_dir or HERE
    inp = power_inputs(run1_dir, run2_dir)
    sig = drift_sigmas(inp)
    pred = {k: np.asarray(pred_new[k], float) for k in ("F_pred", "P_pred", "C_pred")}
    ratio_P = pred["P_pred"] * inp["P2"] / inp["pred2"]["P_pred"]
    ratio_C = pred["C_pred"] * inp["C2"] / inp["pred2"]["C_pred"]
    h1_P, h1_C = ratio_P.copy(), ratio_C.copy()
    cols = [core.GRID.index(4), core.GRID.index(8)]
    h1_P[cols] = pred["P_pred"][cols] - POWER_H1_EFFECT
    h1_C[cols] = pred["C_pred"][cols] - POWER_H1_EFFECT
    variants = {}
    for mode in ("base", "correlated", "drift_x2"):
        t_h1 = _probs(_simulate(pred, h1_P, h1_C, sig, mode, inp, n_datasets, seed), n_datasets)
        t_exp = _probs(_simulate(pred, ratio_P, ratio_C, sig, mode, inp, n_datasets, seed), n_datasets)
        variants[mode] = {"power_H1": t_h1["H1_small_n_accuracy"]["P_HOLDS"], "power_H4": t_exp["H4_overprediction_every_n"]["P_HOLDS"],
                          "scenario_h1_effect": t_h1, "expected_outcome": t_exp}
    files = [{"file": os.path.relpath(f, base_dir).replace("\\", "/"), "sha256": core.sha256_file(f), "used": used}
             for f, used in inp["files"]]
    for name in ("ghz2_study.py", "ghz3_study_h4.py"):
        files.append({"file": name, "sha256": core.sha256_file(os.path.join(base_dir, name)),
                      "used": "H1-H3" if name == "ghz2_study.py" else "H4"})
    return {
        "prereg": "run 3 section 4 (rule 16), PREREG v3", "environment": environment_info(), "label": label,
        "snapshot_sha256": snapshot_sha256,
        "device_change": bool(device_change), "grid": list(core.GRID), "n_datasets": n_datasets, "seed": seed,
        "method": (
            "Drift: sigma_rel,X (X = P, C) = sqrt(max(0, mean over n in {4, 8, 16, 32, 48} of [ln(X_run1(n)/X_run2(n))^2 / 2 - "
            "v_X(n)])), v_X(n) = var(X_boot)/X_hat^2 from run 2's bootstrap. Per dataset the truth P and C are multiplied by "
            "exp(sigma_rel,X * z), z independent per n and component; shot noise = one randomly chosen centred row of run 2's "
            "bootstrap (P and C jointly) added to the point estimate; replicates = point estimate + all centred rows; F = (P + "
            "C)/2. Power of H1 = P(H1 HOLDS) with truth P_pred - 0.03 and C_pred - 0.03 at n = 4, 8 and run 2's ratios "
            "elsewhere. Power of H4 = P(H4 HOLDS) with truth = run 2's ratios (P_true = P_pred * P_run2 / P_pred,run2, C "
            "likewise). Expected outcome = P(HOLDS), P(FAILS), P(UNDEFINED) of H1-H4 under run 2's ratios. Sensitivity: drift "
            "fully correlated across n (one z per component) and drift x 2."),
        "predictions": {k: {str(n): float(v[i]) for i, n in enumerate(core.GRID)} for k, v in pred.items()},
        "run2_ratios": {"P": {str(n): float(inp["P2"][i] / inp["pred2"]["P_pred"][i]) for i, n in enumerate(core.GRID)},
                        "C": {str(n): float(inp["C2"][i] / inp["pred2"]["C_pred"][i]) for i, n in enumerate(core.GRID)}},
        "sigma_rel": {"P": sig["P"], "C": sig["C"]}, "sigma_detail": sig["detail"],
        "power": {"H1": variants["base"]["power_H1"], "H4": variants["base"]["power_H4"]},
        "expected_outcome": variants["base"]["expected_outcome"],
        "sensitivity": {m: {"power_H1": variants[m]["power_H1"], "power_H4": variants[m]["power_H4"],
                            "expected_outcome": variants[m]["expected_outcome"]} for m in ("correlated", "drift_x2")},
        "scenario_h1_effect_base": variants["base"]["scenario_h1_effect"],
        "power_min": POWER_MIN, "inputs": files,
    }


def pred_arrays_from_comps(comps):
    c = _by_str(comps)
    return {k: np.array([c[str(n)][k] for n in core.GRID], float) for k in ("F_pred", "P_pred", "C_pred")}


def design_time_power(run1_dir=None, run2_dir=None, base_dir=None, n_datasets=POWER_DATASETS, seed=POWER_SEED):
    """certs/power.json: the same method on run 2's snapshot as a stand-in for the unseen one (not used to read the result)."""
    inp = power_inputs(run1_dir, run2_dir)
    return compute_power({k: inp["pred2"][k] for k in ("F_pred", "P_pred", "C_pred")}, run1_dir, run2_dir, base_dir,
                         n_datasets, seed, label="design-time stand-in: run 2's snapshot and M2 predictions (not used to read the result)",
                         snapshot_sha256=RUN2_KNOWN["snapshot_content_sha256"], device_change=False)


# --------------------------------------------------------------------------------------------------- stopping-rule log
def append_log(root, line):
    """Append one JSON line to run/dryrun_log.jsonl (created with run/ if needed)."""
    run_dir = os.path.join(root, RUN_DIR)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, LOG_FILE), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")


def predictions_sha256(model):
    """SHA-256 of the predictions (F_pred, P_pred, C_pred per n): the log holds this hash, never the predictions."""
    m = _by_str(model)
    return core.sha256_text(core.canonical_json({str(n): {k: float(m[str(n)][k]) for k in ("F_pred", "P_pred", "C_pred")}
                                                 for n in core.GRID}))


def log_prefix_sha(path, count):
    """SHA-256 of the first ``count`` lines (bytes, newline included) of the log file at ``path`` (an empty hash if absent)."""
    h = hashlib.sha256()
    if os.path.isfile(path) and count > 0:
        with open(path, "rb") as fh:
            for i, raw in enumerate(fh):
                if i >= count:
                    break
                h.update(raw)
    return h.hexdigest()


def log_anchor(root):
    """{"dryrun_log_lines", "dryrun_log_sha256"} of the log as it is now (recorded in job.json at submission)."""
    path = os.path.join(root, RUN_DIR, LOG_FILE)
    n = 0
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            n = sum(1 for _ in fh)
    return {"dryrun_log_lines": n, "dryrun_log_sha256": log_prefix_sha(path, n)}


def log_line(mode, backend=None, snapshot_sha256=None, model=None, ck=None, quota=None, reason=None, exit_code=None,
             attempt=None, extra=None, snapshot_utc=None, invocation=None):
    """One line of the log (PREREG section 1, stopping rule). It holds the SHA-256 of the predictions, never the predictions, and
    the snapshot time (the 2-hour window is measured between snapshot times). ``invocation`` ties the lines of one --submit
    together (the snapshot time).
    mode: "dry-run" | "submit-checks-passed" | "submit-refused" | "submit-failed" | "submit-accepted" (--submit invocations that
    reached the checks; attempt true) | "submit-not-attempt" (missing/invalid quota, existing job.json) | "recover" | "fetch"."""
    line = {"utc": utc_now(), "snapshot_utc": snapshot_utc, "invocation": invocation, "mode": mode, "attempt": attempt,
            "backend": backend, "snapshot_sha256": snapshot_sha256,
            "predictions_sha256": None, "d7": None, "k2": None, "c1": None, "c2": None, "quota_seconds": quota,
            "refusal_reason": reason, "exit_code": exit_code}
    if model is not None:
        line["predictions_sha256"] = predictions_sha256(model)
    if ck is not None:
        c1 = ck["c1"]
        line["d7"] = {"ok": ck["budget_ok"], "estimate_seconds": ck["estimate"]}
        line["k2"] = {"ok": bool(ck["k2"]["pass"]), "error": ck["k2"].get("error")}
        line["c1"] = {"satisfied": c1["c1_satisfied"], "condition_a": c1["condition_a"], "condition_b": c1["condition_b"],
                      "max_abs_delta_F_pred": c1["max_abs_delta_F_pred"], "n_inputs_changed": c1["n_inputs_changed"],
                      "device_differs": c1["device_differs"], "q1_model_test": c1["q1_model_test"]}
        line["c2"] = ck["c2"]
    if extra:
        line.update(extra)
    return line


# --------------------------------------------------------------------------------------------------- shared reporting
def k2_noiseless(entries):
    """K2 (PREREG section 5): noiseless MPS simulation of the exact transpiled circuits, 2000 shots, fixed seed; F_sim >= 0.98 for
    every n and C_mix,sim <= 0.05. Used on the circuits about to be submitted (--dry-run, --submit; a failure refuses the attempt)
    and, through ghz3_analyze, on the submitted circuits (binding). Returns {"pass", "detail"}."""
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="matrix_product_state")
    res = sim.run([e["circuit"] for e in entries], shots=core.SHOTS, seed_simulator=SIM_SEED).result()
    counts = {e["name"]: core.counts_by_register(res.get_counts(i), e["circuit"]) for i, e in enumerate(entries)}
    detail, ok = {"F_sim": {}, "C_mix_sim": {}, "thresholds": {"F_sim_min": F_SIM_MIN, "C_mix_sim_max": C_MIX_SIM_MAX},
                  "seed": SIM_SEED}, True
    for n in core.GRID:
        f = core.point_estimates(counts, n, "GHZ")["F"]
        detail["F_sim"][str(n)] = float(f)
        ok &= bool(f >= F_SIM_MIN)
    for n in core.MIX_NS:
        c = core.point_estimates(counts, n, "MIX")["C"]
        detail["C_mix_sim"][str(n)] = float(c)
        ok &= bool(c <= C_MIX_SIM_MAX)
    return {"pass": bool(ok), "detail": detail}


def build_and_report(snap, target, rep_delay, show_model=False):
    """Build + transpile (integrity-checked) every circuit; returns (entries, model, est_seconds). Prints the budget and, only
    if ``show_model`` (the selftest), the model: --dry-run and --submit never print a prediction (stopping rule)."""
    entries = core.build_all(snap, target)
    n_circ = len(entries)
    shots_total = n_circ * core.SHOTS
    est, rd, longest = core.estimate_time(entries, target, rep_delay)
    model = core.model_all(entries, target)
    print(f"circuits: {n_circ} (expected {core.EXPECTED_CIRCUITS})   shots per circuit: {core.SHOTS}   "
          f"shot total: {shots_total} (expected {core.EXPECTED_SHOTS})")
    print(f"K3 integrity: every circuit has n-1 two-qubit gates on the tree edges ({n_circ}/{n_circ} checked)")
    print(f"rep_delay used: {rd * 1e6:.1f} us   longest circuit: {longest * 1e6:.2f} us")
    print(f"rough quantum time = sum over circuits of shots*(rep_delay+circuit duration) = {_fmt_s(est)}")
    if show_model:
        print("model M2 per n:")
        for n in core.GRID:
            m = model[n]
            print(f"  n={n:<3} P_pred={m['P_pred']:.4f} C_pred={m['C_pred']:.4f} F_pred={m['F_pred']:.4f}   "
                  f"(reference M: F_M={m['F_M']:.4f})")
        for n in core.GRID:
            S = model[n]["S"]
            print(f"  S_{n}: root={S[0]} size={len(S)} last3={S[-3:]}")
    if n_circ != core.EXPECTED_CIRCUITS or shots_total != core.EXPECTED_SHOTS:
        raise core.IntegrityError("circuit / shot count differs from PREREG D-7")
    return entries, model, est


def enforce_time_budget(est, limit=core.MAX_QUANTUM_SECONDS):
    """D-7: refuse (SystemExit) if the rough quantum-time estimate exceeds ``limit`` seconds."""
    if est > limit:
        raise SystemExit(f"REFUSED: rough quantum-time estimate {est:.1f} s exceeds the {limit:.0f} s limit of PREREG D-7; "
                         "nothing is submitted")


# ---------------------------------------------------------------------------------------------------------- selftest
def cmd_selftest(run2_dir=None):
    """FakeKingston only (offline). Returns 0 on success."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeKingston

    t0 = time.time()
    try:
        ids = code_identity(HERE, run2_dir)
        print(f"[selftest] code identity with run 2's frozen values: OK ({', '.join(f'{k} {v[:12]}' for k, v in ids.items())})")
    except core.FreezeError as exc:
        print(f"[selftest] code identity FAILED: {exc}")
        return 1
    backend = FakeKingston()
    snap, h = core.snapshot_from_backend(backend, utc="SELFTEST")
    print(f"[selftest] backend {backend.name}: {snap['num_qubits']} qubits, snapshot sha256 {h[:16]}")
    adj = core.operational_graph(snap)
    print(f"[selftest] operational graph: {len(adj)} qubits; root {core.select_root(adj)}")
    entries, model, _est = build_and_report(snap, backend.target, getattr(backend, "default_rep_delay", None), show_model=True)

    # model from the snapshot-rebuilt target must equal the model from the real target (analysis path == submit path)
    tgt2 = core.target_from_snapshot(snap)
    model2 = core.model_all(entries, tgt2)
    same = all(abs(model[n][k] - model2[n][k]) < 1e-12 for n in core.GRID for k in ("P_pred", "C_pred", "F_pred", "F_M"))
    print(f"[selftest] M2 (P_pred, C_pred, F_pred) and F_M from target == from snapshot-rebuilt target: {same}")
    if not same:
        return 1

    # QPY round trip
    import io
    buf = io.BytesIO()
    qpy.dump([e["circuit"] for e in entries], buf)
    buf.seek(0)
    back = qpy.load(buf)
    ok = len(back) == len(entries) and all(a.name == b["circuit"].name for a, b in zip(back, entries))
    print(f"[selftest] QPY round trip of {len(back)} circuits: {ok}")
    if not ok:
        return 1

    # tiny noiseless pipeline check on n = 4 (same estimators as the analysis)
    sim = AerSimulator(method="matrix_product_state", seed_simulator=1)
    sub = [e for e in entries if e["n"] == 4 and e["family"] == "GHZ"]
    res = sim.run([e["circuit"] for e in sub], shots=core.SHOTS).result()
    counts = {e["name"]: core.counts_by_register(res.get_counts(i), e["circuit"]) for i, e in enumerate(sub)}
    est4 = core.point_estimates(counts, 4, "GHZ")
    print(f"[selftest] noiseless n=4 pipeline: P={est4['P']:.4f} C={est4['C']:.4f} C_re={est4['C_re']:.4f} "
          f"F={est4['F']:.4f} (expect ~1)")
    if est4["F"] < 0.95:
        return 1

    # C-1 (v2), C-2, rule 14 and power logic (offline)
    import copy
    comps = {str(n): copy.deepcopy(model[n]) for n in core.GRID}
    same_c = c1_check(comps, copy.deepcopy(comps), "dev", "dev")
    small = copy.deepcopy(comps)
    small["48"]["t1"][0] *= 1.01                                  # an input differs, but F_pred does not move by 0.02
    big = copy.deepcopy(comps)
    big["48"]["t1"][0] *= 1.01
    big["16"]["F_pred"] -= 0.03
    c1_ok = (not same_c["c1_satisfied"]
             and not c1_check(comps, small, "dev", "dev")["c1_satisfied"]
             and not c1_check(comps, copy.deepcopy(comps), "dev", "other")["c1_satisfied"]      # (a) holds, (b) does not
             and c1_check(comps, big, "dev", "dev")["c1_satisfied"])
    print(f"[selftest] C-1 (v3) logic: identical refused, input change without a 0.02 move refused, device change without a "
          f"0.02 move refused, input change with a 0.03 move passes: {c1_ok}")
    c2_ok = (c2_check(100.0, 115.0)["c2_satisfied"] and not c2_check(100.0, 114.9)["c2_satisfied"]
             and not c2_check(301.0, 1e9)["c2_satisfied"] and c2_check(300.0, 345.0)["c2_satisfied"])
    print(f"[selftest] C-2 logic (1.15 x estimate <= N and estimate <= 300 s): {c2_ok}")
    try:
        pw = compute_power(pred_arrays_from_comps(comps), n_datasets=100, label="selftest")
        pw_ok = all(abs(v["P_HOLDS"] + v["P_FAILS"] + v["P_UNDEFINED"] - 1.0) < 1e-12 for v in pw["expected_outcome"].values())
    except Exception as exc:  # noqa: BLE001
        print(f"[selftest] power function FAILED: {type(exc).__name__}: {exc}")
        pw_ok = False
    print(f"[selftest] power function (100 datasets on FakeKingston predictions; values not printed): {pw_ok}")
    if not (c1_ok and c2_ok and pw_ok):
        return 1
    print(f"[selftest] OK   wall time {time.time() - t0:.1f} s")
    return 0


# ------------------------------------------------------------------------------------------ account / hardware helpers
def _service():
    """The ONLY place that instantiates QiskitRuntimeService (default saved account; nothing is read or printed here)."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService()


def usage_summary(usage):
    """The whitelisted numeric usage fields of the service's usage dict (never the raw dict)."""
    out = {}
    if isinstance(usage, dict):
        for k in USAGE_WHITELIST:
            v = usage.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
                out[k] = v
    return out


def _print_usage(service):
    """Information only (C-2 decides on --quota-seconds): whitelisted numeric usage fields, if the service offers them."""
    try:
        s = usage_summary(service.usage())
        if s:
            print("account usage (information only; C-2 uses the N you pass): " + ", ".join(f"{k} = {v:g}" for k, v in s.items()))
        else:
            print("account usage: no whitelisted numeric field available; C-2 uses the N you pass")
    except Exception as exc:  # noqa: BLE001
        print(f"account usage query not available ({type(exc).__name__}); C-2 uses the N you pass")


def _submit_job(backend, circuits, shots):
    """Submit ONE SamplerV2 job (dynamical decoupling off, twirling off; no execution-time limit); returns the job id."""
    from qiskit_ibm_runtime import SamplerV2
    sampler = SamplerV2(mode=backend)
    sampler.options.dynamical_decoupling.enable = False
    sampler.options.twirling.enable_gates = False
    sampler.options.twirling.enable_measure = False
    job = sampler.run([(c,) for c in circuits], shots=shots)
    return job.job_id()


def heron_r2_basis(backend):
    """(is_heron_r2, basis). PREREG D-1 (v2): Heron r2 by ``processor_type`` (family Heron, revision 2) when that field is
    present; otherwise num_qubits == 156 (``"num_qubits_fallback"``)."""
    ptype = getattr(backend, "processor_type", None)
    if ptype:
        ok = str(ptype.get("family", "")).lower() == "heron" and str(ptype.get("revision", "")) == "2"
        return bool(ok), "processor_type"
    return backend.num_qubits == 156, "num_qubits_fallback"


def pick_backend(service):
    """D-1: among the operational >=156-qubit non-simulator backends visible to the account, the Heron r2 one (see
    heron_r2_basis) with the fewest pending jobs (ties: name). Prints the candidate list and the basis of the choice.
    Returns (backend, basis)."""
    backs = service.backends(simulator=False, operational=True, min_num_qubits=MIN_QUBITS)
    rows = []
    for b in backs:
        st = b.status()
        ok, basis = heron_r2_basis(b)
        rows.append({"backend": b, "name": b.name, "n": b.num_qubits, "pending": st.pending_jobs,
                     "operational": bool(st.operational), "heron_r2": ok, "basis": basis})
    rows.sort(key=lambda r: (r["pending"], r["name"]))
    print(f"operational non-simulator backends with >= {MIN_QUBITS} qubits: {len(rows)}")
    for r in rows:
        tag = ("Heron r2" if r["heron_r2"] else "not Heron r2") + f" (basis: {r['basis']})"
        print(f"  {r['name']:<20} qubits={r['n']:<4} pending_jobs={r['pending']:<5} {tag}")
    cand = [r for r in rows if r["operational"] and r["heron_r2"]]
    if not cand:
        raise SystemExit("no operational Heron r2 backend with >= 156 qubits is visible to this account; not selecting any")
    chosen = cand[0]
    print(f"SELECTED (D-1, least busy Heron r2): {chosen['name']} (pending_jobs={chosen['pending']}, "
          f"basis: {chosen['basis']})")
    return chosen["backend"], chosen["basis"]


def _checks(snap, model, est, quota, run2_dir, entries):
    """All pre-submission checks (D-7, K2, C-1, C-2, rule 14). Returns a dict; prints only pass/fail lines (no prediction)."""
    ck = {"estimate": est, "budget_ok": bool(est <= core.MAX_QUANTUM_SECONDS)}
    ref = load_run2_reference(run2_dir)           # CalibrationError: handled by the callers (logged, exit 5)
    c1 = c1_check(ref["comps"], model, ref["snap"]["backend"], snap["backend"])
    try:                                          # K2 on the circuits about to be submitted
        ck["k2"] = {"pass": bool(k2_noiseless(entries)["pass"]), "error": None}
    except Exception as exc:  # noqa: BLE001
        ck["k2"] = {"pass": False, "error": type(exc).__name__}
    ck.update(c1=c1, ref=ref, rule14=rule14_check(model))
    ck["c2"] = c2_check(est, quota) if quota is not None else None
    print(f"D-7 (estimate {est:.1f} s <= {core.MAX_QUANTUM_SECONDS:.0f} s): {'PASS' if ck['budget_ok'] else 'FAIL'}")
    print(f"K2 (noiseless simulation of the circuits to be submitted): {'PASS' if ck['k2']['pass'] else 'FAIL'}"
          + ("" if not ck["k2"]["error"] else f" ({ck['k2']['error']})"))
    print(f"C-1 (new calibration for M2): {'PASS' if c1['c1_satisfied'] else 'FAIL'}")
    if ck["c2"] is None:
        print("C-2 (quota): not evaluated (pass --quota-seconds N; --submit requires it)")
    else:
        print(f"C-2 (1.15 x estimate = {ck['c2']['required_seconds']:.1f} s <= N = {quota:.1f} s): "
              f"{'PASS' if ck['c2']['c2_satisfied'] else 'FAIL'}")
    return ck


def _refusal(ck):
    """(exit code, reason) of the first failing condition, or (0, None)."""
    if not ck["budget_ok"]:
        return EXIT_TIME, "D-7: estimate above the 300 s ceiling"
    if not ck["k2"]["pass"]:
        return EXIT_K2, "K2: the noiseless simulation of the circuits to be submitted failed"
    if not ck["c1"]["c1_satisfied"]:
        return EXIT_C1, "C-1 not satisfied"
    if ck["c2"] is not None and not ck["c2"]["c2_satisfied"]:
        return EXIT_C2, "C-2 not satisfied"
    return 0, None


def cmd_dry_run(root, quota=None, run2_dir=None):
    service = _service()
    backend, basis = pick_backend(service)
    utc = utc_now()
    snap, h = core.snapshot_from_backend(backend, utc=utc)
    print(f"backend choice basis: {basis}")
    print(f"snapshot (not saved in --dry-run): {backend.name} {utc} sha256 {h[:16]}")
    entries, model, est = build_and_report(snap, backend.target, snap["rep_delay"])
    try:
        ck = _checks(snap, model, est, quota, run2_dir, entries)
    except CalibrationError as exc:
        append_log(root, log_line("dry-run", backend.name, h, model, None, quota, f"C-1 cannot be evaluated: {exc}", EXIT_C1,
                                  snapshot_utc=utc))
        print(f"C-1 cannot be evaluated: {exc}", file=sys.stderr)
        return EXIT_C1
    _print_usage(service)
    code, reason = _refusal(ck)
    append_log(root, log_line("dry-run", backend.name, h, model, ck, quota, reason, code, snapshot_utc=utc))
    print("dry run only: nothing was submitted" + ("." if code == 0 else f" (and --submit would refuse, exit code {code})."))
    binding = bool(ck["budget_ok"] and ck["k2"]["pass"] and ck["c1"]["c1_satisfied"])
    print("this dry run is " + ("BINDING (D-7, K2 and C-1 pass): a passing --submit must follow within 2 hours of its snapshot time"
                                if binding else "not binding (D-7, K2 or C-1 failed)"))
    print(f"appended a line to {RUN_DIR}/{LOG_FILE}")
    return code


def _move_into(tmp, run_dir, names):
    os.makedirs(run_dir, exist_ok=True)
    for name in names:
        os.replace(os.path.join(tmp, name), os.path.join(run_dir, name))


def _keep_attempt(root, tmp):
    """Keep the temporary folder of a failed submission, renamed with the attempt time; returns the new folder name."""
    base = f"{ATTEMPT_PREFIX}{utc_now()}"
    name, k = base, 1
    while os.path.exists(os.path.join(root, name)):
        k += 1
        name = f"{base}_{k}"
    os.replace(tmp, os.path.join(root, name))
    return name


def cmd_submit(root, quota=None, run2_dir=None, power_run1_dir=None, power_run2_dir=None):
    from qiskit import qpy

    run_dir = os.path.join(root, RUN_DIR)
    job_path = os.path.join(run_dir, "job.json")
    quota_p = parse_quota(quota)
    if os.path.exists(job_path):                      # not an attempt (PREREG section 1)
        append_log(root, log_line("submit-not-attempt", quota=quota_p, reason="job.json already exists", exit_code=1,
                                  attempt=False))
        raise SystemExit(f"{job_path} already exists: a job was already submitted from this folder; refusing to submit again")
    if quota_p is None:                               # not an attempt
        append_log(root, log_line("submit-not-attempt", reason="--quota-seconds missing or invalid", exit_code=EXIT_QUOTA,
                                  attempt=False))
        print("REFUSED: --submit requires --quota-seconds N (a positive number: the remaining QPU seconds read on the IBM "
              "Quantum dashboard); nothing is submitted", file=sys.stderr)
        return EXIT_QUOTA
    quota = quota_p
    service = _service()
    backend, basis = pick_backend(service)
    utc = utc_now()
    snap, h = core.snapshot_from_backend(backend, utc=utc)
    entries, model, est = build_and_report(snap, backend.target, snap["rep_delay"])
    inv = dict(snapshot_utc=utc, invocation=utc)          # ties the lines of this --submit together (the snapshot time)
    try:
        ck = _checks(snap, model, est, quota, run2_dir, entries)   # D-7, K2, C-1, C-2: before anything is written or submitted
    except CalibrationError as exc:
        append_log(root, log_line("submit-refused", backend.name, h, model, None, quota,
                                  f"C-1 cannot be evaluated: {exc}", EXIT_C1, attempt=True, **inv))
        print(f"REFUSED: C-1 cannot be evaluated: {exc}; nothing is submitted", file=sys.stderr)
        return EXIT_C1
    code, reason = _refusal(ck)
    if code:
        append_log(root, log_line("submit-refused", backend.name, h, model, ck, quota, reason, code, attempt=True, **inv))
        print(f"REFUSED: {reason}; nothing is submitted. Logged to {RUN_DIR}/{LOG_FILE}.", file=sys.stderr)
        return code
    # the checks passed: record it at once, before anything else (an interrupted passing attempt leaves a trace)
    append_log(root, log_line("submit-checks-passed", backend.name, h, model, ck, quota, None, 0, attempt=True, **inv))

    # power at submission (PREREG section 1 and 4): computed from the new predictions; nothing of it is printed
    ref = ck["ref"]
    device_change = str(snap["backend"]) != str(ref["snap"]["backend"])
    try:
        power = compute_power(pred_arrays_from_comps(model), power_run1_dir, power_run2_dir, HERE, label=(
            "at submission, new snapshot" + ("; device change (I-6)" if device_change else "")),
            snapshot_sha256=h, device_change=device_change)
    except Exception as exc:  # noqa: BLE001
        append_log(root, log_line("submit-failed", backend.name, h, model, ck, quota,
                                  f"power computation failed ({type(exc).__name__})", EXIT_SUBMIT_FAILED, attempt=True, **inv))
        print(f"SUBMISSION NOT DONE: the power computation failed ({type(exc).__name__}); nothing is submitted.", file=sys.stderr)
        return EXIT_SUBMIT_FAILED

    # the calibration dates of every M2 input of S_48 at submission (PREREG section 1, used in section 3)
    m2_dates, m2_dates_error = None, None
    try:
        tree, ones = m2_date_targets(entries)
        m2_dates = select_m2_dates(calibration_dates(backend.properties()), model[C1_N]["S"], tree, ones)
    except Exception as exc:  # noqa: BLE001
        m2_dates_error = type(exc).__name__

    snap_name = f"snapshot_{backend.name}_{utc}.json"
    tmp = tempfile.mkdtemp(prefix=".submit_tmp_", dir=root)
    job_id = None
    try:
        with open(os.path.join(tmp, snap_name), "w", encoding="utf-8") as fh:
            json.dump({"sha256": h, "snapshot": snap}, fh, indent=1, sort_keys=True)
        with open(os.path.join(tmp, "circuits.qpy"), "wb") as fh:
            qpy.dump([e["circuit"] for e in entries], fh)
        with open(os.path.join(tmp, "model.json"), "w", encoding="utf-8") as fh:
            json.dump({"snapshot_sha256": h, "grid": list(core.GRID), "components": {str(n): model[n] for n in core.GRID}},
                      fh, indent=1)
        with open(os.path.join(tmp, "calibration_check.json"), "w", encoding="utf-8") as fh:
            json.dump(calibration_record(ck["c1"], ref, snap_name, h, ck["rule14"], m2_dates, m2_dates_error), fh, indent=1)
        with open(os.path.join(tmp, "power_run3.json"), "w", encoding="utf-8") as fh:
            json.dump(power, fh, indent=1)
        record = {
            "backend": backend.name, "backend_choice_basis": basis, "submitted_utc": utc, "snapshot_file": snap_name,
            "snapshot_sha256": h, "shots": core.SHOTS, "n_circuits": len(entries),
            "dynamical_decoupling": False, "twirling": False, "est_quantum_seconds": est,
            "quota_seconds": quota, "c2": ck["c2"], "power_run3_sha256": core.sha256_file(os.path.join(tmp, "power_run3.json")),
            "device_change": device_change, "environment": environment_info(), "manifest": core.manifest_of(entries),
            **log_anchor(root),
        }
        with open(os.path.join(tmp, "attempt_record.json"), "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1)
        job_id = _submit_job(backend, [e["circuit"] for e in entries], core.SHOTS)
        # the job id exists: move everything into run/ (job.json last: its existence blocks a second submission)
        with open(os.path.join(tmp, "job.json"), "w", encoding="utf-8") as fh:
            json.dump({"job_id": job_id, **record}, fh, indent=1)
        _move_into(tmp, run_dir, [snap_name, "circuits.qpy", "model.json", "calibration_check.json", "power_run3.json", "job.json"])
    except BaseException as exc:  # noqa: BLE001  (logged and kept, KeyboardInterrupt re-raised)
        kept = None
        try:
            kept = _keep_attempt(root, tmp)
        finally:
            why = f"submission failed ({type(exc).__name__})" + (f"; a job id WAS returned: {job_id}" if job_id else "")
            append_log(root, log_line("submit-failed", backend.name, h, model, ck, quota, why, EXIT_SUBMIT_FAILED, attempt=True,
                                      extra={"attempt_folder": kept, "job_id": job_id}, **inv))
        print(f"SUBMISSION FAILED ({type(exc).__name__}); the attempt's files were kept in {kept}; logged to {RUN_DIR}/{LOG_FILE}.\n"
              "BEFORE ANY RETRY check the account's job list for a job created at this attempt. If one exists it is the run: "
              "use  --recover JOBID  (no second job is to be submitted).", file=sys.stderr)
        if isinstance(exc, KeyboardInterrupt):
            raise
        return EXIT_SUBMIT_FAILED
    shutil.rmtree(tmp, ignore_errors=True)
    append_log(root, log_line("submit-accepted", backend.name, h, model, ck, quota, None, 0, attempt=True, **inv))
    print(f"SUBMITTED job {job_id} on {backend.name}; wrote run/{snap_name}, circuits.qpy, model.json, calibration_check.json, "
          "power_run3.json, job.json")
    return 0


def _read_log_lines(root):
    path = os.path.join(root, RUN_DIR, LOG_FILE)
    out = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                try:
                    out.append(json.loads(raw))
                except ValueError:
                    pass
    return out


def cmd_recover(root, job_id, attempt=None):
    """--recover JOBID: complete run/ from a kept attempt folder after a failed submission whose job exists on the account.
    No new submission. Requires run/job.json absent and exactly one attempt_* folder (or ``attempt``), and REFUSES unless the
    service read succeeds and confirms (PREREG section 1): the job's backend equals the attempt's; it was created at or after the
    attempt's snapshot time and not after the logged failure + 10 minutes; it has 368 circuits. Returns 0 or EXIT_RECOVER."""
    run_dir = os.path.join(root, RUN_DIR)

    def refuse(msg):
        print(f"REFUSED: {msg}", file=sys.stderr)
        return EXIT_RECOVER
    if not job_id:
        return refuse("--recover needs the job id")
    if os.path.exists(os.path.join(run_dir, "job.json")):
        return refuse("run/job.json already exists")
    folders = sorted(d for d in os.listdir(root) if d.startswith(ATTEMPT_PREFIX) and os.path.isdir(os.path.join(root, d)))
    if attempt:
        if attempt not in folders:
            return refuse(f"no attempt folder {attempt!r} (found: {folders})")
        folder = attempt
    elif len(folders) == 1:
        folder = folders[0]
    else:
        return refuse(f"expected exactly one {ATTEMPT_PREFIX}* folder, found {len(folders)} {folders}; pass --attempt NAME")
    src = os.path.join(root, folder)
    try:
        with open(os.path.join(src, "attempt_record.json"), "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return refuse(f"{folder}/attempt_record.json is unreadable ({type(exc).__name__})")
    if os.path.isfile(os.path.join(src, "job.json")):           # the job id was returned but the move failed
        with open(os.path.join(src, "job.json"), "r", encoding="utf-8") as fh:
            prior = json.load(fh).get("job_id")
        if prior and prior != job_id:
            return refuse(f"{folder}/job.json names job {prior}, not {job_id}")
    names = [record["snapshot_file"], "circuits.qpy", "model.json", "calibration_check.json", "power_run3.json"]
    missing = [n for n in names if not os.path.isfile(os.path.join(src, n)) and not os.path.isfile(os.path.join(run_dir, n))]
    if missing:
        return refuse(f"files missing in {folder}: {missing}")
    failures = [l for l in _read_log_lines(root) if l.get("mode") == "submit-failed" and l.get("attempt_folder") == folder]
    if not failures:
        return refuse(f"the log has no failure line for {folder}")
    failed_at = _parse_dt(datetime.datetime.strptime(failures[-1]["utc"], "%Y%m%dT%H%M%SZ").isoformat() + "+00:00")
    snap_at = _parse_dt(datetime.datetime.strptime(record["submitted_utc"], "%Y%m%dT%H%M%SZ").isoformat() + "+00:00")
    notes = {}
    try:                                                        # the service read must succeed (no submission)
        job = _service().job(job_id)
        notes["status"] = str(job.status())
        notes["backend"] = getattr(job.backend(), "name", None)
        created = job.creation_date
        if created is None:
            raise ValueError("no creation date")
        created = created.astimezone(datetime.timezone.utc) if created.tzinfo else created.astimezone().astimezone(datetime.timezone.utc)
        notes["created_utc"] = created.isoformat()
        notes["n_circuits"] = len(job.inputs["pubs"])
    except Exception as exc:  # noqa: BLE001
        return refuse(f"the service read of job {job_id} failed ({type(exc).__name__}); --recover needs it")
    if notes["backend"] != record["backend"]:
        return refuse(f"the job ran on {notes['backend']}, the attempt on {record['backend']}")
    if not (snap_at - datetime.timedelta(seconds=CLOCK_TOLERANCE_SECONDS) <= created
            <= failed_at + datetime.timedelta(seconds=RECOVER_WINDOW_SECONDS)):
        return refuse(f"the job was created at {created.isoformat()}, outside the window [snapshot {snap_at.isoformat()} - 10 min, "
                      f"failure {failed_at.isoformat()} + 10 min]")
    if notes["n_circuits"] != core.EXPECTED_CIRCUITS or len(record["manifest"]) != core.EXPECTED_CIRCUITS:
        return refuse(f"the job has {notes['n_circuits']} circuits, expected {core.EXPECTED_CIRCUITS}")
    os.makedirs(run_dir, exist_ok=True)
    for n in names:
        if os.path.isfile(os.path.join(src, n)):
            os.replace(os.path.join(src, n), os.path.join(run_dir, n))
    job_rec = {"job_id": job_id, **record, "recovered": True, "recovered_utc": utc_now(), "recovered_from": folder,
               "recovered_service_read": notes}
    with open(os.path.join(run_dir, "job.json"), "w", encoding="utf-8") as fh:
        json.dump(job_rec, fh, indent=1)
    os.replace(os.path.join(src, "attempt_record.json"), os.path.join(run_dir, "attempt_record.json"))
    for leftover in os.listdir(src):
        if leftover == "job.json":
            os.remove(os.path.join(src, leftover))
    try:
        os.rmdir(src)
    except OSError:
        pass
    append_log(root, log_line("recover", record.get("backend"), record.get("snapshot_sha256"), None, None, record.get("quota_seconds"),
                              f"recovered job {job_id} from {folder}", 0, attempt=False, extra={"job_id": job_id}))
    print(f"RECOVERED job {job_id}: wrote run/job.json (recovered: true) and moved the files of {folder} into run/. "
          "No job was submitted.")
    return 0


# ------------------------------------------------------------------------------------ fetch + execution-time calibration
def _iso_to_dt(s):
    dt = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)


def _jsonable(x):
    return json.loads(json.dumps(x, default=str))


def snapshot_at(backend, when, utc_label):
    """Snapshot of ``backend`` with the calibration properties found at ``when`` (aware UTC datetime): the Target from
    backend.target_history(datetime=when) and the faulty flags from backend.properties(datetime=when), serialised exactly as
    core.snapshot_from_backend does for the current calibration. Returns (snapshot, sha256, calibration dates of that result)."""
    props = backend.properties(datetime=when)
    faulty_q, faulty_g = [], []
    if props is not None:
        faulty_q = list(props.faulty_qubits())
        faulty_g = [(g.gate, list(g.qubits)) for g in props.faulty_gates()]
    target = backend.target_history(datetime=when)
    snap, h = core.snapshot_from_target(target, backend.name, faulty_q, faulty_g,
                                        rep_delay=getattr(backend, "default_rep_delay", None), utc=utc_label,
                                        processor_type=getattr(backend, "processor_type", None))
    return snap, h, calibration_dates(props)


def calibration_dates(props):
    """The calibration date of every parameter in a BackendProperties: {"last_update_date": iso, "qubits": {q: {name: iso}},
    "gates": [{"gate", "qubits", "param", "date"}]} (aware UTC ISO strings)."""
    def iso(d):
        if d is None:
            return None
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        return d.astimezone(datetime.timezone.utc).isoformat()
    out = {"last_update_date": iso(getattr(props, "last_update_date", None)), "qubits": {}, "gates": []}
    for q, params in enumerate(props.qubits):
        out["qubits"][str(q)] = {p.name: iso(p.date) for p in params}
    for g in props.gates:
        for p in g.parameters:
            out["gates"].append({"gate": g.gate, "qubits": [int(x) for x in g.qubits], "param": p.name, "date": iso(p.date)})
    return out


def exec_files(run_dir):
    """The saved execution-calibration attempts (run/execution_calibration_<utc>[_k].json), oldest first."""
    if not os.path.isdir(run_dir):
        return []
    return sorted(f for f in os.listdir(run_dir) if f.startswith(EXEC_PREFIX) and f.endswith(".json"))


def _next_exec_path(run_dir, utc):
    base = f"{EXEC_PREFIX}{utc}"
    name, k = base + ".json", 1
    while os.path.exists(os.path.join(run_dir, name)):
        k += 1
        name = f"{base}_{k}.json"
    return os.path.join(run_dir, name)


def save_execution_calibration(service, job, meta, run_dir):
    """PREREG section 3: save the job's execution timestamps and usage, the calibration at the execution start (the history
    query, with the calibration date of every parameter of that result) and the CURRENT calibration (snapshot as at submission,
    with its dates) to a NEW file run/execution_calibration_<utc>.json; earlier attempts are never overwritten (the analysis uses
    the first). Never raises: whatever fails is recorded ("available": false = no history; "error", "current_error" =
    exception types)."""
    now = utc_now()
    info = {"available": False, "error": None, "job_id": meta.get("job_id"), "backend": meta.get("backend"),
            "saved_utc": now, "current": None, "current_error": None}
    backend = None
    try:
        metrics = job.metrics()
        ts = _jsonable(metrics.get("timestamps") or {})
        info["timestamps"] = ts
        info["usage"] = _jsonable(metrics.get("usage"))
        try:
            info["job_usage_seconds"] = float(job.usage())
        except Exception:  # noqa: BLE001
            info["job_usage_seconds"] = None
        start = ts.get("running") or ts.get("started")
        if not start:
            raise ValueError("no execution start timestamp in the job metrics")
        when = _iso_to_dt(start)
        info["execution_start_utc"] = when.strftime("%Y%m%dT%H%M%SZ")
        info["execution_start_iso"] = when.isoformat()
        backend = service.backend(meta["backend"])
        snap, h, dates = snapshot_at(backend, when, info["execution_start_utc"])
        info.update(snapshot=snap, snapshot_sha256=h, dates=dates, available=True)
    except Exception as exc:  # noqa: BLE001
        info["error"] = type(exc).__name__
        info["available"] = False
        for k in ("snapshot", "snapshot_sha256", "dates"):
            info.pop(k, None)
    try:                                           # the current calibration with its dates (the fallback of PREREG section 3)
        if backend is None:
            backend = service.backend(meta["backend"])
        props = backend.properties(refresh=True)
        when = utc_now()
        snap, h = core.snapshot_from_backend(backend, utc=when)
        info["current"] = {"retrieved_utc": when, "snapshot": snap, "snapshot_sha256": h, "dates": calibration_dates(props)}
    except Exception as exc:  # noqa: BLE001
        info["current_error"] = type(exc).__name__
        info["current"] = None
    path = _next_exec_path(run_dir, now)
    info["attempt_file"] = os.path.basename(path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1)
    return info


def cmd_fetch(root, job_id=None):
    run_dir = os.path.join(root, RUN_DIR)
    with open(os.path.join(run_dir, "job.json"), "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    job_id = job_id or meta["job_id"]
    service = _service()
    job = service.job(job_id)
    print(f"job {job_id}: status {job.status()}")
    result = job.result()
    manifest = meta["manifest"]
    if len(result) != len(manifest):
        raise SystemExit(f"result has {len(result)} pubs, manifest has {len(manifest)}")
    circuits, order, bad = {}, [], []
    for entry, pub in zip(manifest, result):
        regs = {}
        for reg in ("meas", "mid"):
            if hasattr(pub.data, reg):
                regs[reg] = {str(k): int(v) for k, v in getattr(pub.data, reg).get_counts().items()}
        total = {r: sum(c.values()) for r, c in regs.items()}
        if any(t != meta["shots"] for t in total.values()) or "meas" not in regs:
            bad.append(entry["name"])
        circuits[entry["name"]] = regs
        order.append(entry["name"])
    out = {"job_id": job_id, "backend": meta["backend"], "shots": meta["shots"], "order": order,
           "k3_count_totals_ok": not bad, "bad_circuits": bad, "circuits": circuits}
    with open(os.path.join(run_dir, "counts.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print(f"saved run/counts.json ({len(circuits)} circuits)")
    print("K3 count totals == shots: " + ("OK" if not bad else f"FAILED for {bad[:5]}{' ...' if len(bad) > 5 else ''}"))
    info = save_execution_calibration(service, job, meta, run_dir)
    f = f"run/{info['attempt_file']}"
    if info["available"]:
        print(f"saved {f}: calibration at the execution start retrieved (and the current calibration: "
              f"{'saved' if info['current'] is not None else 'not saved'})")
    elif info["current"] is not None:
        print(f"saved {f}: the calibration history was NOT available ({info['error']}); the CURRENT calibration "
              "with its dates was saved (the analysis can verify 'no recalibration since submission')")
    else:
        print(f"saved {f}: NOT retrieved ({info['error']}, {info['current_error']}); the analysis will label it "
              "'execution-time calibration not verified'")
    append_log(root, log_line("fetch", meta.get("backend"), None, None, None, None, None, 0 if not bad else 2, attempt=False,
                              extra={"file": info["attempt_file"], "file_sha256": core.sha256_file(os.path.join(run_dir, info["attempt_file"])),
                                     "job_id": job_id}))
    print("(every fetch attempt is kept and logged; the analysis uses the first logged one)")
    return 0 if not bad else 2


# ------------------------------------------------------------------------------------------------------------- main
def main(argv=None, root=HERE, run2_dir=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--submit", action="store_true")
    g.add_argument("--fetch", nargs="?", const="", metavar="JOBID")
    g.add_argument("--recover", metavar="JOBID")
    ap.add_argument("--attempt", default=None, metavar="NAME", help="with --recover: the kept attempt_* folder to use")
    ap.add_argument("--quota-seconds", default=None, metavar="N",
                    help="remaining QPU seconds from the IBM Quantum dashboard (C-2); required by --submit, optional in --dry-run")
    args = ap.parse_args(argv)
    if args.selftest:
        return cmd_selftest(run2_dir)
    try:
        verify_run3_freeze(root, run2_dir)
    except core.FreezeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    print("freeze manifest verified; ghz2_core.py and ghz2_study.py equal run 2's frozen values")
    if args.dry_run:
        if args.quota_seconds is not None and parse_quota(args.quota_seconds) is None:
            print("REFUSED: --quota-seconds must be a positive number", file=sys.stderr)
            return EXIT_QUOTA
        return cmd_dry_run(root, parse_quota(args.quota_seconds), run2_dir)
    if args.submit:
        return cmd_submit(root, args.quota_seconds, run2_dir)
    if args.recover is not None:
        return cmd_recover(root, args.recover, args.attempt)
    return cmd_fetch(root, args.fetch or None)


if __name__ == "__main__":
    sys.exit(main())
