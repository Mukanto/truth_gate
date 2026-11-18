import numpy as np


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


def fold_mean_baseline(y, fold):
    """For each row, the mean of y over the rows outside its fold (the training-fold mean predictor)."""
    base = np.empty(y.shape[0])
    for k in range(5):
        te = fold == k
        base[te] = y[~te].mean()
    return base


def criterion(d):
    """Claim: a one-nearest-neighbour regression (Euclidean distance on standardised measurements) of y on X
    predicts y for new entries with a mean absolute error at least 10% below that of predicting the mean
    of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10.  Evaluated by 5-fold cross-validation (fold of
    row i = i mod 5); the mean predictor of a held-out row is the mean of y over its training folds.

    Data keys:
      "X": float array (rows, features) = (600, 8); the 8 continuous property measurements of each registry entry.
      "y": float array (rows,) = (600,); the continuous target value of each registry entry.

    Returns True when the skill >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 rows, zero MAE of the mean predictor).
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
    base = fold_mean_baseline(y, fold)
    mae0 = np.mean(np.abs(y - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(y - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.10)
