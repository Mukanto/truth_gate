"""W2 statistics: one structural statistic per case, on 200 samples of the declared worlds.
World sample i uses np.random.default_rng(SEED + i): minus SEED=0, plus SEED=10000 (same seeds as stats.py)."""
import sys, os, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from load import load

N = 200


def draw(m, w):
    s = 0 if w == "minus" else 10000
    return [getattr(m, w)(np.random.default_rng(s + i)) for i in range(N)]


def lag1(v):
    v = v - v.mean()
    return float(np.sum(v[1:] * v[:-1]) / np.sum(v * v))


def icc_oneway(x):
    # x: (groups, members) -> ANOVA ICC(1)
    g, k = x.shape
    gm = x.mean(axis=1)
    msb = k * np.sum((gm - x.mean()) ** 2) / (g - 1)
    msw = np.sum((x - gm[:, None]) ** 2) / (g * (k - 1))
    return float((msb - msw) / (msb + (k - 1) * msw))


def rank(x):
    u, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    return (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]


def summ(a):
    a = np.asarray(a, dtype=float)
    return {"mean": round(float(a.mean()), 4), "sd": round(float(a.std()), 4),
            "q05": round(float(np.quantile(a, 0.05)), 4), "q95": round(float(np.quantile(a, 0.95)), 4)}


def z(v):
    return (v - v.mean()) / v.std()


out = {}
rngp = np.random.default_rng(777)

# B2-03 / B2-04: within-block gene correlation (co-expression) in minus
for case in ("B2-03", "B2-04"):
    m = load(case, "faulty")
    ds = draw(m, "minus")
    wb = []
    blocks = np.repeat(np.arange(6), 10)
    same = (blocks[:, None] == blocks[None, :]) & ~np.eye(60, dtype=bool)
    for d in ds:
        c = np.corrcoef(d["expr"].T)
        wb.append(c[same].mean())
    out[case] = {"within_block_gene_corr_minus": summ(wb), "genes": 60, "rows": ds[0]["expr"].shape[0]}

# B2-05: gap between class-conditional fill values (onset minus non-onset mean of observed values), per indicator
m = load("B2-05", "faulty")
for w in ("minus", "plus"):
    gi, ga, m1, m0 = [], [], [], []
    for d in draw(m, w):
        x, o, y = d["x"], d["observed"], d["onset"]
        c1 = (x[y] * o[y]).sum(0) / o[y].sum(0)
        c0 = (x[~y] * o[~y]).sum(0) / o[~y].sum(0)
        sd = np.array([x[:, j][o[:, j]].std() for j in range(x.shape[1])])
        g = (c1 - c0) / sd
        gi.append(np.abs(g[:6]).mean())
        ga.append(np.abs(g).mean())
        m1.append(1 - o[y].mean())
        m0.append(1 - o[~y].mean())
    out.setdefault("B2-05", {})[w] = {"abs_gap_sd_units_informative6": summ(gi), "abs_gap_sd_units_all12": summ(ga),
                                      "missing_frac_onset": summ(m1), "missing_frac_nononset": summ(m0)}

# B2-06: faulty criterion's sensitivity on synthetic and on real positives, and specificity, in minus and plus
src = open(os.path.join(HERE, "cases", "B2-06", "faulty.py"), encoding="utf-8").read()
old = "    return bool(balanced(pred, ya) >= thr)"
assert old in src
new = ("    nreal = y.size\n"
       "    return (float(np.mean(pred[nreal:])), float(np.mean(pred[:nreal][y])), "
       "float(np.mean(~pred[:nreal][~y])), int(ya.size - nreal))")
src = src.replace(old, new)
p = os.path.join(HERE, "patched", "B2-06_faulty_parts.py")
open(p, "w", encoding="utf-8").write(src)
spec = importlib.util.spec_from_file_location("b206parts", p)
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)
m = load("B2-06", "faulty")
for w in ("minus", "plus"):
    r = np.array([mm.criterion(d) for d in draw(m, w)], dtype=float)
    out.setdefault("B2-06", {})[w] = {"sens_synthetic": summ(r[:, 0]), "sens_real_pos": summ(r[:, 1]),
                                      "spec_real_neg": summ(r[:, 2]), "n_synthetic": summ(r[:, 3])}

# B2-07: share of rows that have an exact copy elsewhere in the sample (minus)
m = load("B2-07", "faulty")
sh = []
for d in draw(m, "minus"):
    _, inv, cnt = np.unique(d["records"], axis=0, return_inverse=True, return_counts=True)
    sh.append(np.mean(cnt[np.asarray(inv).reshape(-1)] > 1))
out["B2-07"] = {"rows_with_exact_copy_minus": summ(sh), "repeated_rows": 50, "rows": 200}

# B2-09: lag-1 autocorrelation of indicators and onsets; in-sample |corr(indicator, onset)| vs a row-permuted baseline
m = load("B2-09", "faulty")
ax, ao, cr, crp = [], [], [], []
for d in draw(m, "minus"):
    x, y = d["x"], d["onset"].astype(float)
    ax.append(np.mean([lag1(x[:, j]) for j in range(x.shape[1])]))
    ao.append(lag1(y))
    cr.append(np.mean(np.abs([np.corrcoef(x[:, j], y)[0, 1] for j in range(x.shape[1])])))
    yp = y[rngp.permutation(y.size)]
    crp.append(np.mean(np.abs([np.corrcoef(x[:, j], yp)[0, 1] for j in range(x.shape[1])])))
