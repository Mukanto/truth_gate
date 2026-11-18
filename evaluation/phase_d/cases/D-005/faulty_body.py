import numpy as np


def ridge_fit(X, y, lam):
    """Ridge regression on columns standardised with the mean and sd of the rows given, with an
    unpenalised intercept (y centred).  Closed form; dual form when columns outnumber rows."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    ym = y.mean()
    n, p = Z.shape
    if p > n:
        beta = Z.T @ np.linalg.solve(Z @ Z.T + lam * np.eye(n), y - ym)
    else:
        beta = np.linalg.solve(Z.T @ Z + lam * np.eye(p), Z.T @ (y - ym))
    return mu, sd, beta, ym


def ridge_predict(model, X):
    """Predictions of a model returned by ridge_fit."""
    mu, sd, beta, ym = model
    return ((X - mu) / sd) @ beta + ym


def criterion(d):
    """Claim: the R-squared of a ridge regression (penalty 1.0, standardised measurements, intercept) of y on X,
    evaluated on new samples, is at least 0.10.

    Data keys:
      "X": float array (samples, features) = (100, 150); the 150 continuous biomarker measurements of each sample.
      "y": float array (samples,) = (100,); the continuous clinical score of each sample.

    Returns True when R-squared >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero variance of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    pred = ridge_predict(ridge_fit(X, y, 1.0), X)
    sst = np.sum((y - y.mean()) ** 2)
    if not sst > 0:
        return None
    r2 = 1.0 - np.sum((y - pred) ** 2) / sst
    if not np.isfinite(r2):
        return None
    return bool(r2 >= 0.10)
