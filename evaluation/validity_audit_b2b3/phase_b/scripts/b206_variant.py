"""B2-06 sensitivity check (not a case file): the faulty criterion with SMOTE interpolating towards one of the
5 nearest positive neighbours (as in the original SMOTE) instead of a random positive. 200 minus and 200 plus
samples, seeds as in stats.py (minus 0..199, plus 10000..10199)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from load import load

m = load("B2-06", "faulty")


def folds(y, k, rng):
    f = np.empty(y.size, dtype=int)
    off = 0
    for c in (True, False):
        idx = np.flatnonzero(y == c)
        f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
        off += idx.size
    return f


def knn(xt, yt, xn, k):
    dist = ((xn[:, None, :] - xt[None, :, :]) ** 2).sum(axis=2)
    nb = np.argsort(dist, axis=1, kind="stable")[:, :k]
    return yt[nb].sum(axis=1) * 2 > k


def smote_nn(xt, yt, rng, kk=5):
    xp = xt[yt]
    mm = xp.shape[0]
    n_new = max(int((~yt).sum()) - mm, 0)
    dd = ((xp[:, None, :] - xp[None, :, :]) ** 2).sum(axis=2)
    np.fill_diagonal(dd, np.inf)
    nn = np.argsort(dd, axis=1)[:, :min(kk, mm - 1)]
    a = rng.integers(0, mm, n_new)
    b = nn[a, rng.integers(0, nn.shape[1], n_new)]
    u = rng.random((n_new, 1))
    return np.vstack([xt, xp[a] + u * (xp[b] - xp[a])]), np.concatenate([yt, np.ones(n_new, dtype=bool)])


def ba_faulty_nn(d):
    x = d["biomarkers"]
    y = d["positive"]
    rng = np.random.default_rng(6)
    xa, ya = smote_nn(x, y, rng)
    f = folds(ya, 5, rng)
    pred = np.zeros(ya.size, dtype=bool)
    for k in range(5):
        te = f == k
        pred[te] = knn(xa[~te], ya[~te], xa[te], 3)
    return 0.5 * (np.mean(pred[ya]) + np.mean(~pred[~ya]))


for w, s in (("minus", 0), ("plus", 10000)):
    v = np.array([ba_faulty_nn(getattr(m, w)(np.random.default_rng(s + i))) for i in range(200)])
    print(w, "mean BA %.3f" % v.mean(), "holds(>=0.75) %d/200" % int(np.sum(v >= 0.75)))
