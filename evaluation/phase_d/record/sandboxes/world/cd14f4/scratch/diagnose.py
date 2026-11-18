"""Oracle diagnostics on the generative truth (population quantities only; no criterion-like analysis)."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pkg"))
import numpy as np  # noqa: E402


def load(sid):
    path = ROOT / "skeletons" / f"{sid}.py"
    spec = importlib.util.spec_from_file_location(sid.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def draws(mod, arg, n=200):
    for i in range(n):
        yield mod._draw(np.random.default_rng([11, i]), arg)


R = 200
m = load("D-007")
for arg in (True, False):
    c_log, r2_raw, own = [], [], []
    rng_lo, rng_hi = [], []
    for d, t in draws(m, arg, R):
        s = d["survival_months"]
        c_log.append(corr(np.log(s), t["prognostic"]))
        own.append(corr(np.log(s), t["scores"][:, 0]))
        r2_raw.append(corr(s, np.exp(m.B_PROGNOSTIC * t["prognostic"])) ** 2)
        rng_lo.append(d["expression"].min()); rng_hi.append(d["expression"].max())
    print(f"D-007 informative={arg}: corr(log S, used score)={np.mean(c_log):.3f} "
          f"corr(log S, own expression programme)={np.mean(own):.3f} oracle R2 months={np.mean(r2_raw):.3f} "
          f"expr range {np.min(rng_lo):.1f}..{np.max(rng_hi):.1f} median months~{np.exp(m.LOG_MEDIAN_MONTHS):.1f}")

m = load("D-008")
for arg in (m.SLOPE_MEAN, 0.0):
    sl, lam, cv_min, o2er_max, cv_mean = [], [], [], [], []
    for d, t in draws(m, arg, R):
        sl.append(t["slope"].mean())
        do2_meas = 10 * d["cardiac_output"] * d["arterial_o2_content"]
        dt = t["do2_true"] - t["do2_true"].mean(axis=1, keepdims=True)
        dm = do2_meas - do2_meas.mean(axis=1, keepdims=True)
        lam.append(np.sum(dt * dm) / np.sum(dm * dm))   # attenuation factor (truth vs measurement of DO2)
        cv_min.append(d["venous_o2_content"].min())
        cv_mean.append(d["venous_o2_content"].mean())
        o2er_max.append((t["vo2_true"] / t["do2_true"]).max())
    print(f"D-008 slope_mean={arg}: mean true slope={np.mean(sl):.3f} attenuation={np.mean(lam):.3f} "
          f"-> expected measured slope ~{np.mean(sl) * np.mean(lam):.3f}; CvO2 min={np.min(cv_min):.2f} "
          f"mean={np.mean(cv_mean):.2f}; max O2ER={np.max(o2er_max):.2f}")
d, t = m._draw(np.random.default_rng(3), m.SLOPE_MEAN)
print("  D-008 example CO", d["cardiac_output"].min().round(2), d["cardiac_output"].max().round(2),
      "CaO2", d["arterial_o2_content"].min().round(1), d["arterial_o2_content"].max().round(1),
      "VO2", d["vo2_expired_gas"].min().round(0), d["vo2_expired_gas"].max().round(0))

m = load("D-010")
for arg in (True, False):
    vs, cy, cs, empty, maxc = [], [], [], [], []
    for d, t in draws(m, arg, R):
        vs.append(np.var(t["signal"]))
        cy.append(corr(d["y"], t["used"]))
        cs.append(corr(d["y"], t["signal"]))
        cnt = d["category"].sum(axis=0)
        empty.append(np.sum(cnt == 0)); maxc.append(cnt.max())
    print(f"D-010 informative={arg}: var(signal)={np.mean(vs):.3f} corr(y, own signal)={np.mean(cs):.3f} "
          f"(oracle R2 {np.mean(cs) ** 2:.3f}); empty districts {np.mean(empty):.1f}, max size {np.mean(maxc):.0f}")
d, t = m._draw(np.random.default_rng(3), True)
print("  D-010 covariate means", d["covariates"].mean(axis=0).round(1), "sds", d["covariates"].std(axis=0).round(1),
      "y mean/sd", d["y"].mean().round(1), d["y"].std().round(1))

m = load("D-011")
for arg in (True, False):
    dm0, dm1, lo, hi = [], [], [], []
    for d, t in draws(m, arg, R):
        a = d["myeloid"]
        s = t["scores"]
        dm0.append(s[a, 0].mean() - s[~a, 0].mean())
        dm1.append(s[a, 1].mean() - s[~a, 1].mean())
        lo.append(d["expression"].min()); hi.append(d["expression"].max())
    print(f"D-011 informative={arg}: lineage programme shift by recorded label {np.mean(dm0):.2f}, {np.mean(dm1):.2f} "
          f"(within-type SD 1); expression range {np.min(lo):.1f}..{np.max(hi):.0f}")
from statistics import NormalDist  # noqa: E402
print(f"  D-011 oracle AUC (two lineage programmes) = {NormalDist().cdf(m.DELTA * np.sqrt(2) / np.sqrt(2)):.3f}")

m = load("D-012")
for arg in (1.0, 0.0):
    pf, po = [], []
    for d, t in draws(m, arg, 2000):
        e = d["exclosure"]
        pf.append(t["prob"][e].mean()); po.append(t["prob"][~e].mean())
    print(f"D-012 effect={arg}: true mean occupancy probability fenced={np.mean(pf):.3f} open={np.mean(po):.3f} "
          f"diff={np.mean(pf) - np.mean(po):.3f}; SD of plot-mean probability within group "
          f"{np.std(np.array(po)) * np.sqrt(5):.3f} (approx)")

for sid, key in (("D-022", "f"), ("D-027", "signal")):
    m = load(sid)
    for arg in (True, False):
        cu, co = [], []
        for d, t in draws(m, arg, R):
            cu.append(corr(d["y"], t["used"]))
            co.append(corr(d["y"], t[key]))
        print(f"{sid} informative={arg}: oracle R2 with own X={np.mean(co) ** 2:.3f} (corr {np.mean(co):.3f})")

for sid, a, b in (("D-023", "dev_head", "dev_wing"), ("D-040", "dev_b", "dev_h")):
    m = load(sid)
    for arg in (m.RHO_RESID, 0.0):
        c = [corr(t[a], t[b]) for d, t in draws(m, arg, R)]
        print(f"{sid} rho={arg}: corr of true residual deviations={np.mean(c):.3f}")
    d, t = m._draw(np.random.default_rng(3), m.RHO_RESID)
    print("  ", {k: (v.mean().round(2), v.std().round(2)) for k, v in d.items()})

m = load("D-035")
prev, mah = [], []
for d, t in draws(m, True, R):
    prev.append(d["positive"].mean())
corrm = m._correlation()
shift = m.SHIFT_DIR * (m.MAHALANOBIS / np.sqrt(m.SHIFT_DIR @ np.linalg.solve(corrm, m.SHIFT_DIR)))
print(f"D-035: prevalence={np.mean(prev):.3f}; Mahalanobis={np.sqrt(shift @ np.linalg.solve(corrm, shift)):.3f}; "
      f"best balanced accuracy={NormalDist().cdf(m.MAHALANOBIS / 2):.3f}; min eig corr={np.linalg.eigvalsh(corrm).min():.3f}")
d, t = m._draw(np.random.default_rng(3), True)
print("   feature mins", d["features"].min(axis=0).round(2))
for arg in (True, False):
    ag = []
    for d, t in draws(m, arg, 50):
        ag.append(np.mean(d["positive"] == t["condition"]))
    print(f"   informative={arg}: agreement label vs latent condition {np.mean(ag):.3f}")

m = load("D-042")
for arg in (True, False):
    nu, cs, vy, cu = [], [], [], []
    for d, t in draws(m, arg, 100):
        nu.append(np.unique(d["X"], axis=0).shape[0])
        cs.append(corr(d["y"], t["sar"][t["compound"]]))
        vy.append(np.var(d["y"]))
    print(f"D-042 informative={arg}: unique descriptor rows={np.mean(nu):.0f}; corr(y, own SAR)={np.mean(cs):.3f} "
          f"var(y)={np.mean(vy):.3f}")

m = load("D-047")
for arg in (1.0, 0.0):
    clip0, clip100, nsel, ch = [], [], [], []
    for d, t in draws(m, arg, R):
        allv = np.concatenate([d["screening"], d["entry"], d["week12"]])
        clip0.append(np.mean(allv == 0)); clip100.append(np.mean(allv == 100))
        sel = d["screening"] >= 60
        nsel.append(sel.sum()); ch.append(t["change"][sel].mean())
    print(f"D-047 effect={arg}: selected n={np.mean(nsel):.0f}; true change in selected={np.mean(ch):.1f}; "
          f"share at 0={np.mean(clip0):.4f} at 100={np.mean(clip100):.4f}")
nd = NormalDist()
sd = np.sqrt(m.CHANGE_SD ** 2 + 2 * m.VISIT_SD ** 2)
print(f"  D-047 analytic P(entry-week12>=10): plus {1 - nd.cdf((10 + m.CHANGE_MEAN) / sd):.3f}, "
      f"minus {1 - nd.cdf(10 / (np.sqrt(2) * m.VISIT_SD)):.3f}")
