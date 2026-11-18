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


def fold_mean_baseline(y, fold):
    """For each row, the mean of y over the rows outside its fold (the training-fold mean predictor)."""
    base = np.empty(y.shape[0])
    for k in range(5):
        te = fold == k
        base[te] = y[~te].mean()
    return base


def criterion(d):
    """Claim: for new subjects, a ridge regression of the trial-level outcome y on the features X (penalty 1.0,
    standardised features, intercept) has a mean absolute error at least 5% below that of predicting the
    mean outcome: 1 - MAE(model) / MAE(mean predictor) >= 0.05.  Evaluated by 5-fold cross-validation over
    the pooled subject-trial rows; the mean predictor of a held-out row is the mean of y over its training folds.

    Data keys:
      "X": float array (subjects, trials, features) = (60, 30, 25); the 25 continuous features computed for
           each trial of each subject.
      "y": float array (subjects, trials) = (60, 30); the continuous outcome of each trial of each subject.

    Returns True when the skill >= 0.05, False otherwise, None at an allowed guard (non-finite values, no
    held-out trial, zero MAE of the mean predictor).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    S, T, F = X.shape
    if S * T < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    Xf = X.reshape(S * T, F)
    yf = y.reshape(S * T)
    fold = np.repeat(np.arange(S) % 5, T)
    pred = np.empty(S * T)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(Xf[~te], yf[~te], 1.0), Xf[te])
    base = fold_mean_baseline(yf, fold)
    mae0 = np.mean(np.abs(yf - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(yf - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.05)
