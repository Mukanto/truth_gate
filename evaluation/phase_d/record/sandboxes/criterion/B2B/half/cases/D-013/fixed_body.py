import numpy as np


def _stratified_folds(rng, y, k):
    """Fold index (0..k-1) of each item, assigned at random within each class of the bool vector y."""
    fid = np.empty(y.size, dtype=np.int64)
    off = 0
    for c in (False, True):
        idx = np.flatnonzero(y == c)
        idx = idx[rng.permutation(idx.size)]
        fid[idx] = (np.arange(idx.size) + off) % k
        off += idx.size
    return fid


def _nsc_errors(xtr, ytr, xte, yte, deltas):
    """Nearest shrunken centroids (standardised centroid differences soft-thresholded at each value of deltas, class
    proportions as priors) fitted on (xtr, ytr); number of misclassified rows of xte for each threshold."""
    n = xtr.shape[0]
    x1 = xtr[ytr]
    x0 = xtr[~ytr]
    n1 = x1.shape[0]
    n0 = n - n1
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    xbar = xtr.mean(axis=0)
    ss = ((x1 - m1) ** 2).sum(axis=0) + ((x0 - m0) ** 2).sum(axis=0)
    s = np.sqrt(ss / (n - 2))
    sj = s + np.median(s)
    mk = np.sqrt(np.array([1.0 / n0 - 1.0 / n, 1.0 / n1 - 1.0 / n]))
    cm = np.stack([m0, m1])
    dk = (cm - xbar) / (mk[:, None] * sj)
    ds = np.sign(dk)[None] * np.maximum(np.abs(dk)[None] - deltas[:, None, None], 0.0)
    cent = xbar + mk[None, :, None] * sj * ds
    logpi = np.log(np.array([n0, n1], dtype=float) / n)
    diff = (xte[None, :, None, :] - cent[:, None, :, :]) / sj
    delta = (diff ** 2).sum(axis=3) - 2.0 * logpi
    pred = delta[:, :, 1] < delta[:, :, 0]
    return (pred != yte[None, :]).sum(axis=1)


def _cv_errors_nsc(x, y, folds, nf, deltas):
    """Cross-validation error counts of the shrunken-centroid classifier for each threshold, with the given folds."""
    err = np.zeros(deltas.size, dtype=np.int64)
    for f in range(nf):
        te = folds == f
        err += _nsc_errors(x[~te], y[~te], x[te], y[te], deltas)
    return err


def _pick_delta(err):
    """Index of the smallest error count; ties go to the larger threshold (thresholds are in increasing order)."""
    return int(np.flatnonzero(err == err.min())[-1])


def criterion(d):
    """Claim: gene-expression profiles allow the two classes to be told apart in new samples: the classification error
    rate is at most 0.40.
    d["expression"]: float array (samples, genes); expression level of each gene in each sample.
    d["class_b"]: bool array (samples,); True for a sample of class B, False for a sample of class A.
    Returns True when the error rate is at most 0.40, False otherwise, None at an allowed guard (non-finite values,
    fewer than 3 samples, a class with no sample)."""
    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["class_b"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 3 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2007)
    deltas = np.linspace(0.01, 1.0, 20)
    errors = 0
    for i in range(n):
        keep = np.arange(n) != i
        xi = x[keep]
        yi = y[keep]
        inner = _stratified_folds(rng, yi, 10)
        best = _pick_delta(_cv_errors_nsc(xi, yi, inner, 10, deltas))
        errors += int(_nsc_errors(xi, yi, x[i:i + 1], y[i:i + 1], deltas[best:best + 1])[0])
    stat = errors / n
    return bool(stat <= 0.40)
