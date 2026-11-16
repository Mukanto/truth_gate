"""ghz3_analyze.py -- analysis of the GHZ run-3 data (PREREG.md v3: sections 2 estimators, 3 model M2 and the calibration in force
at execution, 4 criteria, power and readings, 5 controls, 6).

Derived from ghz2_analyze.py (run 2).  Reads run/job.json, run/counts.json, the snapshot named in job.json, run/circuits.qpy (the
circuits that were submitted), run/model.json, run/calibration_check.json, run/power_run3.json, run/execution_calibration_<utc>.json
(the first logged --fetch attempt: the log names its file and SHA-256) and run/dryrun_log.jsonl.  Computes P, C, F with 95% bootstrap intervals, M2's P_pred, C_pred, F_pred
from the snapshot (cross-checked against run/model.json) and, if the calibration at the execution start differs from the snapshot's
(section 3), from the execution-time calibration (primary; the snapshot's are then secondary); R = F_meas / F_pred, the reference
arm F_M, C with Re (I-1); applies H1-H3 (imported unchanged from ghz2_study.py), H4 (imported unchanged from ghz3_study_h4.py),
K1, K2, K3 (with the run-3 additions), the pre-registered readings, the "within drift" labels and the verdict mapping; writes
RESULTS_GHZ3.json, RESULTS_GHZ3.md and RESULTS_GHZ3_boot.npz.  K2 is read from certs/k2_sim.json (a missing or unreadable file is a
K2 failure).  The power numbers read are those of run/power_run3.json (computed at submission), never certs/power.json.

PREREG v3 (final): K2 is binding here (noiseless MPS on run/circuits.qpy) and also runs in --dry-run and --submit; the answer is assembled
from the pre-written sentences; the stopping rule is applied to the anchored log lines plus the accepted line, with the dry run
binding when D-7, K2 and C-1 pass (the 2 h window between snapshot times); the post-anchor lines, the first logged fetch (file and
SHA-256) and the job's creation and start times are K3 items; the power environment (versions, platform) is compared.
PREREG v3 additions: the answer to Q1 and Q2 is assembled mechanically (assemble_answer); C-1 per question (Q1 replicate label);
the stopping rule is checked on run/dryrun_log.jsonl (deviations reported, the log prefix anchored in job.json is a K3 item);
the power file is checked against the frozen hashes and recomputed (K3); K2 is also run here, on the submitted circuits
(noiseless MPS, binding); the execution-time calibration uses the first saved attempt, accepts a history result only if its
M2-input dates are at or before the execution start, and calls a difference "changed" only if every differing input carries a
later date than at submission.

Usage:  python ghz3_analyze.py            (verifies FREEZE_GHZ3.json and the code identity first)
"""
from __future__ import annotations

import datetime
import json
import math
import os
import sys

import numpy as np
from qiskit import qpy

import ghz2_core as core
import ghz2_study
import ghz3_run
import ghz3_study_h4

HERE = os.path.dirname(os.path.abspath(__file__))
RUN2_DIR = ghz3_run.RUN2_DIR
RUN1_DIR = ghz3_run.RUN1_DIR

CRITERIA = {
    "H1_small_n_accuracy": ghz2_study.H1_small_n_accuracy,
    "H2_gme_reach_matches": ghz2_study.H2_gme_reach_matches,
    "H3_population_specific": ghz2_study.H3_population_specific,
    "H4_overprediction_every_n": ghz3_study_h4.H4_overprediction_every_n,
}
ROLES = {"H1_small_n_accuracy": "confirmatory", "H4_overprediction_every_n": "confirmatory",
         "H2_gme_reach_matches": "reported", "H3_population_specific": "reported (exploratory)"}
K1_C_MAX = 0.05
MODEL_TOL = 1e-9
POWER_MIN = ghz3_run.POWER_MIN
H1_BAND = ghz2_study.H1_BAND
# run 1 under the corrected model M2, exploratory values quoted in run 2's PREREG section 0 (fallback only)
RUN1_QUOTED_R = {4: 0.98, 8: 0.96, 16: 0.87, 32: 0.85, 48: 0.84}

LABEL_CHANGED = "calibration changed before execution"
LABEL_NOT_VERIFIED = "execution-time calibration not verified"
LABEL_VERIFIED = "verified: no recalibration since submission"
EXEC_RTOL = 1e-6                    # PREREG section 3: "equal" = within a relative tolerance of 1e-6 per M2 input value

# PREREG section 4: the pre-written answers (verdict mapping, rule 3)
# PREREG section 4 (v3): the answer is assembled from pre-written sentences
Q1_SENTENCES = {
    ("HOLDS", None): "Q1: on this run's calibration M2 is accurate within 0.05 for 4 and 8 qubits.",
    ("FAILS", "fails"): "Q1: on this run's calibration M2 is not accurate within 0.05 for 4 or 8 qubits.",
    ("FAILS", "not demonstrated"): "Q1: M2's accuracy within 0.05 for 4 and 8 qubits is not demonstrated (H1 failed with power below 0.8).",
    ("UNDEFINED", None): "Q1 is not answered.",
}
Q2_SENTENCES = {
    ("HOLDS", None): "Q2: on a new calibration M2 still overpredicts the fidelity at every n.",
    ("FAILS", "fails"): "Q2: on a new calibration M2 does not overpredict at every n; the run-1/2 overprediction did not persist everywhere.",
    ("FAILS", "not demonstrated"): "Q2: persistence of the overprediction at every n is not demonstrated (H4 failed with power below 0.8).",
    ("UNDEFINED", None): "Q2 is not answered.",
}
JOINT_SENTENCES = {                      # only these four combinations
    (("HOLDS", None), ("HOLDS", None)): "Together: a small systematic bias.",
    (("HOLDS", None), ("FAILS", "fails")): "Together: M2 is accurate at small n and does not overpredict everywhere.",
    (("FAILS", "fails"), ("HOLDS", None)): "Together: the bias persists and exceeds 0.05 at small n.",
    (("FAILS", "fails"), ("FAILS", "fails")): "Together: M2 misses the small-n band and does not overpredict at every n.",
}
ANSWER_UNINTERPRETABLE = "yorumlanamaz"
Q1_LABEL = ghz3_run.Q1_LABEL
SIM_SEED = ghz3_run.SIM_SEED             # K2 (binding), as in ghz3_run.py and ghz3_d4.py
F_SIM_MIN = ghz3_run.F_SIM_MIN
C_MIX_SIM_MAX = ghz3_run.C_MIX_SIM_MAX
SUBMIT_PASSING_MODES = ("submit-checks-passed", "submit-accepted", "submit-failed")   # a --submit that passed D-7, K2, C-1, C-2
POST_ANCHOR_SLACK = 0


def verdict_word(v):
    return {True: "HOLDS", False: "FAILS", None: "UNDEFINED"}[v]


def apply_criteria(data):
    """Apply the imported H1-H4 to ``data`` in the schema of ghz2_study (F/P/C _pred, _hat, _boot; no n: the criteria index
    GRID by position). Returns {id: "HOLDS"|"FAILS"|"UNDEFINED"}."""
    data = {k: np.asarray(v, dtype=float) for k, v in data.items()}
    out = {}
    for cid, fn in CRITERIA.items():
        try:
            out[cid] = verdict_word(fn(data))
        except Exception as exc:  # noqa: BLE001
            out[cid] = f"UNDEFINED ({type(exc).__name__})"
    return out


def k1_verdict(mix):
    """K1 (PREREG section 5): for MIX_8 and MIX_32, the 97.5th percentile of the bootstrap replicates of C_mix is <= 0.05.
    F_mix is reported but is not part of the rule."""
    out = {}
    for n, m in mix.items():
        c_hi = float(np.percentile(m["C_boot"], 97.5))
        out[str(n)] = {"C_mix": float(m["C"]), "C_mix_ci_high": c_hi, "F_mix": float(m["F"]),
                       "F_mix_ci": [float(m["F_lo"]), float(m["F_hi"])], "pass": bool(c_hi <= K1_C_MAX)}
    return out, all(v["pass"] for v in out.values())


