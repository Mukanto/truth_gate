import numpy as np


def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd


def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
    return fid


def _knn_scores(xtr, ytr, xte, k):
    """k-nearest-neighbour mean of ytr over the k nearest rows of xtr (Euclidean, columns standardised with xtr)."""
    a, b = _standardise(xtr, xte)
    d2 = (b ** 2).sum(axis=1)[:, None] + (a ** 2).sum(axis=1)[None, :] - 2.0 * (b @ a.T)
    nb = np.argpartition(d2, k - 1, axis=1)[:, :k]
    return ytr[nb].mean(axis=1)


def criterion(d):
    """Claim: the daily driver measurements predict the daily river level in later days of the record: the root-mean-
    square error of the prediction is at most 0.70 standard deviations of the level.
    d["level"]: float array (days,); daily river level, in time order.
    d["drivers"]: float array (days, variables); daily measurements of the variables that may influence the river
    level, in time order.
    Returns True when RMSE / SD(level) is at most 0.70, False otherwise, None at an allowed guard (non-finite values,
    no evaluated day, constant evaluated level)."""
    y = np.asarray(d["level"], dtype=float)
    x = np.asarray(d["drivers"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    rng = np.random.default_rng(2014)
    edges = (np.arange(11) * n) // 10
    parts = []
    for b in range(2, 10):
        tr = np.arange(edges[b])
        te = np.arange(edges[b], edges[b + 1])
        parts.append(_knn_scores(x[tr], y[tr], x[te], 5))
    pred = np.concatenate(parts)
    ye = y[edges[2]:]
    if ye.size < 1 or ye.max() == ye.min():
        return None
    return bool(np.sqrt(np.mean((ye - pred) ** 2)) / ye.std() <= 0.70)
