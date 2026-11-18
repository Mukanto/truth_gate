import sys, zlib, importlib.util
from pathlib import Path
from statistics import NormalDist
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "pkg"))
N01 = NormalDist()

# D-007: oracle R^2 of E[survival | module scores]
b2 = 0.45**2 + 0.20**2; s2 = 0.62**2; v = b2 + s2
raw = np.exp(s2) * (np.exp(2*b2) - np.exp(b2)) / (np.exp(2*v) - np.exp(v))
print(f"D-007 oracle R2 log scale {b2/v:.3f}, raw months {raw:.3f}")

# D-008: attenuation of the within-patient slope by DO2 measurement error (typical patient)
co, hb, sat = 3.3*1.9, 10.5, 0.955
cao2 = 1.34*hb*sat + 0.27
do2 = 10*co*cao2
ar_factor = 0.85   # expected within-6-occasion share of marginal AR(1) variance (rough)
true_var = ar_factor*((10*co*0.15*cao2)**2 + (10*co*1.34*0.5*sat)**2 + (10*co*1.34*hb*0.012)**2)
err_var = (do2*0.06)**2 + (do2*0.02*(cao2-0.27)/cao2)**2 + (10*co*1.34*hb*0.008)**2
rel = true_var/(true_var+err_var)
coupling = 256*do2*(0.06**2 + 0.02**2)/(true_var+err_var)
print(f"D-008 DO2 typical {do2:.0f}, within true SD {np.sqrt(true_var):.0f}, error SD {np.sqrt(err_var):.0f}, "
      f"reliability {rel:.2f}, expected measured gas slope plus {0.25*rel:.3f} minus 0; Fick-coupling bias ~{coupling:.3f}")

# D-010: oracle R^2 (population)
var_lp = 0.095; dist = 0.245**2; cov_lp_u = 0.245*0.6*0.053
tot = var_lp + dist + 2*cov_lp_u + 0.845
print(f"D-010 oracle R2 {(var_lp+dist+2*cov_lp_u)/tot:.3f} r {np.sqrt((var_lp+dist+2*cov_lp_u)/tot):.3f}; "
      f"with district means shrunk (8 per district, reliability 0.34): R2 ~{(var_lp+0.34*dist+cov_lp_u)/tot:.3f}")

# D-011: oracle AUC
dw2 = 40*np.mean(np.random.default_rng(0).uniform(0.15, 0.35, 200000)**2)
D = np.sqrt(2.4**2 + dw2)
print(f"D-011 oracle AUC programme only {N01.cdf(2.4/np.sqrt(2)):.3f}, with weak genes {N01.cdf(D/np.sqrt(2)):.3f}")

# D-012: plot occupancy probabilities
sd_tot = np.sqrt(1 + 0.3**2 + 0.2**2)
po, pf = N01.cdf(-0.5/sd_tot), N01.cdf(0.4/sd_tot)
print(f"D-012 expected occupancy open {po:.3f} fenced {pf:.3f} diff {pf-po:.3f}")

# D-022
print("D-022 signal share 0.30 -> oracle r about", round(np.sqrt(0.30), 3),
      "; rough OLS(66 terms) new-run r at n_train 240:", round(0.30/np.sqrt(0.30+0.70*66/240), 3),
      "at 300:", round(0.30/np.sqrt(0.30+0.70*66/300), 3))

# D-023 (log scale, population)
vs = 0.04**2 + 0.08**2
C = np.zeros((3, 3))  # body, head, wing
own = 0.035**2 + 0.012**2 + 0.01**2
for eff in (True, False):
    lam = vs/(vs+1e-4)
    C[0,0] = vs + 1e-4; C[0,1] = C[1,0] = 0.9*vs; C[0,2] = C[2,0] = 1.1*vs
    C[1,1] = 0.81*vs + 0.03**2 + own; C[2,2] = 1.21*vs + 0.03**2 + own
    C[1,2] = C[2,1] = (0.99*vs + 0.03**2) if eff else 0.99*lam*vs
    pc = (C[1,2] - C[1,0]*C[0,2]/C[0,0]) / np.sqrt((C[1,1]-C[1,0]**2/C[0,0])*(C[2,2]-C[2,0]**2/C[0,0]))
    print(f"D-023 {'plus' if eff else 'minus'} population partial corr (log scale) {pc:.3f}")

