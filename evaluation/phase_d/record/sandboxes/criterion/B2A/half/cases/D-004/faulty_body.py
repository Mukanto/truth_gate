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
    """Claim: on future days, a ridge regression forecast of y from the day's 5 predictors X (penalty 1.0,
    standardised predictors, intercept, one model for all stations) has a squared error at least 5% below
    that of the persistence forecast (the previous day's y at the same station), squared errors pooled over
    stations: 1 - MSE(model) / MSE(persistence) >= 0.05.

    Data keys:
      "X": float array (stations, days_in_order, features) = (40, 250, 5); the 5 continuous daily predictors
           at each station on each day, days in time order.
      "y": float array (stations, days_in_order) = (40, 250); the continuous daily outcome at each station,
           days in time order.

    Returns True when the skill >= 0.05, False otherwise, None at an allowed guard (non-finite values, no
    forecast day, zero MSE of the persistence forecast).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    S, T, F = X.shape
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    Xf = X.reshape(S * T, F)
    yf = y.reshape(S * T)
    rng = np.random.default_rng(0)
    fold = np.empty(S * T, dtype=int)
    fold[rng.permutation(S * T)] = np.arange(S * T) % 5
    pred = np.empty(S * T)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(Xf[~te], yf[~te], 1.0), Xf[te])
    ev = np.zeros((S, T), dtype=bool)
    ev[:, 1:] = True
    pred = pred.reshape(S, T)
    prev = np.zeros((S, T))
    prev[:, 1:] = y[:, :-1]
    if not ev.any():
        return None
    mse0 = np.mean((y[ev] - prev[ev]) ** 2)
    if not mse0 > 0:
        return None
    skill = 1.0 - np.mean((y[ev] - pred[ev]) ** 2) / mse0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.05)
