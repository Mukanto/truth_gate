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


def top_corr(X, y, m):
    """Indices of the m columns with the largest absolute Pearson correlation with y (a column with no
    spread scores 0)."""
    A = X - X.mean(axis=0)
    b = y - y.mean()
    den = np.sqrt((A ** 2).sum(axis=0) * (b ** 2).sum())
    r = (A * b[:, None]).sum(axis=0) / np.where(den > 0, den, 1.0)
    return np.argsort(-np.abs(r), kind="stable")[:m]


def criterion(d):
    """Claim: the R-squared of a ridge-penalised linear regression of y (penalty 10, standardised features,
    intercept) that uses 20 of the 500 features, for new samples, is at least 0.10.  The 20 features are
    the ones with the largest absolute Pearson correlation with y.

    Data keys:
      "X": float array (samples, features) = (100, 500); the 500 continuous imaging-derived features of each sample.
      "y": float array (samples,) = (100,); the continuous symptom score of each sample.

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
    fold = np.arange(n) % 5
    pred = np.empty(n)
    sel = top_corr(X, y, 20)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te][:, sel], y[~te], 10.0), X[te][:, sel])
    sst = np.sum((y - y.mean()) ** 2)
    if not sst > 0:
        return None
    r2 = 1.0 - np.sum((y - pred) ** 2) / sst
    if not np.isfinite(r2):
        return None
    return bool(r2 >= 0.10)
