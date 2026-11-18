import numpy as np


def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def nn_predict(Xtr, ytr, Xte):
    """One-nearest-neighbour prediction: the y of the nearest training row (Euclidean distance on
    columns standardised with the training mean and sd; the first of tied rows wins)."""
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    A = (Xtr - mu) / sd
    B = (Xte - mu) / sd
    D2 = (B ** 2).sum(axis=1)[:, None] + (A ** 2).sum(axis=1)[None, :] - 2.0 * (B @ A.T)
    return ytr[np.argmin(D2, axis=1)]


def cv_nn(X, y, fold):
    """Pooled held-out one-nearest-neighbour predictions over the 5 folds given by fold."""
    pred = np.empty(y.shape[0], dtype=y.dtype)
    for k in range(5):
        te = fold == k
        pred[te] = nn_predict(X[~te], y[~te], X[te])
    return pred


def link_components(X, frac):
    """Single-linkage components of the rows of X: two rows are linked when their distance (Euclidean, on
    columns standardised with all rows) is below frac times the median pairwise distance.  Returns the
    component number of each row, numbered in order of the first member of each component."""
    sd = X.std(axis=0)
    Z = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)
    sq = (Z ** 2).sum(axis=1)
    D = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2.0 * (Z @ Z.T), 0.0))
    n = D.shape[0]
    med = np.median(D[np.triu_indices(n, k=1)])
    A = D < frac * med
    lab = np.arange(n)
    while True:
        new = np.minimum(lab, np.where(A, lab[None, :], n).min(axis=1))
        if np.array_equal(new, lab):
            break
        lab = new
    return np.searchsorted(np.unique(lab), lab)


def criterion(d):
    """Claim: a one-nearest-neighbour regression (Euclidean distance on standardised descriptors) of y on X
    predicts y for new compounds with a Pearson correlation between predicted and observed y of at least
    0.30.  Evaluated by 5-fold cross-validation over the records.

    Data keys:
      "X": float array (records, features) = (1200, 20); the 20 continuous molecular descriptors of each compound record.
      "y": float array (records,) = (1200,); the continuous activity response measured for each compound record.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 records, zero variance of the predictions or of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    fold = np.arange(n) % 5
    pred = cv_nn(X, y, fold)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
