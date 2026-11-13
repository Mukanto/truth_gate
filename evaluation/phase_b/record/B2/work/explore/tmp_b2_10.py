"""W37: Using 6 weekly indicators, a ridge regression forecasts next-week hospital admissions in future weeks with R^2 of at least 0.30."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 150, 6


def _ar(rng, n, k, rho):
    e = rng.standard_normal((n, k))
    out = np.empty((n, k))
    out[0] = e[0]
    s = np.sqrt(1.0 - rho ** 2)
    for t in range(1, n):
        out[t] = rho * out[t - 1] + s * e[t]
    return out


def _gen(rng, eff):
    lead = _ar(rng, N, 1, 0.8)[:, 0]                         # driver that the first three indicators measure
    other = _ar(rng, N, 1, 0.8)[:, 0]                        # an equally persistent driver unrelated to the indicators
    walk = _ar(rng, N, 3, 0.95)                              # three slowly drifting indicators
    meas = 0.8 * rng.standard_normal((N, 3))
    res = _ar(rng, N, 1, 0.7)[:, 0]
    ind = np.empty((N, K))
    ind[:, :3] = lead[:, None] + meas
    ind[:, 3:] = walk
    admissions_next = 300.0 + 30.0 * (eff * lead + (1.0 - eff) * other) + 25.0 * res
    return {"indicators": ind, "admissions_next": admissions_next}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: indicators (150, 6) weekly indicator values, axes (weeks, indicators), rows in time order;
    admissions_next (150,) admissions in the following week.
    Holds when the claim is supported by the data. Written by someone else."""
    def _ridge(xt, yt, lam):
        # ridge regression on training-standardised features
        mu = xt.mean(axis=0)
        sd = np.maximum(xt.std(axis=0), 1e-12)
        z = (xt - mu) / sd
        ym = yt.mean()
        w = np.linalg.solve(z.T @ z + lam * np.eye(z.shape[1]), z.T @ (yt - ym))
        return lambda xn: ym + ((xn - mu) / sd) @ w

    x = np.asarray(d["indicators"], dtype=float)
    y = np.asarray(d["admissions_next"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    if not np.all(x.std(axis=0) > 0) or not y.std() > 0:
        return None
    lam = 100.0        # ridge penalty
    thr = 0.30       # claimed R^2

    def r2(yy, pp):
        return 1.0 - float(np.sum((yy - pp) ** 2)) / float(np.sum((yy - yy.mean()) ** 2))

    cut = int(y.size * 2 // 3)        # rows are in time order: fit on the first two thirds, evaluate on the last third
    tr, te = np.arange(y.size) < cut, np.arange(y.size) >= cut
    if not y[te].std() > 0:
        return None
    p = _ridge(x[tr], y[tr], lam)(x[te])
    return bool(r2(y[te], p) >= thr)


def permute_weeks(d, rng):
    return {**d, "admissions_next": d["admissions_next"][rng.permutation(N)]}


STUDY = Study(
    name="W37",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="next-week admissions follow the driver that three indicators measure (coefficient 30; ideal forward R squared about 0.45) -> they follow an equally persistent driver unrelated to every indicator; the autocorrelated residual, the drifting indicators and all variances unchanged"),
    },
    controls=[Control("permute_weeks", ["C"], transform=permute_weeks)],
)