# D-040 (population, linear)
vg = 0.75**2 + 1; vl = 16*vg + 17; cgl = 4*vg
for eff in (True, False):
    vb = 6.25*vg + 2.4**2 + 16 + 1 + 1
    cbh = (6.25*vg + 2.4**2) if eff else 6.25*cgl**2/vl
    pc = (cbh - (2.5*cgl)**2/vl) / (vb - (2.5*cgl)**2/vl)
    print(f"D-040 {'plus' if eff else 'minus'} population partial corr {pc:.3f}")

# D-042 variance components
comp = {"series level": 0.64, "global SAR": 0.09, "local SAR": 0.16, "idiosyncratic": 0.25,
        "assay source": 0.09, "replicate noise": 0.45**2}
tot = sum(comp.values())
print("D-042 variance shares", {k: round(v/tot, 3) for k, v in comp.items()},
      "| replicate ICC", round((tot-0.09-0.2025)/tot, 3))

# D-047: P(drop >= 10 | screening >= 60) by integrating the bivariate normal (no clipping)
r1, r2 = np.exp(-0.5), np.exp(-3.0)
vS = 121 + 9 + 64 + 25
cSd = 64*(r1 - r1*r2)
vd = 64*(2 - 2*r2) + 50 + 64
grid = np.linspace(60, 52 + 8*np.sqrt(vS), 4000)
dens = np.exp(-(grid-52)**2/(2*vS)); dens /= dens.sum()
for name, mu in (("plus", 14.0), ("minus", 0.0)):
    m = mu + cSd*(grid-52)/vS; s = np.sqrt(vd - cSd**2/vS)
    p = np.array([1 - N01.cdf((10 - mi)/s) for mi in m])
    print(f"D-047 {name}: P(drop>=10 | screening>=60) ~ {np.sum(p*dens):.3f}; share selected {1-N01.cdf(8/np.sqrt(vS)):.3f}")


def load(bid):
    spec = importlib.util.spec_from_file_location("m", HERE / "skeletons" / f"{bid}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def rng_for(s, i):
    return np.random.default_rng(np.random.SeedSequence([7, zlib.crc32(s.encode()), i]))


# marginal equality of keys over many draws (descriptive, not the claim's statistic)
for bid, key in (("D-007", "survival_months"), ("D-012", "occupied"), ("D-008", "vo2_expired_gas")):
    st = load(bid).STUDY
    out = {}
    for w in ("plus", "minus"):
        vals = [st.worlds[w].generate(rng_for(w, i))[key] for i in range(400)]
        a = np.stack(vals).astype(float)
        out[w] = (a.mean(), a.std(), np.median(a))
    print(f"{bid} {key}: plus mean/sd/median {np.round(out['plus'],3)}  minus {np.round(out['minus'],3)}")

# structure descriptives
st = load("D-042").STUDY
d = st.worlds["plus"].generate(rng_for("x", 0))
print("D-042 unique descriptor rows:", np.unique(d["X"], axis=0).shape[0], "of", d["X"].shape[0])
st = load("D-010").STUDY
d = st.worlds["plus"].generate(rng_for("x", 0))
cnt = d["category"].sum(0)
print("D-010 patients per district: min", cnt.min(), "median", np.median(cnt), "max", cnt.max(), "empty", (cnt == 0).sum())
st = load("D-047").STUDY
d = st.worlds["plus"].generate(rng_for("x", 0))
print("D-047 selected (screening>=60):", int((d["screening"] >= 60).sum()))
