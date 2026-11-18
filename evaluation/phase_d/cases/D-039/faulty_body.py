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


def slope(x, y):
    """Slope of the ordinary least squares regression of y on x (with intercept); None when x has no spread."""
    a = x - x.mean()
    den = np.sum(a * a)
    if not den > 0:
        return None
    return float(np.sum(a * (y - y.mean())) / den)


def criterion(d):
    """Claim: on future months, the slope of the ordinary least squares regression of observed y on the
    forecasts of a ridge regression of y on the 3 predictors X (penalty 1.0, standardised predictors,
    intercept) is at least 0.5.

    Data keys:
      "X": float array (months_in_order, features) = (400, 3); the 3 continuous monthly predictor series, rows
           in time order.
      "y": float array (months_in_order,) = (400,); the continuous monthly outcome, in time order.

    Returns True when the slope >= 0.5, False otherwise, None at an allowed guard (non-finite values, fewer
    than 2 forecast months, zero variance of the forecasts).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    pred = np.empty(n)
    rng = np.random.default_rng(0)
    fold = np.empty(n, dtype=int)
    fold[rng.permutation(n)] = np.arange(n) % 5
    ev = np.ones(n, dtype=bool)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te], y[~te], 1.0), X[te])
    b = slope(pred[ev], y[ev])
    if b is None:
        return None
    return bool(b >= 0.5)