def k2_status(certs_dir):
    """K2 (PREREG section 5): read certs/k2_sim.json. A missing or unreadable file is a K2 failure. The pass condition is the
    estimator-fidelity part only; the bit-order control is reported, not part of the pass condition."""
    path = os.path.join(certs_dir, "k2_sim.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            k2 = json.load(fh)
        ok = bool(k2["pass"] is True)
        return {"pass": ok, "readable": True, "file": "certs/k2_sim.json", "detail": k2.get("detail"),
                "bit_order_control_reported_only": k2.get("bit_order_control")}
    except Exception as exc:  # noqa: BLE001
        return {"pass": False, "readable": False, "file": "certs/k2_sim.json", "error": type(exc).__name__}


def k2_noiseless(entries):
    """K2 (PREREG section 5, binding here): noiseless MPS simulation of the submitted circuits (ghz3_run.k2_noiseless, the same
    function that --dry-run and --submit run on the circuits about to be submitted). Returns {"pass", "detail"}."""
    return ghz3_run.k2_noiseless(entries)


def load_run(run_dir):
    with open(os.path.join(run_dir, "job.json"), "r", encoding="utf-8") as fh:
        job = json.load(fh)
    with open(os.path.join(run_dir, job["snapshot_file"]), "r", encoding="utf-8") as fh:
        snap_file = json.load(fh)
    with open(os.path.join(run_dir, "counts.json"), "r", encoding="utf-8") as fh:
        counts = json.load(fh)
    with open(os.path.join(run_dir, "circuits.qpy"), "rb") as fh:
        circuits = qpy.load(fh)
    with open(os.path.join(run_dir, "model.json"), "r", encoding="utf-8") as fh:
        model = json.load(fh)
    return job, snap_file, counts, circuits, model


def _reach_point(values):
    ok = [n for n, v in zip(core.GRID, values) if v > 0.5]
    return int(max(ok)) if ok else 0


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------------------------------------- H2: reach and crossing
def interp_crossing(values, level=0.5):
    """Where F falls to ``level``, by linear interpolation in n between grid points: the first grid step i with
    values[i] > level >= values[i+1]. None if F is above ``level`` at every n (crossing beyond n = 48) or F(4) <= level."""
    v = np.asarray(values, dtype=float)
    n = np.asarray(core.GRID, dtype=float)
    if v[0] <= level:
        return None
    for i in range(len(v) - 1):
        if v[i] > level >= v[i + 1]:
            return float(n[i] + (v[i] - level) / (v[i] - v[i + 1]) * (n[i + 1] - n[i]))
    return None


def h2_report(f_hat, f_boot, f_pred):
    """H2's reported extras (PREREG section 4): point reach, CI-based reach (largest n with 2.5th percentile of F > 0.5), and the
    interpolated crossing of F = 0.5 for the point values, for the predictions and with a 95% percentile interval from the
    bootstrap replicates (replicates without a crossing are counted, not used)."""
    f_boot = np.asarray(f_boot, float)
    lo = np.percentile(f_boot, 2.5, axis=0)
    cross_b = [interp_crossing(row) for row in f_boot]
    ok = np.array([c for c in cross_b if c is not None], float)
    return {"n_meas_point": _reach_point(f_hat), "n_pred": _reach_point(f_pred),
            "n_meas_by_ci_low_gt_half": int(max([n for n, l in zip(core.GRID, lo) if l > 0.5], default=0)),
            "crossing_point": interp_crossing(f_hat), "crossing_pred": interp_crossing(f_pred),
            "crossing_ci": None if ok.size == 0 else [float(np.percentile(ok, 2.5)), float(np.percentile(ok, 97.5))],
            "crossing_replicates_without_crossing": int(len(cross_b) - ok.size), "replicates": int(len(cross_b))}


# ----------------------------------------------------------------------------------------------- drift, labels, readings
def drift_quantities(p_pred, c_pred, f_pred, sigma):
    """sigma_d,F(n) = 1/2 sqrt((P_pred sigma_P)^2 + (C_pred sigma_C)^2) and sigma_d,R(n) = sigma_d,F(n)/F_pred(n)
    (PREREG section 4) on the predictions in use. ``sigma``: {"P": sigma_rel,P, "C": sigma_rel,C}."""
    p, c, f = (np.asarray(x, float) for x in (p_pred, c_pred, f_pred))
    sf = 0.5 * np.sqrt((p * sigma["P"]) ** 2 + (c * sigma["C"]) ** 2)
    return sf, sf / f


def h1_drift_label(f_hat, f_pred, sigma_dF, verdict):
    """H1: "within drift" when ||F_hat(n) - F_pred(n)| - 0.05| < 2 sigma_d,F(n) at the n that decides the verdict (the n of n = 4,
    8 with the larger deviation). The label never changes the verdict."""
    cols = [list(core.GRID).index(4), list(core.GRID).index(8)]
    dev = np.abs(np.asarray(f_hat, float)[cols] - np.asarray(f_pred, float)[cols])
    j = int(np.argmax(dev))
    n = int(core.GRID[cols[j]])
    gap = float(abs(dev[j] - H1_BAND))
    lim = float(2.0 * np.asarray(sigma_dF, float)[cols[j]])
    return {"n_decisive": n, "abs_deviation": float(dev[j]), "distance_to_band": gap, "two_sigma_d_F": lim,
            "within_drift": bool(gap < lim)}


def h4_margins(f_boot, f_pred, sigma_dR, verdict):
    """H4: q97.5(n) of F_boot/F_pred, the margins 1 - q97.5(n) next to sigma_d,R(n), and the labels; each n is compared with its
    own sigma_d,R(n): HOLDS -> "holds within drift" iff 1 - q97.5(n) < 2 sigma_d,R(n) at SOME n; FAILS -> "fails within drift"
    iff q97.5(n) - 1 < 2 sigma_d,R(n) at EVERY n where q97.5(n) >= 1. ``n_concerned``: the n satisfying the HOLDS condition, or the
    n with q97.5(n) >= 1 (FAILS)."""
    q = np.percentile(np.asarray(f_boot, float) / np.asarray(f_pred, float)[None, :], 97.5, axis=0)
    margin = 1.0 - q
    sd = np.asarray(sigma_dR, float)
    two = 2.0 * sd
    out = {"q975": [float(x) for x in q], "margin": [float(x) for x in margin], "sigma_d_R": [float(x) for x in sd],
           "two_sigma_d_R": [float(x) for x in two], "label": None, "n_concerned": []}
    if verdict == "HOLDS":
        idx = np.where(margin < two)[0]
        out["n_concerned"] = [int(core.GRID[i]) for i in idx]
        out["label"] = "holds within drift" if idx.size else None
    elif verdict == "FAILS":
        idx = np.where(q >= 1.0)[0]
        out["n_concerned"] = [int(core.GRID[i]) for i in idx]
        out["label"] = "fails within drift" if idx.size and bool(np.all((q - 1.0)[idx] < two[idx])) else None
    return out


def power_reading(verdict, power):
    """PREREG section 4: a FAILS of a confirmatory criterion reads "fails" if its power at submission is >= 0.8 and "not
    demonstrated" if it is below 0.8. ``power`` is None only if the power file is missing or mismatched, which is a K3 failure
    (yorumlanamaz): there is then no reading."""
    if verdict != "FAILS" or power is None:
        return None
    return "fails" if power >= POWER_MIN else "not demonstrated"


def build_labels(h1_label, h4_label, rule14_ok, device_change, exec_label, q1_replicate=False):
    """The labels attached to the answer (PREREG section 4): within drift (H1), holds/fails within drift (H4), H1 one-sided,
    the Q1 replicate label, device change, and the execution-time calibration label."""
    labels = []
    if h1_label and h1_label.get("within_drift"):
        labels.append({"label": "within drift", "applies_to": "H1"})
    if h4_label and h4_label.get("label"):
        labels.append({"label": h4_label["label"], "applies_to": "H4"})
    if not rule14_ok:
        labels.append({"label": "H1 one-sided", "applies_to": "H1"})
    if q1_replicate:
        labels.append({"label": Q1_LABEL, "applies_to": "Q1"})
    if device_change:
        labels.append({"label": "device change", "applies_to": "I-6"})
    if exec_label:
        labels.append({"label": exec_label, "applies_to": "section 3"})
    return labels


def _outcome(verdict, reading):
    """("HOLDS", None) | ("FAILS", "fails" | "not demonstrated") | ("UNDEFINED", None)."""
    if verdict == "HOLDS":
        return ("HOLDS", None)
    if verdict == "FAILS":
        return ("FAILS", "fails" if reading == "fails" else "not demonstrated")
    return ("UNDEFINED", None)


def assemble_answer(h1, h1_reading, h4, h4_reading, controls_ok, labels=()):
    """The answer to Q1 and Q2 assembled mechanically from the pre-written sentences of PREREG section 4 (v3): the Q1 sentence
    (H1's outcome and reading), the Q2 sentence (H4's outcome and reading), the joint sentence only for the four listed
    combinations, then the labels. A control failure gives "yorumlanamaz" alone. ``h1``, ``h4``: "HOLDS" | "FAILS" | other
    (UNDEFINED); ``*_reading``: "fails" | "not demonstrated" (used only for FAILS).
    Returns {"answer", "q1", "q2", "joint", "labels"}."""
    out = {"labels": [dict(x) for x in labels], "q1": None, "q2": None, "joint": None}
    if not controls_ok:
        out["answer"] = ANSWER_UNINTERPRETABLE
        return out
    o1, o4 = _outcome(h1, h1_reading), _outcome(h4, h4_reading)
    out["q1"], out["q2"] = Q1_SENTENCES[o1], Q2_SENTENCES[o4]
    out["joint"] = JOINT_SENTENCES.get((o1, o4))
    out["answer"] = " ".join(x for x in (out["q1"], out["q2"], out["joint"]) if x)
    return out


# ------------------------------------------------------------------------------------------- stopping-rule log (PREREG 1)
def read_log(run_dir):
    path = os.path.join(run_dir, ghz3_run.LOG_FILE)
    lines, bad = [], 0
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                if not raw.strip():
                    continue
                try:
                    lines.append(json.loads(raw))
                except ValueError:
                    bad += 1
    return lines, bad


def _utc(s):
    return datetime.datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=datetime.timezone.utc)


def _t(l):
    """The time of a log line for the stopping rule: its snapshot time if it has one, else its write time."""
    return _utc(l.get("snapshot_utc") or l["utc"])


def _checks_ok(l):
    """D-7, K2 and C-1 passed (whatever C-2 says), from the logged results (not from the exit code)."""
    return bool((l.get("d7") or {}).get("ok") and (l.get("k2") or {}).get("ok", True) and (l.get("c1") or {}).get("satisfied"))


def stopping_rule_report(lines):
    """The stopping rule of PREREG section 1 (v3) applied to log lines; reported, not enforced.
    An attempt is one --submit invocation that reached the checks (lines with the same ``invocation``; modes submit-refused,
    submit-checks-passed, submit-failed, submit-accepted); a missing/invalid quota or an existing job.json is not an attempt
    (submit-not-attempt). An invocation is refused if it has a submit-refused line, passing if it has a submit-checks-passed
    (or accepted / failed) line. Deviations:
      - an attempt on a UTC day (snapshot time) after a refused attempt of that day (so two refused attempts on one day too);
      - a passing --dry-run (D-7, K2 and C-1 passed in its logged results, whatever C-2 says) without a passing --submit whose
        snapshot time is 0 to 2 hours after the dry run's snapshot time.
    Also reported: every logged line whose C-1 passed but whose C-2 failed, with its quota."""
    notes = []
    sub = [l for l in lines if str(l.get("mode", "")).startswith("submit-") and l.get("mode") != "submit-not-attempt"
           and l.get("attempt") is not False]
    inv = {}
    for l in sub:
        inv.setdefault(l.get("invocation") or l.get("snapshot_utc") or l["utc"], []).append(l)
    attempts = []
    for key, ls in inv.items():
        modes = {l["mode"] for l in ls}
        attempts.append({"key": key, "time": _t(ls[0]), "day": str(ls[0].get("snapshot_utc") or ls[0]["utc"])[:8], "modes": sorted(modes),
                         "refused": "submit-refused" in modes, "passing": bool(modes & set(SUBMIT_PASSING_MODES)),
                         "failed": "submit-failed" in modes, "accepted": "submit-accepted" in modes})
    attempts.sort(key=lambda a: a["time"])
    first_refused = {}
    for a in attempts:
        if a["day"] in first_refused:
            notes.append(f"{a['day']}: attempt at {a['key']} after the refused attempt at {first_refused[a['day']]} of the same UTC day")
        if a["refused"] and a["day"] not in first_refused:
            first_refused[a["day"]] = a["key"]
    passing_submits = [a["time"] for a in attempts if a["passing"]]
    for l in lines:
        if l.get("mode") == "dry-run" and _checks_ok(l):
            t = _t(l)
            if not any(0 <= (ts - t).total_seconds() <= 2 * 3600 for ts in passing_submits):
                notes.append(f"passing --dry-run (snapshot {l.get('snapshot_utc') or l['utc']}) without a passing --submit within 2 hours")
    c1_pass_c2_fail = [{"utc": l.get("utc"), "snapshot_utc": l.get("snapshot_utc"), "mode": l.get("mode"),
                        "quota_seconds": l.get("quota_seconds"), "estimate_seconds": (l.get("c2") or {}).get("estimate_seconds"),
                        "required_seconds": (l.get("c2") or {}).get("required_seconds")}
                       for l in lines if (l.get("c1") or {}).get("satisfied") and l.get("c2") is not None
                       and not l["c2"].get("c2_satisfied")]
    return {"n_lines": len(lines), "n_dry_run": sum(1 for l in lines if l.get("mode") == "dry-run"),
            "n_attempts": len(attempts), "n_submit_refused": sum(1 for a in attempts if a["refused"]),
            "n_submit_failed": sum(1 for a in attempts if a["failed"]), "n_submit_accepted": sum(1 for a in attempts if a["accepted"]),
            "n_not_attempts": sum(1 for l in lines if l.get("mode") == "submit-not-attempt"),
            "n_fetch": sum(1 for l in lines if l.get("mode") == "fetch"),
            "c1_pass_c2_fail": c1_pass_c2_fail, "deviations_from_the_rule": notes}


