"""W30: In a fraud-screening data set where about 12% of transactions are fraudulent, a nearest-neighbour rule on 10 transaction features achieves an F1 score of at least 0.60 for fraud on new transactions."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 150, 10


def _gen(rng, eff):
    fraud = rng.random(N) < 0.12
    x = rng.standard_normal((N, K))
    x[:, :6] += eff * 1.6 * fraud[:, None]                   # six informative features
    x = (x - x.mean(axis=0)) / x.std(axis=0)                 # standardised
    return {"features": x, "fraud": fraud.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: features (150, 10) standardised transaction features; fraud (150,) bool, True for a fraudulent transaction
    (about 18 of 150).
    Holds when the claim is supported by the data. Written by someone else."""
    def _folds(y, k, rng):
        # stratified random fold labels 0..k-1
        f = np.empty(y.size, dtype=int)
        off = 0
        for c in (True, False):
            idx = np.flatnonzero(y == c)
            f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    def _knn(xt, yt, xn, k):
        dist = ((xn[:, None, :] - xt[None, :, :]) ** 2).sum(axis=2)
        nb = np.argsort(dist, axis=1, kind="stable")[:, :k]
        return yt[nb].sum(axis=1) * 2 > k

    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["fraud"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
        return None
    thr = 0.60       # claimed F1 for fraud

    def copy_up(xt, yt, rng):
        # copies of randomly drawn fraud rows (with replacement) until the classes are balanced
        pos = np.flatnonzero(yt)
        n_new = max(int((~yt).sum()) - pos.size, 0)
        pick = pos[rng.integers(0, pos.size, n_new)]
        return np.vstack([xt, xt[pick]]), np.concatenate([yt, np.ones(n_new, dtype=bool)])

    def f1(pred, yy):
        tp = float(np.sum(pred & yy))
        return 2.0 * tp / (2.0 * tp + float(np.sum(pred & ~yy)) + float(np.sum(~pred & yy)))

    rng = np.random.default_rng(8)
    fold = _folds(y, 5, rng)
    pred = np.zeros(y.size, dtype=bool)
    for k in range(5):
        te = fold == k
        xa, ya = copy_up(x[~te], y[~te], rng)
        pred[te] = _knn(xa, ya, x[te], 1)
    return bool(f1(pred, y) >= thr)


def permute_fraud(d, rng):
    return {**d, "fraud": d["fraud"][rng.permutation(N)]}


STUDY = Study(
    name="W30",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="six of ten features shifted 1.6 sd for fraudulent transactions -> no feature carries information about fraud; prevalence (12%), sample size and standardisation unchanged"),
    },
    controls=[Control("permute_fraud", ["C"], transform=permute_fraud)],
)