out["B2-09"] = {"lag1_indicators_minus": summ(ax), "lag1_onset_minus": summ(ao),
                "mean_abs_corr_indicator_onset_minus": summ(cr), "same_after_permuting_onset_rows": summ(crp)}

# B2-10: lag-1 autocorrelation and in-sample OLS R^2 of next-week admissions on the 6 indicators (minus)
m = load("B2-10", "faulty")
ay, ai, r2, r2p = [], [], [], []
for d in draw(m, "minus"):
    x, y = d["indicators"], d["admissions_next"]
    ay.append(lag1(y))
    ai.append(np.mean([lag1(x[:, j]) for j in range(x.shape[1])]))
    a = np.column_stack([np.ones(y.size), x])
    b = np.linalg.lstsq(a, y, rcond=None)[0]
    r2.append(1 - np.sum((y - a @ b) ** 2) / np.sum((y - y.mean()) ** 2))
    yp = y[rngp.permutation(y.size)]
    b = np.linalg.lstsq(a, yp, rcond=None)[0]
    r2p.append(1 - np.sum((yp - a @ b) ** 2) / np.sum((yp - yp.mean()) ** 2))
out["B2-10"] = {"lag1_target_minus": summ(ay), "lag1_indicators_minus": summ(ai), "insample_R2_minus": summ(r2),
                "insample_R2_after_permuting_weeks": summ(r2p)}

# B2-11: ICC of patch features within patient (minus)
m = load("B2-11", "faulty")
ic = []
for d in draw(m, "minus"):
    pt = d["patches"]
    ic.append(np.mean([icc_oneway(pt[:, :, f]) for f in range(pt.shape[2])]))
out["B2-11"] = {"icc_patch_features_minus": summ(ic)}

# B2-12: ICC of stay and of characteristics within hospital (minus)
m = load("B2-12", "faulty")
is_, ix = [], []
for d in draw(m, "minus"):
    is_.append(icc_oneway(d["stay"]))
    ix.append(np.mean([icc_oneway(d["x"][:, :, f]) for f in range(d["x"].shape[2])]))
out["B2-12"] = {"icc_stay_minus": summ(is_), "icc_characteristics_minus": summ(ix)}

# B3-06: per-capita values vs population (minus)
m = load("B3-06", "faulty")
c1, c2 = [], []
for d in draw(m, "minus"):
    lp = np.log(d["population"])
    c1.append(np.corrcoef(lp, np.log(d["co2_emissions_total"] / d["population"]))[0, 1])
    c2.append(np.corrcoef(lp, np.log(d["gdp_total"] / d["population"]))[0, 1])
out["B3-06"] = {"corr_logpop_logpcCO2_minus": summ(c1), "corr_logpop_logpcGDP_minus": summ(c2)}

# B3-09 / B3-12: elasticity of the count on its denominator (1 = proportional); corr of predictor with denominator and ratio
for case, num, den, pred in (("B3-09", "infections", "admissions", "beds"), ("B3-12", "leavers", "headcount", "payroll")):
    m = load(case, "faulty")
    el, cpd, crr = [], [], []
    for d in draw(m, "minus"):
        k = d[num] > 0
        el.append(np.polyfit(np.log(d[den][k]), np.log(d[num][k]), 1)[0])
        cpd.append(np.corrcoef(d[pred], d[den])[0, 1])
        crr.append(np.corrcoef(d[pred], d[num] / d[den])[0, 1])
    out[case] = {"elasticity_count_on_denominator_minus": summ(el), "corr_predictor_denominator_minus": summ(cpd),
                 "corr_predictor_ratio_minus": summ(crr)}

# B3-10: correlation of the ratio with its denominator (minus)
m = load("B3-10", "faulty")
cr = []
for d in draw(m, "minus"):
    cr.append(np.corrcoef(d["heart_weight"] / d["body_weight"], d["body_weight"])[0, 1])
out["B3-10"] = {"corr_ratio_bodyweight_minus": summ(cr)}

# B3-11: scale effect and occupants-area link in minus
m = load("B3-11", "faulty")
ce, co = [], []
for d in draw(m, "minus"):
    eui = d["energy_use"] / d["floor_area"]
    ce.append(np.corrcoef(rank(eui), rank(d["floor_area"]))[0, 1])
    co.append(np.corrcoef(rank(d["occupants"]), rank(d["floor_area"]))[0, 1])
out["B3-11"] = {"spearman_eui_area_minus": summ(ce), "spearman_occupants_area_minus": summ(co)}

# B3-07: log-scale variant of the fixed (coefficient of log fertilizer_total with log area covariate), hold rate at 0.3
m = load("B3-07", "faulty")
for w in ("minus", "plus"):
    cf = []
    for d in draw(m, w):
        X = np.column_stack([np.ones(d["farm_area"].size), z(np.log(d["fertilizer_total"])), z(np.log(d["farm_area"]))])
        cf.append(np.linalg.lstsq(X, z(np.log(d["yield_total"])), rcond=None)[0][1])
    cf = np.array(cf)
    out.setdefault("B3-07", {})["logscale_fixed_" + w] = {**summ(cf), "holds_ge_0.3": int(np.sum(cf >= 0.3))}

json.dump(out, open(os.path.join(HERE, "w2_out.json"), "w"), indent=1)
for k, v in out.items():
    print(k, json.dumps(v))
