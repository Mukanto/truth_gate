import numpy as np


def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd


def _stratified_folds(rng, y, k):
    """Fold index (0..k-1) of each item, assigned at random within each class of the bool vector y."""
    fid = np.empty(y.size, dtype=np.int64)
    off = 0
    for c in (False, True):
        idx = np.flatnonzero(y == c)
        idx = idx[rng.permutation(idx.size)]
        fid[idx] = (np.arange(idx.size) + off) % k
        off += idx.size
    return fid


def _oversample(x, y, rng):
    """Random oversampling: rows of the smaller class of the bool vector y are copied, drawn with replacement, until
    the two classes have equal counts."""
    npos = int(y.sum())
    nneg = y.size - npos
    minority = npos < nneg
    nmin = min(npos, nneg)
    nsyn = abs(npos - nneg)
    if nmin == 0 or nsyn == 0:
        return x, y
    idx = np.flatnonzero(y == minority)
    pick = idx[rng.integers(0, idx.size, nsyn)]
    return np.vstack([x, x[pick]]), np.concatenate([y, y[pick]])


def _knn_scores(xtr, ytr, xte, k):
    """k-nearest-neighbour mean of ytr over the k nearest rows of xtr (Euclidean, columns standardised with xtr)."""
    a, b = _standardise(xtr, xte)
    d2 = (b ** 2).sum(axis=1)[:, None] + (a ** 2).sum(axis=1)[None, :] - 2.0 * (b @ a.T)
    nb = np.argpartition(d2, k - 1, axis=1)[:, :k]
    return ytr[nb].mean(axis=1)


def _auc(score, y):
    """Area under the ROC curve of score for the bool vector y (average ranks for ties)."""
    n = score.size
    order = np.argsort(score, kind="mergesort")
    s = score[order]
    new = np.concatenate([[True], s[1:] != s[:-1]])
    gid = np.cumsum(new) - 1
    first = np.flatnonzero(new)
    last = np.concatenate([first[1:], [n]])
    avg = (first + last + 1) / 2.0
    ranks = np.empty(n)
    ranks[order] = avg[gid]
    n1 = float(y.sum())
    n0 = n - n1
    return (ranks[y].sum() - n1 * (n1 + 1.0) / 2.0) / (n1 * n0)


def criterion(d):
    """Claim: a classifier built from the measured variables ranks new records correctly: the area under the ROC curve
    for the event is at least 0.75.
    d["features"]: float array (records, variables); measured variables of each record.
    d["event"]: bool array (records,); True if the event occurred for the record.
    Returns True when the AUC is at least 0.75, False otherwise, None at an allowed guard (non-finite values, a class
    with no record)."""
    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["event"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.all() or not y.any():
        return None
    rng = np.random.default_rng(2012)
    folds = _stratified_folds(rng, y, 10)
    ye = y
    scores = np.zeros(y.size)
    for f in range(10):
        te = folds == f
        xs, ys = _oversample(x[~te], y[~te], rng)
        scores[te] = _knn_scores(xs, ys.astype(float), x[te], 5)
    return bool(_auc(scores, ye) >= 0.75)
