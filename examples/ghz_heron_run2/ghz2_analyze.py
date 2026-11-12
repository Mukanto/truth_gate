"""ghz2_analyze.py -- analysis of the GHZ run-2 data (PREREG.md sections 2 estimators, 3 model M2, 4 criteria, 5 controls, 6 I-1).

Adapted from run 1 (../ghz_heron/ghz_analyze.py).  Reads run/job.json, run/counts.json, the snapshot named in job.json,
run/circuits.qpy (the circuits that were submitted) and run/model.json.  Computes P, C, F with 95% bootstrap intervals,
M2's P_pred, C_pred, F_pred (recomputed from the snapshot-rebuilt Target and the saved circuits, cross-checked against
run/model.json), R = F_meas / F_pred, the reference arm F_M (run 1's model, reported only) and C with Re (sensitivity I-1);
applies H1-H3 (imported unchanged from ghz2_study.py) and K1, K3; writes RESULTS_GHZ2.json, RESULTS_GHZ2.md and
RESULTS_GHZ2_boot.npz (the bootstrap arrays, so the intervals can be recomputed).  K2 is a simulator pre-run (ghz2_d4.py);
it is read from certs/k2_sim.json if that file exists.

Usage:  python ghz2_analyze.py            (verifies FREEZE_GHZ2.json first)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from qiskit import qpy

import ghz2_core as core
import ghz2_study

HERE = os.path.dirname(os.path.abspath(__file__))

CRITERIA = {
    "H1_small_n_accuracy": ghz2_study.H1_small_n_accuracy,
    "H2_gme_reach_matches": ghz2_study.H2_gme_reach_matches,
    "H3_population_specific": ghz2_study.H3_population_specific,
}
K1_C_MAX = 0.05
MODEL_TOL = 1e-9


def verdict_word(v):
    return {True: "HOLDS", False: "FAILS", None: "UNDEFINED"}[v]


def apply_criteria(data):
    """Apply the imported H1-H3 to ``data`` in the schema of ghz2_study (F/P/C _pred, _hat, _boot; no n: the criteria index
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

    # ---- model M2 (and reference M) from the snapshot-rebuilt Target; must equal the saved model (K3)
    target = core.target_from_snapshot(snap)
    comps = core.model_all(entries, target)
    pred = {k: np.array([comps[n][k] for n in core.GRID]) for k in ("P_pred", "C_pred", "F_pred", "F_M")}
    saved = {k: np.array([model_saved["components"][str(n)][k] for n in core.GRID]) for k in pred}
    model_consistent = bool(all(np.max(np.abs(pred[k] - saved[k])) < MODEL_TOL for k in pred))
    k3["m2_recomputed_equals_saved_model"] = model_consistent
    k3_ok = all(k3.values())

    # ---- estimators + bootstrap
    res = core.analyze_counts(counts["circuits"], B=B)
    if [int(x) for x in res["n"]] != list(ghz2_study.GRID) or list(core.GRID) != list(ghz2_study.GRID):
        raise RuntimeError("analysed column order differs from ghz2_study.GRID; refusing to apply the criteria")
    data = {"F_pred": pred["F_pred"], "P_pred": pred["P_pred"], "C_pred": pred["C_pred"],
            "F_hat": res["F_hat"], "P_hat": res["P"], "C_hat": res["C"],
            "F_boot": res["F_boot"], "P_boot": res["P_boot"], "C_boot": res["C_boot"]}
    crit = apply_criteria(data)

    # ---- K1 and headline
    k1, k1_ok = k1_verdict(res["mix"])
    n_meas = _reach_point(res["F_hat"])
    n_pred = _reach_point(pred["F_pred"])
    ci_excludes_half = None
    if n_meas > 0:
        i = list(core.GRID).index(n_meas)
        ci_excludes_half = bool(res["F_lo"][i] > 0.5)
    n_meas_ci = int(max([n for n, l in zip(core.GRID, res["F_lo"]) if l > 0.5], default=0))
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
            "n": n,
            "P": float(res["P"][i]), "P_ci": [float(res["P_lo"][i]), float(res["P_hi"][i])], "P_pred": float(pred["P_pred"][i]),
            "C": float(res["C"][i]), "C_ci": [float(res["C_lo"][i]), float(res["C_hi"][i])], "C_pred": float(pred["C_pred"][i]),
            "F": float(res["F_hat"][i]), "F_ci": [float(res["F_lo"][i]), float(res["F_hi"][i])], "F_pred": float(pred["F_pred"][i]),
            "R": float(res["F_hat"][i] / pred["F_pred"][i]) if pred["F_pred"][i] > 0 else None,
            "F_M_reference": float(pred["F_M"][i]),
            "C_re": float(res["C_re"][i]), "C_re_ci": [float(res["C_re_lo"][i]), float(res["C_re_hi"][i])],
        })
    results = {
        "study": "GHZ run 2: corrected model M2 on new data (PREREG run-2 v1)",
        "backend": job["backend"], "job_id": job["job_id"], "submitted_utc": job["submitted_utc"],
        "snapshot_sha256": snap_file["sha256"], "bootstrap": {"B": B, "seed": core.BOOT_SEED},
        "interpretable": interpretable,
        "headline": {"n_meas_point": n_meas, "n_pred": n_pred, "ci_at_n_meas_excludes_half": ci_excludes_half,
                     "n_meas_by_ci_low_gt_half": n_meas_ci},
        "table": table,
        "mix_controls": {str(n): {"P": float(m["P"]), "C": m["C"], "C_ci": [m["C_lo"], m["C_hi"]], "F": m["F"],
                                  "F_ci": [m["F_lo"], m["F_hi"]]} for n, m in res["mix"].items()},
        "criteria": crit,
        "controls": {"K1": {"pass": k1_ok, "detail": k1}, "K2": k2 if k2 is not None else "not recorded (run ghz2_d4.py)",
                     "K3": {"pass": k3_ok, "detail": k3}},
        "model_components": {str(n): comps[n] for n in core.GRID},
    }
    if write:
        with open(os.path.join(out_dir, "RESULTS_GHZ2.json"), "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
        with open(os.path.join(out_dir, "RESULTS_GHZ2.md"), "w", encoding="utf-8") as fh:
            fh.write(render_markdown(results))
        arrays = {"n": res["n"], "P_hat": res["P"], "C_hat": res["C"], "C_re_hat": res["C_re"], "F_hat": res["F_hat"],
                  "P_boot": res["P_boot"], "C_boot": res["C_boot"], "F_boot": res["F_boot"], "C_re_boot": res["C_re_boot"],
                  "P_pred": pred["P_pred"], "C_pred": pred["C_pred"], "F_pred": pred["F_pred"], "F_M": pred["F_M"],
                  "bootstrap_B": np.array(B), "bootstrap_seed": np.array(core.BOOT_SEED)}
        for n, m in res["mix"].items():
            arrays[f"mix{n}_C_boot"] = m["C_boot"]
            arrays[f"mix{n}_F_boot"] = m["F_boot"]
        np.savez(os.path.join(out_dir, "RESULTS_GHZ2_boot.npz"), **arrays)
    return results


def render_markdown(r):
    h = r["headline"]
    L = [f"# GHZ run 2 on {r['backend']}: results", "",
         f"Job `{r['job_id']}`, submitted {r['submitted_utc']}, snapshot sha256 `{r['snapshot_sha256'][:16]}`, "
         f"bootstrap B={r['bootstrap']['B']} seed={r['bootstrap']['seed']}.", "",
         f"**Interpretable: {'yes' if r['interpretable'] else 'NO (yorumlanamaz: a control failed)'}**  ",
         f"**Headline: n_meas = {h['n_meas_point']}** (largest n with F_hat > 0.5, the H2 definition; 0 = none); "
         f"n_pred = {h['n_pred']}. 95% CI at n_meas excludes 0.5: {h['ci_at_n_meas_excludes_half']} "
         f"(reported, not used by H2). Largest n with CI_low(F) > 0.5: {h['n_meas_by_ci_low_gt_half']}.", "",
         "| n | P (95% CI) | P_pred | C (95% CI) | C_pred | F (95% CI) | F_pred | R = F/F_pred | F_M (ref.) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for t in r["table"]:
        R = "n/a" if t["R"] is None else f"{t['R']:.3f}"
        L.append(f"| {t['n']} | {t['P']:.4f} [{t['P_ci'][0]:.4f}, {t['P_ci'][1]:.4f}] | {t['P_pred']:.4f} | "
                 f"{t['C']:.4f} [{t['C_ci'][0]:.4f}, {t['C_ci'][1]:.4f}] | {t['C_pred']:.4f} | "
                 f"{t['F']:.4f} [{t['F_ci'][0]:.4f}, {t['F_ci'][1]:.4f}] | {t['F_pred']:.4f} | {R} | {t['F_M_reference']:.4f} |")
    L += ["", "Sensitivity I-1: C with Re (nominal phase) instead of |.|", "", "| n | C (abs) | C_re (95% CI) |", "|---|---|---|"]
    for t in r["table"]:
        L.append(f"| {t['n']} | {t['C']:.4f} | {t['C_re']:.4f} [{t['C_re_ci'][0]:.4f}, {t['C_re_ci'][1]:.4f}] |")
    L += ["", "## Criteria (imported unchanged from ghz2_study.py)", "", "| id | verdict |", "|---|---|"]
    L += [f"| {cid} | {v} |" for cid, v in r["criteria"].items()]
    L += ["", "## Controls", "", "| MIX n | P | C_mix (95% CI) | F_mix (95% CI, reported only) | K1 (C_mix CI high <= 0.05) |",
          "|---|---|---|---|---|"]
    for n, m in r["mix_controls"].items():
        ok = r["controls"]["K1"]["detail"][n]["pass"]
        L.append(f"| {n} | {m['P']:.4f} | {m['C']:.4f} [{m['C_ci'][0]:.4f}, {m['C_ci'][1]:.4f}] | {m['F']:.4f} "
                 f"[{m['F_ci'][0]:.4f}, {m['F_ci'][1]:.4f}] | {'pass' if ok else 'FAIL'} |")
    k2 = r["controls"]["K2"]
    k2s = k2 if isinstance(k2, str) else ("pass" if k2.get("pass") else "FAIL")
    L += ["", f"- K1 (coherence detector): {'pass' if r['controls']['K1']['pass'] else 'FAIL'}",
          f"- K2 (estimator fidelity + bit-order control, simulator pre-run): {k2s}",
          f"- K3 (integrity): {'pass' if r['controls']['K3']['pass'] else 'FAIL'} "
          f"{json.dumps(r['controls']['K3']['detail'])}", ""]
    return "\n".join(L)


def main(argv=None, root=HERE):
    try:
        core.verify_freeze(root)
    except core.FreezeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    results = run_analysis(root)
    print(render_markdown(results))
    print("wrote RESULTS_GHZ2.json, RESULTS_GHZ2.md and RESULTS_GHZ2_boot.npz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
