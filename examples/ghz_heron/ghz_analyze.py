"""ghz_analyze.py -- analysis of the GHZ-on-Heron run (PREREG.md sections 4 estimators, 5 model, 6 criteria, 7 controls).

Reads run/job.json, run/counts.json, the snapshot named in job.json, run/circuits.qpy (the circuits that were submitted)
and run/model.json.  Computes P, C, F with 95% bootstrap intervals, F_pred (model M recomputed from the snapshot-rebuilt
Target and the saved circuits, cross-checked against run/model.json) and R = F_meas / F_pred; applies G1-G3 (imported
unchanged from ghz_study.py) and K1, K3; writes RESULTS_GHZ.json and RESULTS_GHZ.md.  K2 is a simulator pre-run
(ghz_d4.py); it is read from certs/k2_sim.json if that file exists.

Usage:  python ghz_analyze.py            (verifies FREEZE_GHZ.json first)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from qiskit import qpy

import ghz_core as core
import ghz_study

HERE = os.path.dirname(os.path.abspath(__file__))

CRITERIA = {
    "G1_small_n_accuracy": ghz_study.G1_small_n_accuracy,
    "G2_excess_decay_grows": ghz_study.G2_excess_decay_grows,
    "G3_gme_reach_matches": ghz_study.G3_gme_reach_matches,
}
K1_C_MAX = 0.05
MODEL_TOL = 1e-9


def verdict_word(v):
    return {True: "HOLDS", False: "FAILS", None: "UNDEFINED"}[v]


def apply_criteria(f_pred, f_hat, f_boot):
    """Apply the imported G1-G3 to the data in the schema of ghz_study (no n: the criteria index GRID by position).
    Returns {id: "HOLDS"|"FAILS"|"UNDEFINED"}."""
    data = {"F_pred": np.asarray(f_pred, dtype=float), "F_hat": np.asarray(f_hat, dtype=float),
            "F_boot": np.asarray(f_boot, dtype=float)}
    out = {}
    for cid, fn in CRITERIA.items():
        try:
            out[cid] = verdict_word(fn(data))
        except Exception as exc:  # noqa: BLE001
            out[cid] = f"UNDEFINED ({type(exc).__name__})"
    return out


def k1_verdict(mix):
    """K1 (PREREG v2): for MIX_8 and MIX_32, the 97.5th percentile of the bootstrap replicates of C_mix is <= 0.05.
    F_mix is reported but is not part of the rule."""
    out = {}
    for n, m in mix.items():
        c_hi = float(np.percentile(m["C_boot"], 97.5))
        out[str(n)] = {"C_mix": float(m["C"]), "C_mix_ci_high": c_hi, "F_mix": float(m["F"]),
                       "F_mix_ci": [float(m["F_lo"]), float(m["F_hi"])], "pass": bool(c_hi <= K1_C_MAX)}
    return out, all(v["pass"] for v in out.values())


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


def run_analysis(root=HERE, run_dir=None, out_dir=None, B=core.BOOT_B, write=True):
    run_dir = run_dir or os.path.join(root, "run")
    out_dir = out_dir or root
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
    k3_ok = all(k3.values())

    # ---- model M from the snapshot-rebuilt Target
    target = core.target_from_snapshot(snap)
    comps = core.model_all(entries, target)
    f_pred = np.array([comps[n]["F_pred"] for n in core.GRID])
    saved = np.array([model_saved["components"][str(n)]["F_pred"] for n in core.GRID])
    model_consistent = bool(np.max(np.abs(f_pred - saved)) < MODEL_TOL)

    # ---- estimators + bootstrap
    res = core.analyze_counts(counts["circuits"], B=B)
    f_hat, f_boot = res["F_hat"], res["F_boot"]
    if [int(x) for x in res["n"]] != list(ghz_study.GRID) or list(core.GRID) != list(ghz_study.GRID):
        raise RuntimeError("analysed column order differs from ghz_study.GRID; refusing to apply the criteria")
    crit = apply_criteria(f_pred, f_hat, f_boot)

    # ---- K1 and headline
    k1, k1_ok = k1_verdict(res["mix"])
    lo = res["F_lo"]
    n_meas = int(max([n for n, l in zip(core.GRID, lo) if l > 0.5], default=0))
    n_pred = int(max([n for n, f in zip(core.GRID, f_pred) if f > 0.5], default=0))
    k2_path = os.path.join(root, "certs", "k2_sim.json")
    k2 = None
    if os.path.isfile(k2_path):
        with open(k2_path, "r", encoding="utf-8") as fh:
            k2 = json.load(fh)
    k2_ok = None if k2 is None else bool(k2.get("pass"))
    interpretable = bool(k1_ok and k3_ok and k2_ok is not False)

    table = []
    for i, n in enumerate(core.GRID):
        table.append({
            "n": n, "F_meas": float(f_hat[i]), "F_ci_low": float(res["F_lo"][i]), "F_ci_high": float(res["F_hi"][i]),
            "F_pred": float(f_pred[i]), "R": float(f_hat[i] / f_pred[i]) if f_pred[i] > 0 else None,
            "P": float(res["P"][i]), "C": float(res["C"][i]),
        })
    results = {
        "study": "GHZ fidelity vs device calibration model (PREREG v1)",
        "backend": job["backend"], "job_id": job["job_id"], "submitted_utc": job["submitted_utc"],
        "snapshot_sha256": snap_file["sha256"], "bootstrap": {"B": B, "seed": core.SEED},
        "interpretable": interpretable,
        "headline": {"n_meas": n_meas, "n_pred": n_pred},
        "table": table,
        "mix_controls": {str(n): {"P": float(m["P"]), "C": m["C"], "C_ci": [m["C_lo"], m["C_hi"]], "F": m["F"],
                                  "F_ci": [m["F_lo"], m["F_hi"]]} for n, m in res["mix"].items()},
        "criteria": crit,
        "controls": {"K1": {"pass": k1_ok, "detail": k1}, "K2": k2 if k2 is not None else "not recorded (run ghz_d4.py)",
                     "K3": {"pass": k3_ok, "detail": k3}},
        "model_matches_saved_model_json": model_consistent,
        "model_components": {str(n): comps[n] for n in core.GRID},
    }
    if write:
        with open(os.path.join(out_dir, "RESULTS_GHZ.json"), "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
        with open(os.path.join(out_dir, "RESULTS_GHZ.md"), "w", encoding="utf-8") as fh:
            fh.write(render_markdown(results))
    return results


def render_markdown(r):
    L = [f"# GHZ fidelity on {r['backend']}: results", "",
         f"Job `{r['job_id']}`, submitted {r['submitted_utc']}, snapshot sha256 `{r['snapshot_sha256'][:16]}`, "
         f"bootstrap B={r['bootstrap']['B']} seed={r['bootstrap']['seed']}.", "",
         f"**Interpretable: {'yes' if r['interpretable'] else 'NO (yorumlanamaz: a control failed)'}**  ",
         f"**Headline: n_meas = {r['headline']['n_meas']}** (largest n with CI_low(F) > 0.5; 0 = none); "
         f"n_pred = {r['headline']['n_pred']}.", "",
         "| n | F_meas | 95% CI | F_pred | R = F_meas/F_pred | P | C |", "|---|---|---|---|---|---|---|"]
    for t in r["table"]:
        R = "n/a" if t["R"] is None else f"{t['R']:.3f}"
        L.append(f"| {t['n']} | {t['F_meas']:.4f} | [{t['F_ci_low']:.4f}, {t['F_ci_high']:.4f}] | {t['F_pred']:.4f} | "
                 f"{R} | {t['P']:.4f} | {t['C']:.4f} |")
    L += ["", "## Criteria (imported unchanged from ghz_study.py)", "", "| id | verdict |", "|---|---|"]
    L += [f"| {cid} | {v} |" for cid, v in r["criteria"].items()]
    L += ["", "## Controls", "", "| MIX n | P | C_mix (95% CI) | F_mix (95% CI, reported only) | K1 (C_mix CI high <= 0.05) |", "|---|---|---|---|---|"]
    for n, m in r["mix_controls"].items():
        ok = r["controls"]["K1"]["detail"][n]["pass"]
        L.append(f"| {n} | {m['P']:.4f} | {m['C']:.4f} [{m['C_ci'][0]:.4f}, {m['C_ci'][1]:.4f}] | {m['F']:.4f} "
                 f"[{m['F_ci'][0]:.4f}, {m['F_ci'][1]:.4f}] | {'pass' if ok else 'FAIL'} |")
    k2 = r["controls"]["K2"]
    k2s = k2 if isinstance(k2, str) else ("pass" if k2.get("pass") else "FAIL")
    L += ["", f"- K1 (coherence detector): {'pass' if r['controls']['K1']['pass'] else 'FAIL'}",
          f"- K2 (estimator fidelity, simulator pre-run): {k2s}",
          f"- K3 (integrity): {'pass' if r['controls']['K3']['pass'] else 'FAIL'} "
          f"{json.dumps(r['controls']['K3']['detail'])}",
          f"- model recomputed from the snapshot equals run/model.json: {r['model_matches_saved_model_json']}", ""]
    return "\n".join(L)


def main(argv=None, root=HERE):
    try:
        core.verify_freeze(root)
    except core.FreezeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    results = run_analysis(root)
    print(render_markdown(results))
    print("wrote RESULTS_GHZ.json and RESULTS_GHZ.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
