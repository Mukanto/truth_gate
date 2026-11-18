import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _std_coef(y, X, j):
    """Standardised coefficient of column j of X (n, k) in the regression of y (n,) on an intercept and X."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(coef[1 + j] * np.std(X[:, j], ddof=1) / np.std(y, ddof=1))


def criterion(d):
    """Claim: after accounting for body mass, kidney weight and heart weight are positively related; the
    standardised slope of kidney weight on heart weight is at least 0.25.

    d['kidney_weight'] : (rats,) float, combined kidney weight of each rat, in g
    d['heart_weight']  : (rats,) float, heart weight of each rat, in g
    d['body_mass']     : (rats,) float, body mass of each rat, in g

    Returns True / False; None when a value is not finite, fewer than 3 rats, or a variance is zero.
    """
    kid = np.asarray(d['kidney_weight'], dtype=float)
    heart = np.asarray(d['heart_weight'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(kid)) and np.all(np.isfinite(heart)) and np.all(np.isfinite(body))):
        return None
    if kid.size < 3:
        return None
    y = kid
    x = heart
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    if _flat(y) or _flat(x) or _flat(body):
        return None
    b = _std_coef(y, np.column_stack([x, body]), 0)
    if not np.isfinite(b):
        return None
    return bool(b >= 0.25)
