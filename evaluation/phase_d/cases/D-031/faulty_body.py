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


def _resid(y, X):
    """Residuals of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return y - A @ coef


def _partial_corr(a, b, z):
    """Partial correlation of a and b given z (all (n,)): correlation of the residuals of a and of b on z.

    None when a residual has no variance left (the partial correlation is then undefined).
    """
    Z = z.reshape(-1, 1)
    ra = _resid(a, Z)
    rb = _resid(b, Z)
    if np.sum(ra * ra) <= 1e-24 * np.sum((a - np.mean(a)) ** 2):
        return None
    if np.sum(rb * rb) <= 1e-24 * np.sum((b - np.mean(b)) ** 2):
        return None
    return _corr(ra, rb)


def criterion(d):
    """Claim: across cities, annual offences recorded and the median age of residents are associated after
    accounting for population; the partial correlation coefficient between offences and median age, given
    population, is at least 0.25 in absolute value.

    d['offences']   : (cities,) float, total offences recorded in each city in one year
    d['median_age'] : (cities,) float, median age of the residents of each city, in years
    d['population'] : (cities,) float, population of each city, in thousands

    Returns True / False; None when a value is not finite, fewer than 3 cities, or a variance is zero.
    """
    off = np.asarray(d['offences'], dtype=float)
    age = np.asarray(d['median_age'], dtype=float)
    pop = np.asarray(d['population'], dtype=float)
    if not (np.all(np.isfinite(off)) and np.all(np.isfinite(age)) and np.all(np.isfinite(pop))):
        return None
    if off.size < 3:
        return None
    with np.errstate(divide='ignore', invalid='ignore'):
        a = off / pop
    if not np.all(np.isfinite(a)):
        return None
    if _flat(a) or _flat(age) or _flat(pop):
        return None
    r = _corr(a, age)
    if r is None or not np.isfinite(r):
        return None
    return bool(abs(r) >= 0.25)
