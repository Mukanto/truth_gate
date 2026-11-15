"""Auditor helper (isolated): re-typed copy of the shared Student-t upper-tail quadrature used in the B-1 twins,
evaluated only on textbook values whose answers are known. No criterion, study file or world is imported or called."""
import numpy as np


def sf(t, df):
    t = np.asarray(t, dtype=float)
    df = np.broadcast_to(np.asarray(df, dtype=float), t.shape)
    u = np.linspace(0.0, 1.0, 1001)

    def tail(lo):
        x = lo[..., None] + (np.pi / 2.0 - lo[..., None]) * u
        f = np.cos(x) ** (df[..., None] - 1.0)
        return (f.sum(-1) - 0.5 * (f[..., 0] + f[..., -1])) * (np.pi / 2.0 - lo) / (len(u) - 1)

    ang = np.arctan(np.abs(t) / np.sqrt(df))
    upper = tail(ang) / (2.0 * tail(np.zeros_like(ang)))
    return np.where(t >= 0.0, upper, 1.0 - upper)


known = [  # (t, df, one-sided upper-tail p from standard t tables)
    (12.706, 1, 0.025), (6.314, 1, 0.05), (2.920, 2, 0.05), (2.353, 3, 0.05), (1.833, 9, 0.05),
    (2.228, 10, 0.025), (2.998, 7, 0.01), (1.895, 7, 0.05), (2.093, 19, 0.025), (3.552, 40, 0.0005),
    (1.960, 1e6, 0.025), (1.645, 1e6, 0.05), (2.576, 1e6, 0.005), (0.0, 5, 0.5), (-1.833, 9, 0.95),
]
for t, df, p in known:
    print(f"t={t:8.3f} df={df:>9g}  sf={float(sf(t, df)):.5f}  table={p}")
