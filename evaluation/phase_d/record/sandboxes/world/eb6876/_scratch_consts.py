# Scratch: Monte Carlo constants for the generative models (model math only, no analysis of generated data).
import numpy as np

rng = np.random.default_rng(1)

# D-022: variance of the true process-quality function under AR(0.4) correlated readings
R = 0.4 ** np.abs(np.subtract.outer(np.arange(10), np.arange(10)))
C = np.linalg.cholesky(R)
Z = rng.standard_normal((2_000_000, 10)) @ C.T
f = (0.35 * Z[:, 0] + 0.25 * Z[:, 2] - 0.20 * Z[:, 5] - 0.30 * (Z[:, 3] ** 2 - 1) - 0.20 * (Z[:, 7] ** 2 - 1)
     + 0.30 * Z[:, 1] * Z[:, 4] - 0.25 * Z[:, 6] * Z[:, 8])
print("D-022 F_SD", f.std(), "mean", f.mean())

# D-042: variance of the activity function of the 4-d latent (var 1.09 per dim)
L = rng.standard_normal((2_000_000, 4)) * np.sqrt(1.09)
g = np.sin(1.3 * L[:, 0]) + 0.8 * L[:, 1] - 0.5 * (L[:, 2] ** 2 - 1.09) + 0.6 * L[:, 0] * L[:, 3]
print("D-042 G_SD", g.std(), "mean", g.mean())
W = np.cos(np.outer(np.arange(1, 5), np.arange(1, 21)) * 0.9 + np.arange(4)[:, None])
W = W / np.linalg.norm(W, axis=0)
print("D-042 W rank", np.linalg.matrix_rank(W), "sv", np.linalg.svd(W, compute_uv=False))

# D-007: raw-scale oracle R^2 of lognormal survival
for corr, tau in [(0.72, 0.6)]:
    b = corr * tau
    s = tau * np.sqrt(1 - corr ** 2)
    print("D-007 raw R2", (np.exp(b * b) - 1) / (np.exp(b * b + s * s) - 1), "log R2", corr ** 2)

# D-012: expected occupancy by group under the logit model
plot = rng.standard_normal(2_000_000) * 0.5
quad = rng.standard_normal(2_000_000) * 0.7
for eff in (0.0, 1.5):
    p = 1 / (1 + np.exp(-(-0.85 + eff + plot + quad)))
    print("D-012 eff", eff, "mean occupancy", p.mean())

# D-047: P(entry - week12 >= 10) ignoring clipping
from math import erf, sqrt
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
sd = sqrt(9 ** 2 * 3)
for m in (15.0, 0.0):
    print("D-047 mean change", m, "P(drop>=10)", 1 - Phi((10 - m) / sd))
