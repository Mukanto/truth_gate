"""W35: A logistic model using 20 baseline markers predicts which patients will relapse within five years, in new patients, with AUC of at least 0.75."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 30, 20


def _gen(rng, eff):
    relapse = rng.permutation(np.arange(N) < 12)             # 12 of 30 relapse
    x = rng.standard_normal((N, K))
    x[:, :3] += eff * 1.4 * relapse[:, None]                 # three informative markers
    x = (x - x.mean(axis=0)) / x.std(axis=0)                 # standardised
    return {"markers": x, "relapse": relapse.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: markers (30, 20) standardised baseline marker values for each patient; relapse (30,) bool, True if the
    patient relapsed within five years (12 of 30).
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

    x = np.asarray(d["markers"], dtype=float)
    y = np.asarray(d["relapse"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
        return None
    lam = 1.0        # ridge penalty of the logistic model
    thr = 0.75       # claimed AUC

    def fit_score(xt, yt, xn):
        w = _logit(xt, yt, lam)
        return w[0] + xn @ w[1:]

    rng = np.random.default_rng(2)
    fold = _folds(y, 5, rng)
    s = np.zeros(y.size)
    for k in range(5):
        te = fold == k
        s[te] = fit_score(x[~te], y[~te], x[te])
    auc = _auc(s, y)
    return bool(auc >= thr)


def permute_relapse(d, rng):
    return {**d, "relapse": d["relapse"][rng.permutation(N)]}


STUDY = Study(
    name="W35",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="three of 20 markers shifted 1.4 sd in relapsing patients (population AUC about 0.95 for the ideal predictor) -> no marker carries information; 30 patients, 12 relapses and standardisation unchanged (with 20 markers on 30 patients an in-sample fit still looks good)"),
    },
    controls=[Control("permute_relapse", ["C"], transform=permute_relapse)],
)
