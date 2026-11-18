import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _resid(y, X):
    """Residuals of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return y - A @ coef


def _r2(y, X):
    """R-squared of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    res = _resid(y, X)
    sst = np.sum((y - np.mean(y)) ** 2)
    return float(1.0 - np.sum(res * res) / sst)


def criterion(d):
    """Claim: heart weight accounts for at least 10% of the variance in liver weight beyond what body mass
    accounts for; the increase in R-squared when heart weight is added to a regression of liver weight on
    body mass is at least 0.10.

    d['liver_weight'] : (mice,) float, liver weight of each mouse, in g
    d['heart_weight'] : (mice,) float, heart weight of each mouse, in g
    d['body_mass']    : (mice,) float, body mass of each mouse, in g

    Returns True / False; None when a value is not finite, fewer than 3 mice, or a variance is zero.
    """
    liver = np.asarray(d['liver_weight'], dtype=float)
    heart = np.asarray(d['heart_weight'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(heart)) and np.all(np.isfinite(body))):
        return None
    if liver.size < 3:
        return None
    with np.errstate(divide='ignore', invalid='ignore'):
        y = liver / body
        x = heart / body
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    if _flat(y) or _flat(x) or _flat(body):
        return None
    stat = _r2(y, x.reshape(-1, 1))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.10)
