"""Offline calibration of generative constants (population quantities only, no analysis of observed data)."""
import numpy as np

rng = np.random.default_rng(1)

# D-012: logistic-normal marginal means; latent SD = sqrt(0.5^2 + 0.8^2)
sd_lat = np.sqrt(0.5 ** 2 + 0.8 ** 2)
z = rng.standard_normal(2_000_000) * sd_lat


def mean_p(a):
    return np.mean(1 / (1 + np.exp(-(a + z))))


def solve(target):
    lo, hi = -5.0, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if mean_p(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


a_open = solve(0.33)
a_fenced = solve(0.61)
print("D-012 alpha", a_open, "gamma", a_fenced - a_open)

# D-022: SD of f(Z) under correlation R
R22 = np.eye(10)
pairs = {(0, 1): 0.3, (1, 9): 0.25, (2, 3): 0.45, (4, 9): 0.5, (6, 0): -0.35, (5, 8): 0.2, (3, 7): 0.2}
for (i, j), r in pairs.items():
    R22[i, j] = R22[j, i] = r
print("D-022 eig min", np.linalg.eigvalsh(R22).min())
L = np.linalg.cholesky(R22)
Z = rng.standard_normal((2_000_000, 10)) @ L.T
f = (0.45 * Z[:, 0] - 0.35 * Z[:, 2] + 0.25 * Z[:, 5] - 0.30 * (Z[:, 1] ** 2 - 1) + 0.30 * Z[:, 0] * Z[:, 3]
     - 0.25 * Z[:, 4] * Z[:, 6] + 0.20 * Z[:, 2] * Z[:, 7] + 0.15 * (Z[:, 8] ** 2 - 1))
print("D-022 f mean", f.mean(), "sd", f.std())

# D-042: SD of g(z) with z ~ N(0, (1 + 0.35^2) I_6)
s = np.sqrt(1 + 0.35 ** 2)
zz = rng.standard_normal((2_000_000, 6)) * s
g = 0.6 * zz[:, 0] - 0.45 * zz[:, 1] + 0.35 * zz[:, 2] + 0.25 * (zz[:, 0] * zz[:, 3]) - 0.2 * (zz[:, 1] ** 2 - s ** 2)
print("D-042 g mean", g.mean(), "sd", g.std())
