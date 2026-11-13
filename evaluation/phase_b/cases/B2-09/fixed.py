"""W14: From 8 yearly indicators, the model predicts civil war onset in future country-years with AUC of at least 0.75."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 200, 8


def _ar(rng, n, k, rho):
    e = rng.standard_normal((n, k))
    out = np.empty((n, k))
    out[0] = e[0]
    s = np.sqrt(1.0 - rho ** 2)
    for t in range(1, n):
        out[t] = rho * out[t - 1] + s * e[t]
    return out


def _gen(rng, eff):
    z = _ar(rng, N, K, 0.9)                                  # slowly moving indicators
    h = _ar(rng, N, 1, 0.95)[:, 0]                           # slowly moving unobserved hazard
    u = rng.random(N)
    obs_noise = rng.standard_normal((N, K))
    beta = np.zeros(K)
    beta[:4] = 0.9                                           # four informative indicators
    logit0 = 1.1 * h + eff * (z @ beta)
    lo, hi = -15.0, 8.0
    for _ in range(50):                                      # intercept chosen so that about 15% of rows are onsets
        a = 0.5 * (lo + hi)
        if np.mean(1.0 / (1.0 + np.exp(-(a + logit0)))) > 0.15:
            hi = a
        else:
            lo = a
    p = 1.0 / (1.0 + np.exp(-(a + logit0)))
    onset = u < p
    x = z + 0.3 * obs_noise
    return {"x": x, "onset": onset.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: x (200, 8) indicator values, one country-year per row, rows in time order; onset (200,) bool, True if a
    civil war began in that year (about 15% onsets).
    Holds when the claim is supported by the data. Written by someone else."""
    def _auc(s, y):
        p, q = s[y], s[~y]
        diff = p[:, None] - q[None, :]
        return float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / (p.size * q.size))

    def _folds(y, k, rng):
        # stratified random fold labels 0..k-1
        f = np.empty(y.size, dtype=int)
        off = 0
        for c in (True, False):
            idx = np.flatnonzero(y == c)
            f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    def _logit(xt, yt, lam):
        # ridge logistic regression (Newton / IRLS), unpenalised intercept
        n, p = xt.shape
        a = np.column_stack([np.ones(n), xt])
        pen = lam * np.eye(p + 1)
        pen[0, 0] = 0.0
        t = yt.astype(float)
        w = np.zeros(p + 1)
        for _ in range(30):
            mu = 1.0 / (1.0 + np.exp(-np.clip(a @ w, -30.0, 30.0)))
            g = a.T @ (mu - t) + pen @ w
            h = (a.T * np.maximum(mu * (1.0 - mu), 1e-6)) @ a + pen
            step = np.linalg.solve(h, g)
            w = w - step
            if np.max(np.abs(step)) < 1e-8:
                break
        return w

    x = np.asarray(d["x"], dtype=float)
    y = np.asarray(d["onset"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
        return None
    lam = 1.0        # ridge penalty of the logistic model
    thr = 0.75       # claimed AUC

    def fit_score(xt, yt, xn):
        w = _logit(xt, yt, lam)
        return w[0] + xn @ w[1:]

    cut = int(0.7 * y.size)           # rows are in time order: fit on the first 70%, evaluate on the last 30%
    tr, te = np.arange(y.size) < cut, np.arange(y.size) >= cut
    if y[tr].sum() < 2 or (~y[tr]).sum() < 2 or y[te].sum() < 2 or (~y[te]).sum() < 2:
        return None
    s = fit_score(x[tr], y[tr], x[te])
    return bool(_auc(s, y[te]) >= thr)


def permute_onset(d, rng):
    return {**d, "onset": d["onset"][rng.permutation(N)]}


STUDY = Study(
    name="W14",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="four of the eight indicators enter the onset hazard (coefficient 0.9 each) -> no indicator carries information about onset; the slowly varying unobserved hazard (onsets cluster in time), the autocorrelated indicators and the 15% prevalence are unchanged"),
    },
    controls=[Control("permute_onset", ["C"], transform=permute_onset)],
)
