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


def impute(X, fit, aux, sweeps=5):
    """Iterative regression imputation.  Start from the column means over the rows in fit; in each sweep
    every incomplete column is regressed (ridge, penalty 1.0) on the other columns of X and on the columns
    of aux, fitted on the rows in fit where the column was observed, and applied to the rows where it is
    missing (all rows, whether in fit or not)."""
    n, p = X.shape
    miss = np.isnan(X)
    cnt = (~miss[fit]).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.where(miss[fit], 0.0, X[fit]).sum(axis=0) / cnt
    Xc = np.where(miss, mu, X)
    for _ in range(sweeps):
        for j in range(p):
            mj = miss[:, j]
            if not mj.any():
                continue
            Z = np.column_stack([np.delete(Xc, j, axis=1), aux])
            obs = fit & ~mj
            m = ridge_fit(Z[obs], Xc[obs, j], 1.0)
            Xc[mj, j] = ridge_predict(m, Z[mj])
    return Xc


def criterion(d):
    """Claim: the R-squared of a ridge regression (penalty 1.0, standardised values, intercept) of y on the 20
    laboratory values in X, for new patients, is at least 0.10.  Values not measured are NaN and are filled
    by iterative ridge regression imputation (5 sweeps) before the regression.

    Data keys:
      "X": float array (samples, features) = (250, 20); the 20 laboratory values of each patient, NaN where
           a value was not measured.
      "y": float array (samples,) = (250,); the continuous clinical outcome of each patient.

    Returns True when R-squared >= 0.10, False otherwise, None at an allowed guard (infinite values in X or
    non-finite y, fewer than 2 patients, a column with no observed value, zero variance of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if np.any(np.isinf(X)) or not np.all(np.isfinite(y)):
        return None
    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        Xc = impute(X, ~te, np.empty((n, 0)))
        pred[te] = ridge_predict(ridge_fit(Xc[~te], y[~te], 1.0), Xc[te])
    sst = np.sum((y - y.mean()) ** 2)
    if not sst > 0:
        return None
    r2 = 1.0 - np.sum((y - pred) ** 2) / sst
    if not np.isfinite(r2):
        return None
    return bool(r2 >= 0.10)
