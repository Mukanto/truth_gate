"""Scratch analysis for the Phase C validity audit (B-2, B-3).

For every pair: draw the gate's own 200 minus samples (stream_rng(20261105, "world:minus", i), i = 0..199),
evaluate copies of the faulty and fixed criteria whose last line returns (statistic, holds) instead of holds,
check the holds counts against the certificates, and compute the structural statistics used for W2.
Writes scratch/stats_out.json.
"""
import json
import os
import re
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from truth_gate.sampling import stream_rng  # noqa: E402

SEED = 20261105
N = 200
CASES = ["B2-%02d" % i for i in range(1, 13)] + ["B3-%02d" % i for i in (1, 2, 3, 4, 5, 6, 8, 9, 11, 12)]

PAT = re.compile(r"^(\s*)return bool\((.+?) (>=) ([A-Z_]+|[0-9.]+)\)\s*$")


def load(case, twin, stat=True):
    path = os.path.join(HERE, "cases", case, twin + ".py")
    src = open(path, encoding="utf-8").read()
    if stat:
        lines = src.split("\n")
        done = 0
        for k, line in enumerate(lines):
            if "return bool(beta > 0.0 and t_sf(t, df) < 0.05)" in line:
                ind = line[: len(line) - len(line.lstrip())]
                lines[k] = ind + "return (float(t), bool(beta > 0.0 and t_sf(t, df) < 0.05))"
                done += 1
                continue
            m = PAT.match(line)
            if m:
                ind, expr, op, thr = m.groups()
                lines[k] = f"{ind}return ((_v := float({expr})), bool(_v {op} {thr}))"
                done += 1
        assert done == 1, (case, twin, done)
        src = "\n".join(lines)
    mod = types.ModuleType(f"m_{case.replace('-', '_')}_{twin}")
    mod.__file__ = path
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod


def cert_counts(case, twin):
    c = json.load(open(os.path.join(BASE, "certs", case, twin + ".json")))["body"]["components"][0]["counts"]
    return {k: v["holds"] for k, v in c.items()}


def lag1(x):
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    return float((x[1:] * x[:-1]).sum() / (x * x).sum())


def icc_oneway(a):
    """a: (groups, members). One-way ANOVA ICC(1)."""
    g, k = a.shape
    gm = a.mean(1)
    msb = k * ((gm - a.mean()) ** 2).sum() / (g - 1)
    msw = ((a - gm[:, None]) ** 2).sum() / (g * (k - 1))
    return float((msb - msw) / (msb + (k - 1) * msw))


def summ(v):
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], dtype=float)
    if v.size == 0:
        return None
    return {"mean": round(float(v.mean()), 4), "sd": round(float(v.std(ddof=1)), 4),
            "q05": round(float(np.quantile(v, 0.05)), 4), "q50": round(float(np.quantile(v, 0.5)), 4),
            "q95": round(float(np.quantile(v, 0.95)), 4), "n": int(v.size)}


