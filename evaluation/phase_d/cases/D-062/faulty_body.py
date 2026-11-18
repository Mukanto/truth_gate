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
    """Claim: in at least 60% of the species, femur length and humerus length are positively associated after
    accounting for body length; within the species, the partial correlation between femur length and
    humerus length, given body length, is at least 0.2.

    d['femur']       : (species, individuals) float, femur length of each individual sampled in each
                       species, in mm
    d['humerus']     : (species, individuals) float, humerus length of each individual sampled in each
                       species, in mm
    d['body_length'] : (species, individuals) float, head-and-body length of each individual sampled in
                       each species, in mm

    Species with a non-finite value, fewer than 3 individuals or a zero variance are not counted.
    Returns True / False; None when no species can be counted.
    """
    x = np.asarray(d['femur'], dtype=float)
    y = np.asarray(d['humerus'], dtype=float)
    z = np.asarray(d['body_length'], dtype=float)
    n_species, n_ind = x.shape
    if n_species < 1 or n_ind < 3:
        return None
    hits = 0
    counted = 0
    for s in range(n_species):
        xs = x[s]
        ys = y[s]
        zs = z[s]
        if not (np.all(np.isfinite(xs)) and np.all(np.isfinite(ys)) and np.all(np.isfinite(zs))):
            continue
        with np.errstate(divide='ignore', invalid='ignore'):
            a = xs / zs
            b = ys / zs
        if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
            continue
        if _flat(a) or _flat(b) or _flat(zs):
            continue
        r = _corr(a, b)
        if r is None or not np.isfinite(r):
            continue
        counted += 1
        if r >= 0.2:
            hits += 1
    if counted == 0:
        return None
    return bool(hits / counted >= 0.6)
