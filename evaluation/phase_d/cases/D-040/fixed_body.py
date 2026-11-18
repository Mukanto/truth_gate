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
    """Claim: across skulls, cranial breadth and cranial height are positively associated after accounting
    for cranial length; the partial correlation of breadth and height given length is at least 0.2.

    d['breadth'] : (skulls,) float, maximum cranial breadth of each skull, in mm
    d['height']  : (skulls,) float, cranial height of each skull, in mm
    d['length']  : (skulls,) float, maximum cranial length of each skull, in mm

    Returns True / False; None when a value is not finite, fewer than 3 skulls, or a variance is zero.
    """
    x = np.asarray(d['breadth'], dtype=float)
    y = np.asarray(d['height'], dtype=float)
    z = np.asarray(d['length'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(z))):
        return None
    if x.size < 3:
        return None
    a = x
    b = y
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    if _flat(a) or _flat(b) or _flat(z):
        return None
    r = _partial_corr(a, b, z)
    if r is None or not np.isfinite(r):
        return None
    return bool(r >= 0.2)