def structural(case, mod, d):
    """Structural statistics on one minus sample d (dict). Returns dict of floats."""
    out = {}
    if case == "B2-01":
        out["onsets"] = float(d["onset"].sum())
    elif case in ("B2-02", "B2-03"):
        ykey = "outcome" if case == "B2-02" else "defective"
        y = d[ykey]
        out["minority_share"] = float(min(y.mean(), 1 - y.mean()))
        # replicate the faulty criterion's oversampling and folds (same rng seed and call order)
        seed = 20260202 if case == "B2-02" else 20260203
        rng = np.random.default_rng(seed)
        npos = int(y.sum()); nneg = y.size - npos
        pool = np.flatnonzero(y == (npos < nneg))
        pick = pool[rng.integers(0, pool.size, abs(nneg - npos))]
        orig = np.concatenate([np.arange(y.size), pick])
        yo = np.concatenate([y, y[pick]])
        f = np.empty(yo.size, dtype=int); off = 0
        for c in (False, True):
            idx = np.flatnonzero(yo == c)
            idx = idx[rng.permutation(idx.size)]
            f[idx] = (np.arange(idx.size) + off) % 5
            off += idx.size
        minority = (npos < nneg)
        hit = tot = 0
        for j in range(5):
            te = f == j
            tr_orig = set(orig[~te].tolist())
            sel = te & (yo == minority)
            tot += int(sel.sum())
            hit += sum(1 for o in orig[sel] if o in tr_orig)
        out["heldout_minority_with_copy_in_training"] = hit / tot
    elif case == "B2-04":
        out["lag1_rises"] = lag1(d["rises"].astype(float))
        out["lag1_indicators_mean"] = float(np.mean([lag1(d["indicators"][:, j]) for j in range(d["indicators"].shape[1])]))
    elif case == "B2-05":
        out["lag1_demand"] = lag1(d["demand"])
        out["lag1_drivers_mean"] = float(np.mean([lag1(d["drivers"][:, j]) for j in range(d["drivers"].shape[1])]))
    elif case == "B2-06":
        P = d["patch_features"]
        out["icc_features_mean"] = float(np.mean([icc_oneway(P[:, :, j]) for j in range(P.shape[2])]))
    elif case == "B2-07":
        M = d["measurements"]
        out["icc_measurements_mean"] = float(np.mean([icc_oneway(M[:, :, j]) for j in range(M.shape[2])]))
        out["icc_score"] = icc_oneway(d["score"])
    elif case == "B3-01":
        ratio = d["heart_weight"] / d["body_mass"]
        t = d["treated"]
        out["corr_ratio_treated"] = float(np.corrcoef(ratio, t.astype(float))[0, 1])
        out["mass_diff_treated_minus_untreated"] = float(d["body_mass"][t].mean() - d["body_mass"][~t].mean())
        out["corr_ratio_mass"] = float(np.corrcoef(ratio, d["body_mass"])[0, 1])
        b, a = np.polyfit(d["body_mass"], d["heart_weight"], 1)
        out["intercept_heart_on_mass"] = float(a)
    elif case == "B3-02":
        out["corr_creatinine_age"] = float(np.corrcoef(d["creatinine_excretion"], d["age"])[0, 1])
        b, a = np.polyfit(d["creatinine_excretion"], d["albumin_excretion"], 1)
        out["intercept_albumin_on_creatinine"] = float(a)
        out["albumin_mean"] = float(d["albumin_excretion"].mean())
    elif case == "B3-03":
        ratio = d["lv_mass"] / d["body_surface_area"]
        out["corr_ratio_bsa"] = float(np.corrcoef(ratio, d["body_surface_area"])[0, 1])
        out["r2_sbp_on_bsa"] = float(np.corrcoef(d["systolic_bp"], d["body_surface_area"])[0, 1] ** 2)
        b, a = np.polyfit(d["body_surface_area"], d["lv_mass"], 1)
        out["intercept_lvm_on_bsa"] = float(a)
    elif case == "B3-04":
        x = d["kidney_weight"] / d["body_mass"]; y = d["liver_weight"] / d["body_mass"]
        out["corr_ratios"] = float(np.corrcoef(x, y)[0, 1])
        out["intercept_liver_on_body"] = float(np.polyfit(d["body_mass"], d["liver_weight"], 1)[1])
        out["intercept_kidney_on_body"] = float(np.polyfit(d["body_mass"], d["kidney_weight"], 1)[1])
    elif case == "B3-05":
        out["intercept_femur_on_humerus"] = float(np.polyfit(d["humerus_length"], d["femur_length"], 1)[1])
        out["intercept_tibia_on_humerus"] = float(np.polyfit(d["humerus_length"], d["tibia_length"], 1)[1])
        out["corr_femur_tibia_raw"] = float(np.corrcoef(d["femur_length"], d["tibia_length"])[0, 1])
    elif case == "B3-06":
        est = d["estimates"]; tv = d["true_value"]
        out["mean_offset_at_T0"] = float(np.mean([np.polyfit(tv, est[:, j], 1)[1] for j in range(est.shape[1])]))
    elif case == "B3-08":
        fall = d["sbp_baseline_first"] - d["sbp_week12"]
        out["corr_fall_first"] = float(np.corrcoef(fall, d["sbp_baseline_first"])[0, 1])
        out["corr_fall_second"] = float(np.corrcoef(fall, d["sbp_baseline_second"])[0, 1])
    elif case == "B3-09":
        co, ca, cv = d["cardiac_output"], d["arterial_o2_content"], d["venous_o2_content"]
        out["corr_delivery_calcuptake"] = float(np.corrcoef(co * ca, co * (ca - cv))[0, 1])
        out["corr_delivery_expired"] = float(np.corrcoef(co * ca, d["o2_uptake_expired"])[0, 1])
    elif case == "B3-11":
        ga, gb, gc = d["gene_a_expression"], d["gene_b_expression"], d["gene_c_expression"]
        out["corr_ratios"] = float(np.corrcoef(ga / gc, gb / gc)[0, 1])
        out["intercept_a_on_c"] = float(np.polyfit(gc, ga, 1)[1])
        out["intercept_b_on_c"] = float(np.polyfit(gc, gb, 1)[1])
    elif case == "B3-12":
        adm, pop, tm = d["admissions"], d["population"], d["time_years"]
        X = np.column_stack([np.ones(adm.size), pop])
        coef = np.linalg.lstsq(X, adm, rcond=None)[0]
        out["intercept_adm_on_pop"] = float(coef[0])
        X2 = np.column_stack([np.ones(adm.size), tm, pop])
        res = adm - X2 @ np.linalg.lstsq(X2, adm, rcond=None)[0]
        out["lag1_fixed_residuals"] = lag1(res)
        rate = adm / pop
        X3 = np.column_stack([np.ones(adm.size), tm])
        res3 = rate - X3 @ np.linalg.lstsq(X3, rate, rcond=None)[0]
        out["lag1_faulty_residuals"] = lag1(res3)
    return out


def main(only=None):
    results = {}
    for case in CASES:
        if only and case not in only:
            continue
        t0 = time.time()
        fau = load(case, "faulty")
        fix = load(case, "fixed")
        minus = fix.STUDY.worlds["minus"].generate
        rec = {"faulty_stat": [], "fixed_stat": [], "faulty_holds": 0, "fixed_holds": 0, "struct": {}}
        struct_vals = {}
        for i in range(N):
            d = minus(stream_rng(SEED, "world:minus", i))
            for twin, mod in (("faulty", fau), ("fixed", fix)):
                r = mod.criterion({k: np.array(v, copy=True) for k, v in d.items()})
                if r is None:
                    rec[twin + "_stat"].append(None)
                else:
                    rec[twin + "_stat"].append(r[0])
                    rec[twin + "_holds"] += int(r[1])
            for k, v in structural(case, fix, d).items():
                struct_vals.setdefault(k, []).append(v)
        rec["struct"] = {k: summ(v) for k, v in struct_vals.items()}
        rec["faulty_stat"] = summ(rec["faulty_stat"])
        rec["fixed_stat"] = summ(rec["fixed_stat"])
        rec["cert_minus_faulty"] = cert_counts(case, "faulty")["world:minus"]
        rec["cert_minus_fixed"] = cert_counts(case, "fixed")["world:minus"]
        rec["seconds"] = round(time.time() - t0, 1)
        results[case] = rec
        print(case, json.dumps(rec), flush=True)
    out = os.path.join(HERE, "stats_out.json" if not only else "stats_out_partial.json")
    json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