def read_log_split(run_dir, job):
    """(all parsed lines, anchored lines, post-anchor lines): the anchored lines are the first ``dryrun_log_lines`` lines of the
    file (recorded in job.json at submission). Without a readable anchor everything counts as anchored."""
    path = os.path.join(run_dir, ghz3_run.LOG_FILE)
    parsed = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                try:
                    parsed.append(json.loads(raw))
                except ValueError:
                    parsed.append(None)
    try:
        n = int(job["dryrun_log_lines"])
    except Exception:  # noqa: BLE001
        n = len(parsed)
    ok = [l for l in parsed if l is not None]
    return ok, [l for l in parsed[:n] if l is not None], [l for l in parsed[n:] if l is not None]


def log_prefix_status(run_dir, job):
    """K3 additions: (1) the log's first ``dryrun_log_lines`` lines (recorded in job.json at submission) still have the recorded
    SHA-256; (2) no later line is dated before the submission (``submitted_utc``). Returns {"ok", "reason", "lines_after_anchor",
    "post_anchor_ok", "post_anchor_reason"}."""
    path = os.path.join(run_dir, ghz3_run.LOG_FILE)
    try:
        n, want = int(job["dryrun_log_lines"]), str(job["dryrun_log_sha256"])
    except Exception:  # noqa: BLE001
        return {"ok": False, "reason": "job.json carries no log anchor", "lines_after_anchor": None,
                "post_anchor_ok": False, "post_anchor_reason": "job.json carries no log anchor"}
    raws = []
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            raws = fh.readlines()
    if len(raws) < n:
        return {"ok": False, "reason": f"the log has {len(raws)} lines, fewer than the {n} recorded at submission",
                "lines_after_anchor": None, "post_anchor_ok": False, "post_anchor_reason": "the log is shorter than the anchor"}
    ok = ghz3_run.log_prefix_sha(path, n) == want
    post_ok, why = True, None
    for raw in raws[n:]:
        try:
            u = json.loads(raw).get("utc")
        except ValueError:
            u = None
        if not isinstance(u, str) or u < str(job.get("submitted_utc")):
            post_ok, why = False, f"a line after the anchor is dated {u!r}, before the submission {job.get('submitted_utc')}"
            break
    return {"ok": ok, "reason": None if ok else "the first lines of the log differ from the hash recorded at submission",
            "lines_after_anchor": len(raws) - n, "post_anchor_ok": post_ok, "post_anchor_reason": why}


def first_logged_fetch_status(run_dir, lines):
    """K3 addition: the execution calibration used is the first logged --fetch attempt; its file exists and its SHA-256 matches
    the log. Returns {"ok", "file", "reason", "n_logged_fetches"}."""
    fetches = [l for l in lines if l.get("mode") == "fetch"]
    if not fetches:
        return {"ok": False, "file": None, "reason": "no --fetch attempt is logged", "n_logged_fetches": 0}
    first = fetches[0]
    name, want = first.get("file"), first.get("file_sha256")
    path = os.path.join(run_dir, name) if name else None
    if not name or not os.path.isfile(path):
        return {"ok": False, "file": name, "reason": "the file of the first logged fetch is missing", "n_logged_fetches": len(fetches)}
    ok = core.sha256_file(path) == want
    return {"ok": ok, "file": name, "reason": None if ok else "the file's SHA-256 differs from the logged one",
            "n_logged_fetches": len(fetches)}


def job_time_status(timestamps, submitted_utc):
    """K3 addition: the job was created, and started running, at or after the submission time in job.json minus 10 minutes (the
    local clock versus the service's; from the saved metrics). Implemented: fails if a present timestamp is earlier than that, or
    if BOTH creation and start are missing
    (one missing timestamp is reported and the other decides). Returns {"ok", "created", "started", "reason"}."""
    ts = timestamps or {}
    created = ghz3_run._parse_dt(ts.get("created")) if ts.get("created") else None
    started = ghz3_run._parse_dt(ts.get("running") or ts.get("started")) if (ts.get("running") or ts.get("started")) else None
    out = {"created": None if created is None else created.isoformat(), "started": None if started is None else started.isoformat(),
           "ok": False, "reason": None}
    if created is None and started is None:
        out["reason"] = "neither a creation nor a start timestamp is available"
        return out
    try:
        sub = _utc(submitted_utc)
    except Exception:  # noqa: BLE001
        out["reason"] = "the submission time is unreadable"
        return out
    bad = [name for name, t in (("created", created), ("started", started)) if t is not None and t < sub - datetime.timedelta(seconds=ghz3_run.CLOCK_TOLERANCE_SECONDS)]
    out["ok"] = not bad
    out["reason"] = (f"{' and '.join(bad)} more than 10 minutes before the submission {submitted_utc}" if bad else
                     ("only one timestamp available" if (created is None or started is None) else None))
    return out


# -------------------------------------------------------------------------------- power file (K3) and execution calibration
def _close(a, b, tol=1e-9):
    """Recursive comparison: numbers within ``tol``, everything else equal."""
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
        return a is b or a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    return a == b


STUDY_FILES = ("ghz2_study.py", "ghz3_study_h4.py")


def power_file_status(run_dir, job, comps, code_dir=None, certs_dir=None, freeze_path=None, run1_dir=None, run2_dir=None,
                      n_datasets=None):
    """K3 additions (PREREG sections 4 and 5): run/power_run3.json exists and its SHA-256 equals job.json's; its input hashes
    equal those of the frozen certs/power.json (run-1 and run-2 data files) and of FREEZE_GHZ3.json (the study files) and the
    files now; its predictions are the snapshot's; and recomputing it from the snapshot's predictions gives the same numbers
    (the method is deterministic). Returns {"ok", "checks": {"exists_hash", "inputs", "recompute"}, "reasons", "power", "data"}."""
    code_dir = code_dir or HERE
    certs_dir = certs_dir or os.path.join(code_dir, "certs")
    n_datasets = n_datasets or ghz3_run.POWER_DATASETS
    path = os.path.join(run_dir, "power_run3.json")
    out = {"ok": False, "checks": {"exists_hash": False, "inputs": False, "recompute": False}, "reasons": [], "power": None,
           "data": None, "environment": None}
    if not os.path.isfile(path):
        out["reasons"].append("run/power_run3.json is missing")
        return out
    out["checks"]["exists_hash"] = core.sha256_file(path) == job.get("power_run3_sha256")
    if not out["checks"]["exists_hash"]:
        out["reasons"].append("its SHA-256 differs from job.json's")
    try:
        pw = _read_json(path)
        out["data"] = pw
        out["power"] = {"H1": float(pw["power"]["H1"]), "H4": float(pw["power"]["H4"])}
        bad = []
        try:
            frozen = {i["file"]: i["sha256"] for i in _read_json(os.path.join(certs_dir, "power.json"))["inputs"]}
        except Exception as exc:  # noqa: BLE001
            frozen = {}
            bad.append(f"certs/power.json unreadable ({type(exc).__name__})")
        try:
            manifest = {str(k).replace("\\", "/"): v for k, v in _read_json(freeze_path or os.path.join(code_dir, ghz3_run.MANIFEST_NAME))["files"].items()}
        except Exception as exc:  # noqa: BLE001
            manifest = {}
            bad.append(f"FREEZE_GHZ3.json unreadable ({type(exc).__name__})")
        for item in pw["inputs"]:
            f, h = item["file"], item["sha256"]
            expected = manifest.get(f) if f in STUDY_FILES else frozen.get(f)
            if expected is None or h != expected:
                bad.append(f"input {f}: recorded hash differs from the frozen one")
            fp = os.path.normpath(os.path.join(code_dir, f))
            if not os.path.isfile(fp) or core.sha256_file(fp) != h:
                bad.append(f"input {f}: the file now does not match the recorded hash")
        c = {str(k): v for k, v in comps.items()}
        for k in ("F_pred", "P_pred", "C_pred"):
            if any(abs(pw["predictions"][k][str(n)] - c[str(n)][k]) > MODEL_TOL for n in core.GRID):
                bad.append(f"its {k} are not the snapshot's")
        out["checks"]["inputs"] = not bad
        out["reasons"].extend(bad)
        env_now = ghz3_run.environment_info()
        env_rec = pw.get("environment")
        diff = {k: [(env_rec or {}).get(k), env_now.get(k)] for k in env_now if (env_rec or {}).get(k) != env_now.get(k)}
        out["environment"] = {"recorded_in_power_file": env_rec, "recorded_in_job_json": job.get("environment"), "now": env_now,
                              "differs": diff}
        try:
            exp = ghz3_run.compute_power(ghz3_run.pred_arrays_from_comps(comps), run1_dir, run2_dir, code_dir,
                                         n_datasets=n_datasets, seed=ghz3_run.POWER_SEED, label=pw.get("label", ""),
                                         snapshot_sha256=pw.get("snapshot_sha256"), device_change=bool(pw.get("device_change")))
            exp_n = {k: v for k, v in exp.items() if k != "environment"}
            pw_n = {k: v for k, v in pw.items() if k != "environment"}
            same = pw.get("n_datasets") == n_datasets and pw.get("seed") == ghz3_run.POWER_SEED and _close(exp_n, pw_n)
        except Exception as exc:  # noqa: BLE001
            same = False
            out["reasons"].append(f"recomputation failed ({type(exc).__name__})")
        out["checks"]["recompute"] = bool(same)
        if not same:
            out["reasons"].append("recomputing the power from the snapshot's predictions does not give the file's numbers")
            if diff:
                out["reasons"].append("version mismatch is the likely cause: the analysis environment differs from the one recorded "
                                      "at submission: " + ", ".join(f"{k}: {a} -> {b}" for k, (a, b) in diff.items()))
    except Exception as exc:  # noqa: BLE001
        out["reasons"].append(f"unreadable ({type(exc).__name__})")
    out["ok"] = all(out["checks"].values())
    return out


