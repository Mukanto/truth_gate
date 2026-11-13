"""W18: In a screening cohort where about one sample in five is positive, a nearest-neighbour rule on 30 biomarkers attains balanced accuracy of at least 0.75 on new samples."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 100, 30


def _gen(rng, eff):
    positive = rng.random(N) < 0.20
    x = rng.standard_normal((N, K))
    x[:, :15] += eff * 1.1 * positive[:, None]               # 15 informative biomarkers
    x = (x - x.mean(axis=0)) / x.std(axis=0)                 # standardised
    return {"biomarkers": x, "positive": positive.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: biomarkers (100, 30) standardised biomarker values; positive (100,) bool, True for a positive sample
    (about 20 of 100).
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

    x = np.asarray(d["biomarkers"], dtype=float)
    y = np.asarray(d["positive"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
        return None
    thr = 0.75       # claimed balanced accuracy
    k_nn = 3

    def smote(xt, yt, rng):
        # synthetic positives: interpolation between two different random positive rows, up to class balance
        xp = xt[yt]
        m = xp.shape[0]
        n_new = max(int((~yt).sum()) - m, 0)
        a = rng.integers(0, m, n_new)
        b = (a + 1 + rng.integers(0, m - 1, n_new)) % m
        u = rng.random((n_new, 1))
        return np.vstack([xt, xp[a] + u * (xp[b] - xp[a])]), np.concatenate([yt, np.ones(n_new, dtype=bool)])

    def balanced(pred, yy):
        return 0.5 * (float(np.mean(pred[yy])) + float(np.mean(~pred[~yy])))

    rng = np.random.default_rng(6)
    fold = _folds(y, 5, rng)
    pred = np.zeros(y.size, dtype=bool)
    for k in range(5):
        te = fold == k
        xa, ya = smote(x[~te], y[~te], rng)
        pred[te] = _knn(xa, ya, x[te], k_nn)
    return bool(balanced(pred, y) >= thr)


def permute_positive(d, rng):
    return {**d, "positive": d["positive"][rng.permutation(N)]}


STUDY = Study(
    name="W18",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="15 of 30 biomarkers shifted 1.1 sd in positive samples -> no biomarker carries information about status; sample size, prevalence (0.2) and standardisation unchanged"),
    },
    controls=[Control("permute_positive", ["C"], transform=permute_positive)],
)
