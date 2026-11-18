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
    """Claim: age explains at least 10% of the variance in liver mass beyond what body mass explains; the
    increase in R-squared when age is added to a regression of liver mass on body mass is at least 0.10.

    d['liver_mass'] : (rats,) float, liver mass of each rat, in g
    d['age_days']   : (rats,) float, age of each rat, in days
    d['body_mass']  : (rats,) float, body mass of each rat, in g

    Returns True / False; None when a value is not finite, fewer than 3 rats, or a variance is zero.
    """
    liver = np.asarray(d['liver_mass'], dtype=float)
    age = np.asarray(d['age_days'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(age)) and np.all(np.isfinite(body))):
        return None
    if liver.size < 3:
        return None
    y = liver
    if not np.all(np.isfinite(y)):
        return None
    if _flat(y) or _flat(age) or _flat(body):
        return None
    stat = _r2(y, np.column_stack([body, age])) - _r2(y, body.reshape(-1, 1))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.10)
