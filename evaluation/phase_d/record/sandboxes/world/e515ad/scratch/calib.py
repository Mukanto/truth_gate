# Calibration of generative constants (population quantities from model parameters only).
import numpy as np
from statistics import NormalDist
N = NormalDist()
rng = np.random.default_rng(1)

# D-012 probit constants
sd_plot, sd_w = 0.35, 0.7
T = np.sqrt(1 + sd_w**2 + sd_plot**2)
m = T * N.inv_cdf(0.30)
d = T * N.inv_cdf(0.58) - m
print("D012 T m delta", T, m, d)

# D-010 covariate signal variance
M = 2_000_000
K = 150
dist = rng.integers(0, K, M)
age_shift = rng.normal(0, 4, K); bmi_shift = rng.normal(0, 0.05, K)
age = np.clip(52 + age_shift[dist] + 14 * rng.standard_normal(M), 18, 92)
bmi = np.exp(np.log(26.5) + bmi_shift[dist] + 0.16 * rng.standard_normal(M))
sbp = 92 + 0.45 * age + 0.6 * bmi + rng.normal(0, 13, M)
print("D010 means", age.mean(), bmi.mean(), sbp.mean(), "sds", age.std(), bmi.std(), sbp.std())
az = (age - 52) / 14.6; bz = (bmi - 26.8) / 4.4; sz = (sbp - 131.5) / 14.8
lin = 0.18 * az + 0.15 * bz + 0.12 * sz
print("D010 var cov signal", lin.var(), "corr", np.corrcoef([age, bmi, sbp]).round(3).tolist())

# D-022 signal variance
A = np.array([
    [0.7, 0.6, 0.0, 0.5, 0.0, 0.0, 0.4, 0.0, 0.0, 0.3],
    [0.0, 0.3, 0.7, 0.0, 0.6, 0.0, 0.0, 0.5, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.3, 0.0, 0.7, 0.4, 0.0, 0.6, 0.5],
])
comm = (A**2).sum(0); print("D022 communalities", comm)
F = rng.standard_normal((M, 3)); Z = F @ A + np.sqrt(1 - comm) * rng.standard_normal((M, 10))
f = (1.0 * Z[:, 0] - 0.7 * Z[:, 3] + 0.5 * Z[:, 6] - 0.8 * (Z[:, 1] - 0.4) ** 2 - 0.5 * Z[:, 2] ** 2
     + 0.7 * Z[:, 0] * Z[:, 4] - 0.5 * Z[:, 5] * Z[:, 7])
lin_part = 1.0 * Z[:, 0] - 0.7 * Z[:, 3] + 0.5 * Z[:, 6]
print("D022 var f", f.var(), "mean f", f.mean(), "var lin part", lin_part.var(), "noise sd for R2=.30", np.sqrt(f.var() * 0.7 / 0.3))

# D-042 activity variance
u = rng.standard_normal((M, 3))
fa = 0.75 * u[:, 0] - 0.45 * u[:, 1] + 0.25 * u[:, 0] * u[:, 2] - 0.2 * (u[:, 1] ** 2 - 1)
print("D042 var f", fa.var())

# D-047 population proportion (from parameters): P(entry-week12 >= 10 | screening >= 60)
Tt = np.clip(rng.normal(56, 12, M), 5, 95)
scr = Tt + rng.normal(0, 9, M)
sel = scr >= 60
Ts = Tt[sel]
for mu in (0.22, 0.0):
    sdv = np.sqrt((0.20 * Ts) ** 2 + 2 * 81)
    p = np.array([1 - N.cdf(z) for z in ((10 - mu * Ts) / sdv)[:200000]])
    print("D047 mu_r", mu, "P", p.mean(), "selected frac", sel.mean(), "E[T|sel]", Ts.mean())