def inputs_differ(comps_a, comps_b, rtol=EXEC_RTOL):
    """{field: differs} for the M2 inputs of S_48: the qubit list S exactly, every other input value within the relative
    tolerance ``rtol`` (|x - y| <= rtol * max(|x|, |y|); two zeros are equal)."""
    a, b = ghz3_run.m2_inputs(comps_a), ghz3_run.m2_inputs(comps_b)
    out = {}
    for k in ghz3_run.C1_FIELDS:
        x, y = a[k], b[k]
        if k == "S":
            out[k] = list(x) != list(y)
        elif len(x) != len(y):
            out[k] = True
        else:
            out[k] = any(abs(p - q) > rtol * max(abs(p), abs(q)) for p, q in zip(x, y))
    return out


def dates_before_submission(dates, S, edges, one_qubit_gates, submitted_utc):
    """Fallback check (PREREG section 3): True iff the calibration date of every M2 input of S_48 (T1, T2, readout error of the
    qubits of S; every parameter of the cz gates of the tree ``edges``; of the one-qubit gates ``one_qubit_gates``) is before
    the submission time (job.json ``submitted_utc``). A missing record or date, or an unreadable time -> (False, reason)."""
    try:
        sub = _utc(submitted_utc)
    except Exception:  # noqa: BLE001
        return False, "the submission time is unreadable"
    recs, missing = ghz3_run.m2_target_records(dates, S, edges, one_qubit_gates)
    if missing:
        return False, "no calibration record for " + ", ".join(missing[:3])
    for r in recs:
        d = ghz3_run._parse_dt(r["date"])
        if d is None or not d < sub:
            return False, f"{r['gate'] or 'qubit'}{r['qubits']} {r['param']}: date {r['date']} is not before the submission"
    return True, None


def history_dates_ok(dates, S, edges, ones, start):
    """PREREG section 3: a history result is accepted only if every M2-input calibration date in it is at or before the
    execution start ``start`` (aware datetime). Returns (ok, reason)."""
    if not dates:
        return False, "the history result carries no calibration dates"
    recs, missing = ghz3_run.m2_target_records(dates, S, edges, ones)
    if missing:
        return False, "no calibration record for " + ", ".join(missing[:3])
    for r in recs:
        d = ghz3_run._parse_dt(r["date"])
        if d is None or d > start:
            return False, f"{r['gate'] or 'qubit'}{r['qubits']} {r['param']}: date {r['date']} is after the execution start"
    return True, None


def differing_input_dependencies(comps_exec, comps_snap, entries, rtol=EXEC_RTOL):
    """For every M2 input value of S_48 that differs (beyond ``rtol``) between the execution-time and the snapshot's inputs:
    (description, [date keys]) where the input counts as recalibrated if ANY of the keys has a later date (one key for a qubit
    parameter or a gate error; every gate length for an idle time); keys None = the input cannot be dated (S, shape)."""
    a, b = ghz3_run.m2_inputs(comps_exec), ghz3_run.m2_inputs(comps_snap)
    gk = ghz3_run.m2_gate_keys(entries)
    S = b["S"]
    lengths = [("g", "cz", tuple(e), "gate_length") for e in gk["cz"]] + \
              [("g", name, (q,), "gate_length") for name, q in sorted(set(gk["g1_pop"]) | set(gk["g1_par"]))]
    out = []
    for field in ghz3_run.C1_FIELDS:
        x, y = a[field], b[field]
        if field == "S":
            if list(x) != list(y):
                out.append(("S", None))
            continue
        if len(x) != len(y):
            out.append((f"{field} (length)", None))
            continue
        for i, (p, q) in enumerate(zip(x, y)):
            if abs(p - q) <= rtol * max(abs(p), abs(q)):
                continue
            if field in ("t1", "t2", "ro_err"):
                keys = [("q", S[i], {"t1": "T1", "t2": "T2", "ro_err": "readout_error"}[field])]
            elif field == "cz_err":
                keys = [("g", "cz", tuple(gk["cz"][i]), "gate_error")] if i < len(gk["cz"]) else None
            elif field in ("g1_pop_err", "g1_par_err"):
                lst = gk["g1_pop" if field == "g1_pop_err" else "g1_par"]
                keys = [("g", lst[i][0], (lst[i][1],), "gate_error")] if i < len(lst) else None
            else:                                   # idle
                keys = lengths
            out.append((f"{field}[{i}]", keys))
    return out


def changed_inputs_have_later_dates(comps_exec, comps_snap, entries, dates_exec, dates_sub):
    """PREREG section 3: "changed" requires every differing input to carry a later calibration date than at submission.
    Returns (ok, reason)."""
    if not dates_sub:
        return False, "no calibration dates were recorded at submission"
    for desc, keys in differing_input_dependencies(comps_exec, comps_snap, entries):
        if keys is None:
            return False, f"input {desc} differs and cannot be dated"
        later = False
        for k in keys:
            d_exec, d_sub = ghz3_run.date_of(dates_exec, k), ghz3_run.date_of(dates_sub, k)
            if d_exec is not None and d_sub is not None and d_exec > d_sub:
                later = True
                break
        if not later:
            return False, f"input {desc} differs without a later calibration date than at submission"
    return True, None


def execution_calibration(run_dir, entries, comps_snap, submitted_utc=None, sub_dates=None, use_file=None):
    """PREREG section 3 (v3). Uses ``use_file`` (the first logged --fetch attempt; None = the first saved attempt by name, "" = none)
    and returns {"status", "label", "reason", "comps_exec", ...}; the M2 inputs of S_48 are recomputed on the saved calibration with
    the durations and schedule of the submitted circuits and compared with the snapshot's (relative tolerance 1e-6, S exact):
      history result (accepted only if every M2-input date in it is at or before the execution start and it can be used):
          "equal" (label None; snapshot predictions), or "changed" (label "calibration changed before execution"; the primary
          predictions ``comps_exec``) if every differing input has a later date than at submission (``sub_dates`` = the dates
          recorded in calibration_check.json), else "unverified_difference" (label "not verified"; snapshot predictions)
      history unavailable, rejected, or failing in ANY way (hash mismatch, exception, M2 cannot be computed): the saved current
          calibration: "verified_no_recalibration" (label "verified: no recalibration since submission"; snapshot predictions)
          iff its M2 inputs of S_48 equal the snapshot's and the date of every M2 input is before ``submitted_utc``; otherwise
          "unavailable" (label "not verified"; snapshot predictions)."""
    files = ghz3_run.exec_files(run_dir)
    chosen = files[0] if (use_file is None and files) else (use_file if use_file else None)
    out = {"status": "unavailable", "label": LABEL_NOT_VERIFIED, "reason": None, "comps_exec": None, "path": None,
           "execution_start_utc": None, "timestamps": None, "usage": None, "job_usage_seconds": None,
           "attempt_files": files, "attempt_used": chosen}
    if chosen is None or not os.path.isfile(os.path.join(run_dir, chosen)):
        out["reason"] = (f"no run/{ghz3_run.EXEC_PREFIX}*.json file (the calibration was not fetched)" if not files else
                         "the execution-calibration file of the first logged fetch is missing")
        return out
    try:
        info = _read_json(os.path.join(run_dir, chosen))
        for k in ("timestamps", "usage", "job_usage_seconds", "execution_start_utc"):
            out[k] = info.get(k)
        S = ghz3_run.m2_inputs(comps_snap)["S"]
        tree, ones = ghz3_run.m2_date_targets(entries)
        note = None
        if info.get("available"):                                        # the history path; ANY failure falls through
            try:
                snap = info["snapshot"]
                if core.snapshot_hash(snap) != info["snapshot_sha256"]:
                    raise ValueError("the execution-time snapshot does not match its SHA-256")
                start = ghz3_run._parse_dt(info.get("execution_start_iso") or (info.get("timestamps") or {}).get("running")
                                           or (info.get("execution_start_utc") and
                                               datetime.datetime.strptime(info["execution_start_utc"], "%Y%m%dT%H%M%SZ").isoformat() + "+00:00"))
                ok, why = history_dates_ok(info.get("dates"), S, tree, ones, start)
                if not ok:
                    note = f"history result rejected ({why})"
                else:
                    comps_exec = core.model_all(entries, core.target_from_snapshot(snap))
                    differ = inputs_differ(comps_exec, comps_snap)
                    if not any(differ.values()):
                        out.update(path="history", inputs_differ=differ, exec_snapshot_sha256=info["snapshot_sha256"],
                                   status="equal", label=None, comps_exec=comps_exec)
                        return out
                    later_ok, why2 = changed_inputs_have_later_dates(comps_exec, comps_snap, entries, info["dates"], sub_dates)
                    out.update(path="history", inputs_differ=differ, exec_snapshot_sha256=info["snapshot_sha256"])
                    if later_ok:
                        out.update(status="changed", label=LABEL_CHANGED, comps_exec=comps_exec)
                    else:
                        out.update(status="unverified_difference", label=LABEL_NOT_VERIFIED, reason=why2)
                    return out
            except Exception as exc:  # noqa: BLE001
                note = f"history result unusable ({type(exc).__name__}: {exc})"
                out.update(path=None, comps_exec=None)
                out.pop("inputs_differ", None)
                out.pop("exec_snapshot_sha256", None)
        cur = info.get("current")                                        # the fallback path
        if not cur:
            out["reason"] = ((note + "; ") if note else "") + (
                f"the calibration history was not retrieved ({info.get('error')}) and the current calibration was not saved "
                f"({info.get('current_error')})")
            return out
        out["path"] = "current calibration (history " + ("rejected or unusable)" if note else "unavailable)")
        snap = cur["snapshot"]
        if core.snapshot_hash(snap) != cur["snapshot_sha256"]:
            out["reason"] = ((note + "; ") if note else "") + "the saved current-calibration snapshot does not match its SHA-256"
            return out
        comps_cur = core.model_all(entries, core.target_from_snapshot(snap))
        differ = inputs_differ(comps_cur, comps_snap)
        out["inputs_differ"] = differ
        if any(differ.values()):
            out["reason"] = ((note + "; ") if note else "") + "the current calibration's M2 inputs of S_48 differ from the snapshot's"
            return out
        ok, why = dates_before_submission(cur.get("dates") or {}, S, tree, ones, submitted_utc)
        if not ok:
            out["reason"] = ((note + "; ") if note else "") + f"calibration dates do not prove 'no recalibration since submission': {why}"
            return out
        out.update(status="verified_no_recalibration", label=LABEL_VERIFIED, reason=note, exec_snapshot_sha256=cur["snapshot_sha256"])
        return out
    except Exception as exc:  # noqa: BLE001
        out.update(status="unavailable", label=LABEL_NOT_VERIFIED, comps_exec=None,
                   reason=f"execution-time calibration could not be used ({type(exc).__name__})")
        return out


