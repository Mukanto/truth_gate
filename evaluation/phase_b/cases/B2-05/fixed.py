"""W16: Using 12 country-level indicators, the model identifies which country-years will see a civil war onset, with AUC of at least 0.75 in new country-years."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 250, 12


def _gen(rng, eff):
    onset = rng.random(N) < 0.15
    f = rng.standard_normal(N)                               # factor shared by all indicators
    e = rng.standard_normal((N, K))
    u = rng.random((N, K))
    shift = np.zeros(K)
    shift[:6] = 0.7                                          # six informative indicators
    full = 0.4 * f[:, None] + np.sqrt(1.0 - 0.4 ** 2) * e + eff * onset[:, None] * shift[None, :]
    p_miss = np.where(onset, 0.27, 0.19)                     # recording gaps are more frequent in onset rows, both worlds
    observed = u >= p_miss[:, None]
    x = np.where(observed, full, 0.0)                        # unobserved entries hold 0
    return {"x": x, "observed": observed.astype(bool), "onset": onset.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: x (250, 12) indicator values, one row per country-year, entries flagged as unobserved hold 0;
    observed (250, 12) bool, True where the indicator was recorded; onset (250,) bool, True if a civil war began in that
    country-year (about 15%).
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
    obs = np.asarray(d["observed"]).astype(bool)
    y = np.asarray(d["onset"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
        return None
    lam = 1.0        # ridge penalty of the logistic model
    thr = 0.75       # claimed AUC

    def obs_means(xx, oo):
        # mean of the observed values of each indicator over the rows given; None if an indicator has none
        if np.any(oo.sum(axis=0) == 0):
            return None
        return (xx * oo).sum(axis=0) / oo.sum(axis=0)

    def fill(xx, oo, means):
        return np.where(oo, xx, means[None, :])

    # unobserved entries are filled with the training-fold mean of the observed values (no use of the outcome)
    rng = np.random.default_rng(5)
    fold = _folds(y, 5, rng)
    s = np.zeros(y.size)
    for k in range(5):
        te = fold == k
        m = obs_means(x[~te], obs[~te])
        if m is None:
            return None
        xtr, xte = fill(x[~te], obs[~te], m), fill(x[te], obs[te], m)
        w = _logit(xtr, y[~te], lam)
        s[te] = w[0] + xte @ w[1:]
    auc = _auc(s, y)
    return bool(auc >= thr)


def permute_onset(d, rng):
    return {**d, "onset": d["onset"][rng.permutation(N)]}


STUDY = Study(
    name="W16",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="six of the twelve indicators are shifted 0.7 sd in onset rows -> the recorded indicator values carry no information about onset; the pattern of missing entries (19% missing in non-onset rows, 27% in onset rows) and the zero filling are unchanged"),
    },
    controls=[Control("permute_onset", ["C"], transform=permute_onset)],
)
