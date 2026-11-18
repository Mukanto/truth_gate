import numpy as np


def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def poly_features(Z):
    """Intercept, linear terms, squares and all pairwise products of the columns of Z."""
    n, p = Z.shape
    iu, ju = np.triu_indices(p)
    return np.column_stack([np.ones(n), Z, Z[:, iu] * Z[:, ju]])


def poly_fit(X, y):
    """Second-order polynomial regression by ordinary least squares on standardised columns."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    coef = np.linalg.lstsq(poly_features((X - mu) / sd), y, rcond=None)[0]
    return mu, sd, coef


def poly_predict(model, X):
    """Predictions of a model returned by poly_fit."""
    mu, sd, coef = model
    return poly_features((X - mu) / sd) @ coef


def criterion(d):
    """Claim: a second-order polynomial regression of y on X (intercept, the 10 readings, their squares and all
    pairwise products, ordinary least squares) predicts y for new runs with a Pearson correlation between
    predicted and observed y of at least 0.30.

    Data keys:
      "X": float array (samples, features) = (300, 10); the 10 continuous process readings of each production run.
      "y": float array (samples,) = (300,); the continuous quality score of each production run.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 runs, zero variance of the predictions or of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    pred = poly_predict(poly_fit(X, y), X)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