# ------------------------------------------------------------------------------------------- descriptive comparison with runs 1, 2
def run1_under_m2(run1_dir=None):
    """Run 1's F, P, C and M2's F_pred per n, recomputed with the ghz2_core functions from run 1's counts, snapshot and
    submitted circuits (``<run1_dir>/run``). Returns ({n: {"F","P","C","F_pred","R"}}, {"source", "max_abs_F_diff_vs_RESULTS_GHZ"})."""
    run1_dir = run1_dir or RUN1_DIR
    rd = os.path.join(run1_dir, "run")
    job = _read_json(os.path.join(rd, "job.json"))
    sf = _read_json(os.path.join(rd, job["snapshot_file"]))
    snap = sf["snapshot"]
    if core.snapshot_hash(snap) != sf["sha256"]:
        raise RuntimeError("run 1's snapshot does not match its SHA-256")
    counts = _read_json(os.path.join(rd, "counts.json"))["circuits"]
    with open(os.path.join(rd, "circuits.qpy"), "rb") as fh:
        by_name = {c.name: c for c in qpy.load(fh)}
    target = core.target_from_snapshot(snap)
    ns = sorted({m["n"] for m in job["manifest"] if m["family"] == "GHZ"})
    rows = {}
    for n in ns:
        S = core.selection(snap, n)[0]
        comp = core.model_components(by_name[core.circuit_name("GHZ", n, "POP")],
                                     by_name[core.circuit_name("GHZ", n, "PAR", 0)], target, S)
        est = core.point_estimates(counts, n, "GHZ")
        rows[n] = {"F": float(est["F"]), "P": float(est["P"]), "C": float(est["C"]), "F_pred": float(comp["F_pred"]),
                   "R": float(est["F"] / comp["F_pred"])}
    meta = {"source": f"recomputed with ghz2_core from {os.path.basename(run1_dir)}/run (counts, snapshot, circuits.qpy)"}
    res1 = os.path.join(run1_dir, "RESULTS_GHZ.json")
    if os.path.isfile(res1):
        t = {row["n"]: row for row in _read_json(res1)["table"]}
        meta["max_abs_F_diff_vs_RESULTS_GHZ"] = float(max(abs(rows[n]["F"] - t[n]["F_meas"]) for n in rows if n in t))
    return rows, meta


def comparison_with_earlier_runs(r3_table, run1_dir=None, run2_dir=None):
    """R(n) of runs 1, 2 and 3 side by side (descriptive, I-4: not pooled) and run 2's small-n drift. Never raises: a missing
    piece is recorded as such."""
    run2_dir = run2_dir or RUN2_DIR
    out = {"note": "descriptive; runs are not pooled (I-4). R = F_meas / F_pred under M2."}
    r2 = None
    try:
        r2 = {t["n"]: t for t in _read_json(os.path.join(run2_dir, "RESULTS_GHZ2.json"))["table"]}
        out["run2_source"] = "RESULTS_GHZ2.json (frozen run 2)"
    except Exception as exc:  # noqa: BLE001
        out["run2_source"] = f"unavailable ({type(exc).__name__})"
    try:
        r1, meta = run1_under_m2(run1_dir)
        label = meta["source"]
        out["run1_cross_check"] = {k: v for k, v in meta.items() if k != "source"}
    except Exception as exc:  # noqa: BLE001
        r1 = {n: {"R": v, "F": None, "P": None, "C": None, "F_pred": None} for n, v in RUN1_QUOTED_R.items()}
        label = (f"QUOTED (exploratory) from run 2's PREREG section 0, rounded to 2 decimals; recomputation failed "
                 f"({type(exc).__name__}: {exc})")
    out["run1_source"] = label
    rows = []
    for t in r3_table:
        n = t["n"]
        rows.append({"n": n, "R_run1": None if n not in r1 else r1[n]["R"],
                     "R_run2": None if r2 is None or n not in r2 else r2[n]["R"], "R_run3": t["R"]})
    out["R_table"] = rows
    drift = {}
    for n in (4, 8):
        i = list(core.GRID).index(n)
        d = {"F_run3": r3_table[i]["F"], "F_pred_run3": r3_table[i]["F_pred"], "H1_deviation_run3": r3_table[i]["F"] - r3_table[i]["F_pred"]}
        if r2 is not None:
            d["F_run2"] = r2[n]["F"]
            d["C_run2"] = r2[n]["C"]
            d["F_run3_minus_run2"] = r3_table[i]["F"] - r2[n]["F"]
            d["C_run3_minus_run2"] = r3_table[i]["C"] - r2[n]["C"]
        if r1 is not None and n in r1 and r1[n]["F"] is not None:
            d["F_run1"] = r1[n]["F"]
            d["C_run1"] = r1[n]["C"]
            if r2 is not None:
                d["F_run2_minus_run1"] = r2[n]["F"] - r1[n]["F"]
                d["C_run2_minus_run1"] = r2[n]["C"] - r1[n]["C"]
        drift[str(n)] = d
    out["small_n_drift"] = drift
    return out


def tracking_table(f_hat, f_boot, f_pred, run2_dir=None, sigma_dF=None):
    """Per n: the measured change F_run3 - F_run2 with a 95% percentile interval (run 3's and run 2's independent bootstrap
    replicates, paired by index; CI: shot noise only) and sigma_d,F(n) next to it, against the predicted change
    F_pred,run3 - F_pred,run2 (descriptive)."""
    run2_dir = run2_dir or RUN2_DIR
    try:
        z = np.load(os.path.join(run2_dir, "RESULTS_GHZ2_boot.npz"))
        f2_hat, f2_boot, f2_pred = np.asarray(z["F_hat"], float), np.asarray(z["F_boot"], float), np.asarray(z["F_pred"], float)
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": type(exc).__name__}
    m = min(len(f_boot), len(f2_boot))
    diff_b = np.asarray(f_boot, float)[:m] - f2_boot[:m]
    rows = []
    for i, n in enumerate(core.GRID):
        meas = float(f_hat[i] - f2_hat[i])
        lo, hi = np.percentile(diff_b[:, i], [2.5, 97.5])
        pred_change = float(f_pred[i] - f2_pred[i])
        rows.append({"n": n, "measured_change": meas, "ci": [float(lo), float(hi)], "ci_kind": "shot noise only",
                     "sigma_d_F": None if sigma_dF is None else float(sigma_dF[i]),
                     "predicted_change": pred_change, "predicted_inside_ci": bool(lo <= pred_change <= hi)})
    return {"available": True, "ci_kind": "shot noise only", "rows": rows}


# ----------------------------------------------------------------------------------------------------------------- analysis
def _pred_dict(comps):
    c = {str(k): v for k, v in comps.items()}
    return {k: np.array([c[str(n)][k] for n in core.GRID]) for k in ("P_pred", "C_pred", "F_pred", "F_M")}


