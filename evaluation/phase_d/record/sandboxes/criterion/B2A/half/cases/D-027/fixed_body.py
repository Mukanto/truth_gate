import numpy as np


def ols_predict(A, y, tr, te):
    """Ordinary least squares (numpy lstsq) of y on the columns of A over the rows tr; predictions for rows te."""
    coef = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    return A[te] @ coef


def fold_mean_baseline(y, fold):
    """For each row, the mean of y over the rows outside its fold (the training-fold mean predictor)."""
    base = np.empty(y.shape[0])
    for k in range(5):
        te = fold == k
        base[te] = y[~te].mean()
    return base


def criterion(d):
    """Claim: the mean absolute error of an ordinary least squares regression of y on the 25 measurements X
    (with an intercept), for new samples, is at least 10% below that of predicting the mean of y:
    1 - MAE(model) / MAE(mean predictor) >= 0.10.

    Data keys:
      "X": float array (samples, features) = (60, 25); the 25 continuous measurements of each sample.
      "y": float array (samples,) = (60,); the continuous outcome of each sample.

    Returns True when the skill >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero MAE of the mean predictor).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    A = np.column_stack([np.ones(n), X])
    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = ols_predict(A, y, ~te, te)
    base = fold_mean_baseline(y, fold)
    mae0 = np.mean(np.abs(y - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(y - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.10)
