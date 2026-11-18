import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _corr(a, b):
    """Pearson correlation of two 1-D arrays; None when either has zero variance."""
    if _flat(a) or _flat(b):
        return None
    a = a - np.mean(a)
    b = b - np.mean(b)
    sa = np.sqrt(np.sum(a * a))
    sb = np.sqrt(np.sum(b * b))
    if sa == 0.0 or sb == 0.0:
        return None
    return float(np.sum(a * b) / (sa * sb))


def criterion(d):
    """Claim: across children, BMI at age 5 and the yearly rate of change in BMI between ages 5 and 10 are
    negatively correlated; the correlation between the two is at most -0.25.

    d['bmi'] : (children, annual_visits) float, BMI of each child at the annual visits at ages 5, 6, 7, 8,
               9 and 10 (visits in age order), in kg/m2

    Returns True / False; None when a value is not finite, fewer than 2 children, fewer than 3 visits, a
    variance is zero, or (fitted random-effects model) the estimated variance of the random intercept or of
    the random slope is not positive, so that their correlation is not defined.
    """
    bmi = np.asarray(d['bmi'], dtype=float)
    if not np.all(np.isfinite(bmi)):
        return None
    n, m = bmi.shape
    if n < 2 or m < 3:
        return None
    X = np.column_stack([np.ones(m), np.arange(m, dtype=float)])
    XtXi = np.linalg.inv(X.T @ X)
    bhat = bmi @ X @ XtXi
    res = bmi - bhat @ X.T
    s2 = np.sum(res * res) / (n * (m - 2))
    G = np.cov(bhat, rowvar=False) - s2 * XtXi
    if not (G[0, 0] > 0.0 and G[1, 1] > 0.0):
        return None
    r = float(G[0, 1] / np.sqrt(G[0, 0] * G[1, 1]))
    if r is None or not np.isfinite(r):
        return None
    return bool(r <= -0.25)