def run_analysis(root=HERE, run_dir=None, out_dir=None, B=core.BOOT_B, write=True, run2_dir=None, run1_dir=None,
                 code_dir=None, certs_dir=None, power_n_datasets=None):
    run_dir = run_dir or os.path.join(root, "run")
    out_dir = out_dir or root
    certs_dir = certs_dir or os.path.join(root, "certs")
    code_dir = code_dir or HERE
    job, snap_file, counts, circuits, model_saved = load_run(run_dir)
    snap = snap_file["snapshot"]
    manifest = job["manifest"]

    # ---- K3 (post-run and re-check of the pre-run items)
    k3 = {}
    k3["snapshot_hash_matches_file"] = core.snapshot_hash(snap) == snap_file["sha256"]
    k3["snapshot_hash_matches_job"] = snap_file["sha256"] == job["snapshot_sha256"]
    k3["job_id_saved"] = bool(job.get("job_id")) and counts.get("job_id") == job["job_id"]
    names = [m["name"] for m in manifest]
    k3["circuits_match_manifest"] = [c.name for c in circuits] == names and list(counts["order"]) == names
    entries, integ_ok = [], True
    sel = {}
    for m, tc in zip(manifest, circuits):
        n = m["n"]
        if n not in sel:
            sel[n] = core.selection(snap, n)
        S, T, _p = sel[n]
        try:
            core.check_integrity(tc, n, S, T)
        except core.IntegrityError:
            integ_ok = False
        entries.append({**m, "S": S, "T": T, "circuit": tc})
    k3["two_qubit_count_n_minus_1_all"] = integ_ok
    shots = job["shots"]
    k3["count_totals_equal_shots"] = all(
        sum(regs[r].values()) == shots for regs in counts["circuits"].values() for r in regs
    ) and all("meas" in regs for regs in counts["circuits"].values())
    # run-3 additions
    try:
        ghz3_run.code_identity(code_dir, run2_dir)
        k3["core_and_study_sha256_equal_run2_frozen"] = True
    except core.FreezeError:
        k3["core_and_study_sha256_equal_run2_frozen"] = False

    # ---- model M2 (and reference M) from the snapshot-rebuilt Target; must equal the saved model (K3)
    target = core.target_from_snapshot(snap)
    comps = core.model_all(entries, target)
    pred_snap = _pred_dict(comps)
    saved = {k: np.array([model_saved["components"][str(n)][k] for n in core.GRID]) for k in pred_snap}
    k3["m2_recomputed_equals_saved_model"] = bool(all(np.max(np.abs(pred_snap[k] - saved[k])) < MODEL_TOL for k in pred_snap))

    # ---- C-1 recomputed with the v3 rule, run-2 hashes, rule-14 recheck, power file, log prefix (K3 additions)
    calib = {"file_exists": False}
    ref, c1 = None, None
    try:
        ref = ghz3_run.load_run2_reference(run2_dir)
        c1 = ghz3_run.c1_check(ref["comps"], comps, ref["snap"]["backend"], snap["backend"])
        calib["recomputed"] = {k: c1[k] for k in ("device_old", "device_new", "device_differs", "n_inputs_changed", "condition_a",
                                                  "max_abs_delta_F_pred", "threshold", "condition_b", "c1_satisfied",
                                                  "q1_max_abs_delta_F_pred_4_8", "q1_model_test")}
        calib["recomputed"]["inputs_changed"] = c1["inputs_changed"]
        calib["recomputed"]["delta_F_pred"] = {n: v["F_pred"]["diff"] for n, v in c1["delta_pred"].items()}
        k3["c1_recomputed_holds"] = bool(c1["c1_satisfied"])
    except Exception as exc:  # noqa: BLE001
        calib["recomputed"] = f"unavailable ({type(exc).__name__}: {exc})"
        k3["c1_recomputed_holds"] = False
    cc_path = os.path.join(run_dir, "calibration_check.json")
    cc = None
    if os.path.isfile(cc_path):
        cc = _read_json(cc_path)
        calib["file_exists"] = True
        calib["saved"] = {k: cc.get(k) for k in ("c1_satisfied", "device_run2", "device_run3", "device_differs", "n_inputs_changed",
                                                  "inputs_changed", "max_abs_delta_F_pred", "threshold", "q1_model_test",
                                                  "q1_max_abs_delta_F_pred_4_8", "q1_replicate_label",
                                                  "delta_pred_run3_minus_run2", "run2_snapshot_file_sha256",
                                                  "run2_model_file_sha256", "run3_snapshot_sha256", "rule14",
                                                  "m2_input_dates_error")}
    known = ghz3_run.RUN2_KNOWN or {}
    k3["run2_hashes_in_calibration_check_equal_known"] = bool(
        cc is not None and known and cc.get("run2_snapshot_file_sha256") == known.get("snapshot_file_sha256")
        and cc.get("run2_model_file_sha256") == known.get("model_file_sha256")
        and cc.get("run3_snapshot_sha256") == job.get("snapshot_sha256"))
    pw_status = power_file_status(run_dir, job, comps, code_dir, certs_dir, os.path.join(root, ghz3_run.MANIFEST_NAME),
                                  run1_dir, run2_dir, power_n_datasets)
    k3["power_run3_exists_and_hash_matches_job"] = pw_status["checks"]["exists_hash"]
    k3["power_run3_input_hashes_match_frozen"] = pw_status["checks"]["inputs"]
    k3["power_run3_recomputation_equal"] = pw_status["checks"]["recompute"]
    log_status = log_prefix_status(run_dir, job)
    k3["log_prefix_recorded_in_job_unchanged"] = log_status["ok"]
    k3["log_post_anchor_lines_not_before_submission"] = log_status["post_anchor_ok"]
    log_lines, anchored_lines, post_lines = read_log_split(run_dir, job)
    fetch_status = first_logged_fetch_status(run_dir, log_lines)
    k3["first_logged_fetch_file_exists_and_hash_matches"] = fetch_status["ok"]

    # ---- calibration in force at execution (PREREG section 3): the predictions in use (the first logged fetch attempt)
    ex = execution_calibration(run_dir, entries, comps, job.get("submitted_utc"), (cc or {}).get("m2_input_dates"),
                               use_file=fetch_status["file"] or "")
    job_time = job_time_status(ex.get("timestamps"), job.get("submitted_utc"))
    k3["job_created_and_started_after_submission"] = job_time["ok"]
    k3_ok = all(k3.values())
    if ex["status"] == "changed":
        comps_use, pred_use, secondary = ex["comps_exec"], _pred_dict(ex["comps_exec"]), pred_snap
    else:
        comps_use, pred_use, secondary = comps, pred_snap, None
    rule14_snapshot = ghz3_run.rule14_check(comps)
    rule14_use = ghz3_run.rule14_check(comps_use)
    rule14_ok = bool(rule14_snapshot["ok"] and rule14_use["ok"])
    calib["rule14_recheck"] = {"snapshot": rule14_snapshot, "in_use": rule14_use, "ok": rule14_ok,
                               "saved_at_submission": None if cc is None else cc.get("rule14")}
    # ---- C-1 per question (PREREG section 1): the Q1 replicate label (on the snapshot's predictions, as C-1; both reported)
    q1 = {"threshold": ghz3_run.Q1_THRESHOLD, "label_text": Q1_LABEL}
    if c1 is not None:
        q1["max_abs_dF_4_8_snapshot"] = c1["q1_max_abs_delta_F_pred_4_8"]
        q1["model_test"] = bool(c1["q1_model_test"])
        q1["max_abs_dF_4_8_in_use"] = float(max(abs(comps_use[n]["F_pred"] - ref["comps"][str(n)]["F_pred"]) for n in (4, 8)))
        q1["in_use_differs_from_snapshot"] = bool(q1["max_abs_dF_4_8_in_use"] != q1["max_abs_dF_4_8_snapshot"])
        q1["in_use_model_test"] = bool(q1["max_abs_dF_4_8_in_use"] >= ghz3_run.Q1_THRESHOLD)
    elif cc is not None and cc.get("q1_model_test") is not None:
        q1["model_test"] = bool(cc["q1_model_test"])
        q1["max_abs_dF_4_8_snapshot"] = cc.get("q1_max_abs_delta_F_pred_4_8")
        q1["note"] = "from calibration_check.json (the recomputation was unavailable)"
    else:
        q1["model_test"] = None
    q1["replicate_label_attached"] = q1.get("model_test") is False

    # ---- estimators + bootstrap
    res = core.analyze_counts(counts["circuits"], B=B)
    if ([int(x) for x in res["n"]] != list(ghz2_study.GRID) or list(core.GRID) != list(ghz2_study.GRID)
            or list(core.GRID) != list(ghz3_study_h4.GRID)):
        raise RuntimeError("analysed column order differs from the studies' GRID; refusing to apply the criteria")

    def data_for(pred):
        return {"F_pred": pred["F_pred"], "P_pred": pred["P_pred"], "C_pred": pred["C_pred"],
                "F_hat": res["F_hat"], "P_hat": res["P"], "C_hat": res["C"],
                "F_boot": res["F_boot"], "P_boot": res["P_boot"], "C_boot": res["C_boot"]}

    crit = apply_criteria(data_for(pred_use))
    crit_secondary = apply_criteria(data_for(secondary)) if secondary is not None else None

    # ---- K1, K2 (design check and binding) and headline
    k1, k1_ok = k1_verdict(res["mix"])
    k2_design = k2_status(certs_dir)
    try:
        k2_bind = k2_noiseless(entries)
    except Exception as exc:  # noqa: BLE001
        k2_bind = {"pass": False, "detail": None, "error": type(exc).__name__}
    k2 = {"pass": bool(k2_design["pass"] and k2_bind["pass"]), "design_check": k2_design, "binding": k2_bind}
    interpretable = bool(k1_ok and k2["pass"] and k3_ok)
    h2 = h2_report(res["F_hat"], res["F_boot"], pred_use["F_pred"])
    ci_excludes_half = None
    if h2["n_meas_point"] > 0:
        i = list(core.GRID).index(h2["n_meas_point"])
        ci_excludes_half = bool(res["F_lo"][i] > 0.5)

    # ---- drift, labels, readings, the answer
    try:
        sigma = ghz3_run.drift_sigmas(ghz3_run.power_inputs(run1_dir, run2_dir))
        sigma_info = {"sigma_rel_P": sigma["P"], "sigma_rel_C": sigma["C"]}
        sdF, sdR = drift_quantities(pred_use["P_pred"], pred_use["C_pred"], pred_use["F_pred"], sigma)
    except Exception as exc:  # noqa: BLE001
        sigma, sdF, sdR = None, None, None
        sigma_info = {"error": f"unavailable ({type(exc).__name__})"}
    h1_lab = (h1_drift_label(res["F_hat"], pred_use["F_pred"], sdF, crit["H1_small_n_accuracy"])
              if sdF is not None and crit["H1_small_n_accuracy"] in ("HOLDS", "FAILS") else None)
    h4_lab = h4_margins(res["F_boot"], pred_use["F_pred"], sdR, crit["H4_overprediction_every_n"]) if sdR is not None else None
    powers = pw_status["power"] if pw_status["ok"] else None          # always the submission power on the snapshot's predictions
    reads = {"H1_small_n_accuracy": power_reading(crit["H1_small_n_accuracy"], None if powers is None else powers["H1"]),
             "H4_overprediction_every_n": power_reading(crit["H4_overprediction_every_n"], None if powers is None else powers["H4"])}
    device_change = str(job["backend"]) != str(ref["snap"]["backend"] if ref else "ibm_kingston")
    labels = build_labels(h1_lab, h4_lab, rule14_ok, device_change, ex["label"], q1["replicate_label_attached"])
    answer = assemble_answer(crit["H1_small_n_accuracy"], reads["H1_small_n_accuracy"], crit["H4_overprediction_every_n"],
                             reads["H4_overprediction_every_n"], interpretable, labels)

    table = []
    h4_q = np.percentile(res["F_boot"] / pred_use["F_pred"][None, :], 97.5, axis=0)
    for i, n in enumerate(core.GRID):
        row = {
            "n": n,
            "P": float(res["P"][i]), "P_ci": [float(res["P_lo"][i]), float(res["P_hi"][i])], "P_pred": float(pred_use["P_pred"][i]),
            "C": float(res["C"][i]), "C_ci": [float(res["C_lo"][i]), float(res["C_hi"][i])], "C_pred": float(pred_use["C_pred"][i]),
            "F": float(res["F_hat"][i]), "F_ci": [float(res["F_lo"][i]), float(res["F_hi"][i])], "F_pred": float(pred_use["F_pred"][i]),
            "R": float(res["F_hat"][i] / pred_use["F_pred"][i]) if pred_use["F_pred"][i] > 0 else None,
            "H4_ratio_q975": float(h4_q[i]), "H4_margin": float(1.0 - h4_q[i]),
            "sigma_d_F": None if sdF is None else float(sdF[i]), "sigma_d_R": None if sdR is None else float(sdR[i]),
            "F_M_reference": float(pred_use["F_M"][i]),
            "C_re": float(res["C_re"][i]), "C_re_ci": [float(res["C_re_lo"][i]), float(res["C_re_hi"][i])],
        }
        if secondary is not None:
            row["F_pred_snapshot_secondary"] = float(secondary["F_pred"][i])
        table.append(row)
    comparison = comparison_with_earlier_runs(table, run1_dir, run2_dir)
    tracking = tracking_table(res["F_hat"], res["F_boot"], pred_use["F_pred"], run2_dir, sdF)
    log_bad = read_log(run_dir)[1]
    accepted_post = [l for l in post_lines if l.get("mode") == "submit-accepted"][:1]       # the accepted line of this job
    log_report = stopping_rule_report(anchored_lines + accepted_post)
    accepted = [l for l in log_lines if l.get("mode") == "submit-accepted"]
    log_report["accepted_line_predictions_hash_matches_snapshot"] = (
        None if not accepted else accepted[-1].get("predictions_sha256") == ghz3_run.predictions_sha256(comps))
    log_report["n_post_anchor_lines_not_used_for_deviations"] = len(post_lines) - len(accepted_post)
    results = {
        "study": "GHZ run 3: frozen run-2 design on a new calibration (PREREG run-3 v3)",
        "backend": job["backend"], "job_id": job["job_id"], "submitted_utc": job["submitted_utc"],
        "recovered": bool(job.get("recovered")),
        "quota_seconds": job.get("quota_seconds"),
        "snapshot_sha256": snap_file["sha256"], "bootstrap": {"B": B, "seed": core.BOOT_SEED},
        "interpretable": interpretable,
        "answer": answer,
        "q1_per_question": q1,
        "predictions_in_use": {"source": "execution-time calibration" if ex["status"] == "changed" else "snapshot",
                               "execution_calibration": {k: v for k, v in ex.items() if k != "comps_exec"}},
        "headline": {"n_meas_point": h2["n_meas_point"], "n_pred": h2["n_pred"], "ci_at_n_meas_excludes_half": ci_excludes_half,
                     "n_meas_by_ci_low_gt_half": h2["n_meas_by_ci_low_gt_half"]},
        "table": table,
        "mix_controls": {str(n): {"P": float(m["P"]), "C": m["C"], "C_ci": [m["C_lo"], m["C_hi"]], "F": m["F"],
                                  "F_ci": [m["F_lo"], m["F_hi"]]} for n, m in res["mix"].items()},
        "criteria": crit, "roles": ROLES, "readings": reads,
        "criteria_secondary_snapshot_predictions": crit_secondary,
        "h1_drift_label": h1_lab, "h4_margins": h4_lab, "drift": sigma_info,
        "h2_reported": h2,
        "power_at_submission": {"status": pw_status["reasons"] if not pw_status["ok"] else "verified",
                                "checks": pw_status["checks"], "power": pw_status["power"],
                                "expected_outcome": None if pw_status["data"] is None else pw_status["data"]["expected_outcome"],
                                "sensitivity": None if pw_status["data"] is None else pw_status["data"]["sensitivity"],
                                "sigma_rel": None if pw_status["data"] is None else pw_status["data"]["sigma_rel"],
                                "label": None if pw_status["data"] is None else pw_status["data"]["label"],
                                "environment": pw_status.get("environment")},
        "comparison_with_earlier_runs": comparison,
        "tracking": tracking,
        "c1": calib,
        "dryrun_log": {"lines": log_lines, "unparsable_lines": log_bad, "stopping_rule": log_report, "anchor": log_status,
                       "first_logged_fetch": fetch_status, "job_time": job_time},
        "controls": {"K1": {"pass": k1_ok, "detail": k1}, "K2": k2, "K3": {"pass": k3_ok, "detail": k3}},
        "model_components": {str(n): comps[n] for n in core.GRID},
    }
    if write:
        with open(os.path.join(out_dir, "RESULTS_GHZ3.json"), "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
        with open(os.path.join(out_dir, "RESULTS_GHZ3.md"), "w", encoding="utf-8") as fh:
            fh.write(render_markdown(results))
        arrays = {"n": res["n"], "P_hat": res["P"], "C_hat": res["C"], "C_re_hat": res["C_re"], "F_hat": res["F_hat"],
                  "P_boot": res["P_boot"], "C_boot": res["C_boot"], "F_boot": res["F_boot"], "C_re_boot": res["C_re_boot"],
                  "P_pred": pred_use["P_pred"], "C_pred": pred_use["C_pred"], "F_pred": pred_use["F_pred"], "F_M": pred_use["F_M"],
                  "F_pred_snapshot": pred_snap["F_pred"],
                  "bootstrap_B": np.array(B), "bootstrap_seed": np.array(core.BOOT_SEED)}
        for n, m in res["mix"].items():
            arrays[f"mix{n}_C_boot"] = m["C_boot"]
            arrays[f"mix{n}_F_boot"] = m["F_boot"]
        np.savez(os.path.join(out_dir, "RESULTS_GHZ3_boot.npz"), **arrays)
    return results


def _f(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def render_markdown(r):
    h = r["headline"]
    ans = r["answer"]
    ex = r["predictions_in_use"]["execution_calibration"]
    L = [f"# GHZ run 3 on {r['backend']}: results", "",
         f"Job `{r['job_id']}`{' (recovered)' if r.get('recovered') else ''}, submitted {r['submitted_utc']}, snapshot sha256 "
         f"`{r['snapshot_sha256'][:16]}`, bootstrap B={r['bootstrap']['B']} seed={r['bootstrap']['seed']}, quota given "
         f"{r.get('quota_seconds')} s.", "",
         f"**Interpretable: {'yes' if r['interpretable'] else 'NO (yorumlanamaz: a control failed)'}**", "",
         "## Answer to Q1 and Q2 (assembled from the pre-written sentences, PREREG section 4)", ""]
    if ans["q1"] is None:
        L.append(f"**{ans['answer']}**")
    else:
        L += [f"- {ans['q1']}", f"- {ans['q2']}"] + ([f"- {ans['joint']}"] if ans["joint"] else [])
    L += ["", "Labels: " + (", ".join(f"{x['label']} ({x['applies_to']})" for x in ans["labels"]) or "none"), ""]
    q1 = r["q1_per_question"]
    L += [f"C-1 per question: Q1 model test = {q1.get('model_test')} (max |dF_pred(4), dF_pred(8)| on the snapshot's predictions = "
          f"{_f(q1.get('max_abs_dF_4_8_snapshot'), 4)}; on the predictions in use = {_f(q1.get('max_abs_dF_4_8_in_use'), 4)}; "
          f"threshold {q1['threshold']}).", "",
          f"Predictions in use: {r['predictions_in_use']['source']} (execution-time calibration: {ex['status']}, "
          f"{ex.get('reason') or 'verified'}; attempt used: {ex.get('attempt_used')} of {len(ex.get('attempt_files') or [])})", "",
          f"**Headline: n_meas = {h['n_meas_point']}** (largest n with F_hat > 0.5, the H2 definition; 0 = none); "
          f"n_pred = {h['n_pred']}. 95% CI at n_meas excludes 0.5: {h['ci_at_n_meas_excludes_half']} "
          f"(reported, not used by H2). Largest n with CI_low(F) > 0.5: {h['n_meas_by_ci_low_gt_half']}.", "",
          "| n | P (95% CI) | P_pred | C (95% CI) | C_pred | F (95% CI) | F_pred | R = F/F_pred | 97.5% of F_boot/F_pred (H4) | margin 1 - q | sigma_d,R | F_M (ref.) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in r["table"]:
        L.append(f"| {t['n']} | {t['P']:.4f} [{t['P_ci'][0]:.4f}, {t['P_ci'][1]:.4f}] | {t['P_pred']:.4f} | "
                 f"{t['C']:.4f} [{t['C_ci'][0]:.4f}, {t['C_ci'][1]:.4f}] | {t['C_pred']:.4f} | "
                 f"{t['F']:.4f} [{t['F_ci'][0]:.4f}, {t['F_ci'][1]:.4f}] | {t['F_pred']:.4f} | {_f(t['R'])} | "
                 f"{t['H4_ratio_q975']:.3f} | {t['H4_margin']:+.3f} | {_f(t['sigma_d_R'], 4)} | {t['F_M_reference']:.4f} |")
    L += ["", "Sensitivity I-1: C with Re (nominal phase) instead of |.|", "", "| n | C (abs) | C_re (95% CI) |", "|---|---|---|"]
    for t in r["table"]:
        L.append(f"| {t['n']} | {t['C']:.4f} | {t['C_re']:.4f} [{t['C_re_ci'][0]:.4f}, {t['C_re_ci'][1]:.4f}] |")
    L += ["", "## Criteria (H1-H3 imported unchanged from ghz2_study.py, H4 from ghz3_study_h4.py)", "",
          "| id | role | verdict | reading |", "|---|---|---|---|"]
    for cid, v in r["criteria"].items():
        reading = r["readings"].get(cid)
        L.append(f"| {cid} | {r['roles'][cid]} | {v} | {reading if reading else ''} |")
    if r["criteria_secondary_snapshot_predictions"]:
        L += ["", "Secondary (the snapshot's predictions; the primary are the execution-time ones): "
              + ", ".join(f"{k.split('_')[0]} {v}" for k, v in r["criteria_secondary_snapshot_predictions"].items())]
    L += ["", "### Within-drift labels and margins", ""]
    d = r["drift"]
    L.append("sigma_rel: " + (f"P {d['sigma_rel_P']:.4f}, C {d['sigma_rel_C']:.4f}" if "sigma_rel_P" in d else str(d)))
    if r["h1_drift_label"]:
        x = r["h1_drift_label"]
        L.append(f"- H1: decisive n = {x['n_decisive']}, |F_hat - F_pred| = {x['abs_deviation']:.4f}, distance to the 0.05 band = "
                 f"{x['distance_to_band']:.4f}, 2 sigma_d,F = {x['two_sigma_d_F']:.4f}: "
                 f"{'within drift' if x['within_drift'] else 'not within drift'}")
    if r["h4_margins"]:
        x = r["h4_margins"]
        L.append(f"- H4: {x['label'] or 'no within-drift label'}; n concerned (HOLDS: n with margin < 2 sigma_d,R; FAILS: n with q97.5 >= 1): "
                 f"{x['n_concerned'] if x['n_concerned'] else 'none'}")
        L += ["", "| n | q97.5 | margin 1 - q | 2 sigma_d,R |", "|---|---|---|---|"]
        for i, n in enumerate(core.GRID):
            L.append(f"| {n} | {x['q975'][i]:.4f} | {x['margin'][i]:+.4f} | {x['two_sigma_d_R'][i]:.4f} |")
    L += ["", "## Reported (not confirmatory): H2 and H3", ""]
    h2 = r["h2_reported"]
    ci_txt = "n/a" if h2["crossing_ci"] is None else "%.1f to %.1f" % (h2["crossing_ci"][0], h2["crossing_ci"][1])
    L += [f"- H2 (point values): n_meas = {h2['n_meas_point']}, n_pred = {h2['n_pred']}: {r['criteria']['H2_gme_reach_matches']}",
          f"- CI-based reach (largest n with CI low of F > 0.5): {h2['n_meas_by_ci_low_gt_half']}",
          f"- interpolated crossing of F = 0.5: measured {_f(h2['crossing_point'], 1)} (95% CI {ci_txt}; "
          f"{h2['crossing_replicates_without_crossing']} of {h2['replicates']} replicates without a crossing), "
          f"predicted {_f(h2['crossing_pred'], 1)}",
          f"- H3 (exploratory): {r['criteria']['H3_population_specific']}"]
    L += ["", "## Power at submission (run/power_run3.json; certs/power.json is a design-time stand-in and is not used)", ""]
    ps = r["power_at_submission"]
    if ps["power"] and ps["status"] == "verified":
        L.append(f"Power of H1 (truth F_pred - 0.03 at n = 4, 8): {ps['power']['H1']:.3f}; power of H4 (truth with run-2 ratios): "
                 f"{ps['power']['H4']:.3f}. Label: {ps['label']}. Recomputed from the snapshot's predictions: equal.")
        L += ["", "Expected outcome under run 2's ratios (reported, not power):", "", "| id | P(HOLDS) | P(FAILS) | P(UNDEFINED) |", "|---|---|---|---|"]
        for cid, v in ps["expected_outcome"].items():
            L.append(f"| {cid} | {_f(v['P_HOLDS'])} | {_f(v['P_FAILS'])} | {_f(v['P_UNDEFINED'])} |")
        L += ["", "Sensitivity (power of H1, power of H4):", ""]
        for m, v in ps["sensitivity"].items():
            L.append(f"- {m}: {v['power_H1']:.3f}, {v['power_H4']:.3f}")
    else:
        L.append(f"not verified: {ps['status']}. This is a K3 failure (yorumlanamaz).")
    cmp_ = r["comparison_with_earlier_runs"]
    L += ["", "## R(n) = F/F_pred under M2, runs 1, 2 and 3 side by side (descriptive; runs are not pooled, I-4)", "",
          f"- run 1: {cmp_['run1_source']}", f"- run 2: {cmp_['run2_source']}", "",
          "| n | R run 1 | R run 2 | R run 3 |", "|---|---|---|---|"]
    for row in cmp_["R_table"]:
        L.append(f"| {row['n']} | {_f(row['R_run1'])} | {_f(row['R_run2'])} | {_f(row['R_run3'])} |")
    L += ["", "## Tracking: measured change F_run3 - F_run2 against the predicted change (descriptive; CI: shot noise only)", ""]
    tr = r["tracking"]
    if tr["available"]:
        L += ["| n | measured change (95% CI, shot noise only) | sigma_d,F | predicted change | predicted inside CI |", "|---|---|---|---|---|"]
        for row in tr["rows"]:
            L.append(f"| {row['n']} | {row['measured_change']:+.4f} [{row['ci'][0]:+.4f}, {row['ci'][1]:+.4f}] | "
                     f"{_f(row['sigma_d_F'], 4)} | {row['predicted_change']:+.4f} | {row['predicted_inside_ci']} |")
    else:
        L.append(f"unavailable ({tr['error']})")
    L += ["", "## Small-n drift next to H1 (F and C at n = 4, 8)", "",
          "| n | F run 1 | F run 2 | F run 3 | F_pred run 3 | H1 deviation (run 3) | F run 2 - run 1 | F run 3 - run 2 | C run 2 - run 1 | C run 3 - run 2 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for n, d in cmp_["small_n_drift"].items():
        L.append(f"| {n} | {_f(d.get('F_run1'), 4)} | {_f(d.get('F_run2'), 4)} | {_f(d['F_run3'], 4)} | {_f(d['F_pred_run3'], 4)} | "
                 f"{d['H1_deviation_run3']:+.4f} | {_f(d.get('F_run2_minus_run1'), 4)} | {_f(d.get('F_run3_minus_run2'), 4)} | "
                 f"{_f(d.get('C_run2_minus_run1'), 4)} | {_f(d.get('C_run3_minus_run2'), 4)} |")
    c1 = r["c1"]
    L += ["", "## C-1 (v3) and the rule-14 check", ""]
    if c1.get("file_exists"):
        s = c1["saved"]
        L += [f"- at submission: C-1 satisfied = {s['c1_satisfied']}; device run 2 = {s['device_run2']}, run 3 = {s['device_run3']}; "
              f"M2 inputs changed: {s['n_inputs_changed']} of {len(ghz3_run.C1_FIELDS)}; max |dF_pred| = {s['max_abs_delta_F_pred']:.4f} "
              f"(threshold {s['threshold']}); Q1 model test = {s['q1_model_test']}",
              "- dF_pred (run 3 - run 2) per n: " + ", ".join(f"n={n}: {v['F_pred']['diff']:+.4f}" for n, v in s["delta_pred_run3_minus_run2"].items())]
    else:
        L.append("run/calibration_check.json is missing (K3 fails).")
    rc = c1["recomputed"]
    L.append(f"- recomputed in the analysis: {json.dumps(rc) if isinstance(rc, str) else 'C-1 satisfied = ' + str(rc['c1_satisfied'])}")
    L.append(f"- rule-14 check (F_pred + 0.05 < 1 at n = 4, 8): ok = {c1['rule14_recheck']['ok']}"
             + ("" if c1["rule14_recheck"]["ok"] else " -> label \"H1 one-sided\""))
    L += ["", "## Log (run/dryrun_log.jsonl, the whole log) and the stopping rule", ""]
    dl = r["dryrun_log"]
    sr = dl["stopping_rule"]
    L.append(f"{sr['n_lines']} lines: {sr['n_dry_run']} dry runs, {sr['n_attempts']} attempts ({sr['n_submit_refused']} refused, "
             f"{sr['n_submit_failed']} failed, {sr['n_submit_accepted']} accepted), {sr['n_not_attempts']} not-attempts; "
             f"unparsable lines: {dl['unparsable_lines']}.")
    L.append(f"Log prefix recorded in job.json unchanged: {dl['anchor']['ok']}"
             + ("" if dl["anchor"]["ok"] else f" ({dl['anchor']['reason']})")
             + f"; lines after the anchor: {dl['anchor']['lines_after_anchor']}; the accepted line's predictions hash matches the "
               f"snapshot's: {sr['accepted_line_predictions_hash_matches_snapshot']}.")
    L.append(f"Post-anchor lines dated not before the submission: {dl['anchor']['post_anchor_ok']}"
             + ("" if dl["anchor"]["post_anchor_ok"] else f" ({dl['anchor']['post_anchor_reason']})")
             + f"; first logged fetch: {dl['first_logged_fetch'].get('file')} (file and hash ok: {dl['first_logged_fetch']['ok']}; "
               f"{dl['first_logged_fetch']['n_logged_fetches']} logged); job created {dl['job_time']['created']}, started "
               f"{dl['job_time']['started']} (after the submission: {dl['job_time']['ok']}"
             + ("" if not dl["job_time"]["reason"] else f"; {dl['job_time']['reason']}") + ").")
    L.append("Deviations from the stopping rule: " + ("; ".join(sr["deviations_from_the_rule"]) or "none"))
    if sr["c1_pass_c2_fail"]:
        L.append("Logged lines with C-1 passed and C-2 failed: " + "; ".join(
            f"{x['mode']} at {x['snapshot_utc'] or x['utc']} (quota {x['quota_seconds']} s, estimate {_f(x['estimate_seconds'], 1)} s)"
            for x in sr["c1_pass_c2_fail"]))
    env = r["power_at_submission"].get("environment")
    if env:
        L.append("Environment (power file / now): " + ("identical" if not env["differs"] else "DIFFERS: " + ", ".join(
            f"{k}: {a} -> {b}" for k, (a, b) in env["differs"].items())))
    L += ["", "| utc | snapshot utc | mode | attempt | backend | exit | reason | D-7 | K2 | C-1 | C-2 | quota | predictions sha256 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for l in dl["lines"]:
        d7s = "" if not l.get("d7") else str(l["d7"]["ok"])
        k2s = "" if not l.get("k2") else str(l["k2"]["ok"])
        c1s = "" if not l.get("c1") else str(l["c1"]["satisfied"])
        c2s = "" if not l.get("c2") else str(l["c2"]["c2_satisfied"])
        ph = (l.get("predictions_sha256") or "")[:12]
        L.append(f"| {l.get('utc')} | {l.get('snapshot_utc')} | {l.get('mode')} | {l.get('attempt')} | {l.get('backend')} | "
                 f"{l.get('exit_code')} | {l.get('refusal_reason') or ''} | {d7s} | {k2s} | {c1s} | {c2s} | {l.get('quota_seconds')} | {ph} |")
    L += ["", "## Controls", "", "| MIX n | P | C_mix (95% CI) | F_mix (95% CI, reported only) | K1 (C_mix CI high <= 0.05) |",
          "|---|---|---|---|---|"]
    for n, m in r["mix_controls"].items():
        ok = r["controls"]["K1"]["detail"][n]["pass"]
        L.append(f"| {n} | {m['P']:.4f} | {m['C']:.4f} [{m['C_ci'][0]:.4f}, {m['C_ci'][1]:.4f}] | {m['F']:.4f} "
                 f"[{m['F_ci'][0]:.4f}, {m['F_ci'][1]:.4f}] | {'pass' if ok else 'FAIL'} |")
    k2 = r["controls"]["K2"]
    dc, bd = k2["design_check"], k2["binding"]
    L += ["", f"- K1 (coherence detector): {'pass' if r['controls']['K1']['pass'] else 'FAIL'}",
          f"- K2: {'pass' if k2['pass'] else 'FAIL'} = design check (certs/k2_sim.json, FakeKingston circuits; a missing or unreadable file "
          f"fails): {'pass' if dc['pass'] else 'FAIL'}"
          f"{'' if dc['readable'] else ' (unreadable: ' + str(dc.get('error')) + ')'}; binding (noiseless MPS on the submitted circuits): "
          f"{'pass' if bd['pass'] else 'FAIL'}{'' if not bd.get('error') else ' (' + bd['error'] + ')'}; bit-order control (reported, "
          f"uninformative, not part of K2): {json.dumps((dc.get('bit_order_control_reported_only') or {}).get('pass'))}",
          f"- K3 (integrity): {'pass' if r['controls']['K3']['pass'] else 'FAIL'} "
          f"{json.dumps(r['controls']['K3']['detail'])}", ""]
    return "\n".join(L)


def main(argv=None, root=HERE):
    try:
        ghz3_run.verify_run3_freeze(root)
    except core.FreezeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    results = run_analysis(root)
    print(render_markdown(results))
    print("wrote RESULTS_GHZ3.json, RESULTS_GHZ3.md and RESULTS_GHZ3_boot.npz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
