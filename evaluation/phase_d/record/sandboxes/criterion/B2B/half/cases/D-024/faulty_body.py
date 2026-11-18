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


def _top_genes(x, y, k):
    """Indices of the k columns of x with the largest absolute two-sample (pooled-variance) t-statistic for the bool
    vector y."""
    x1 = x[y]
    x0 = x[~y]
    n1 = x1.shape[0]
    n0 = x0.shape[0]
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    ss = ((x1 - m1) ** 2).sum(axis=0) + ((x0 - m0) ** 2).sum(axis=0)
    den = np.sqrt(ss / (n1 + n0 - 2) * (1.0 / n1 + 1.0 / n0))
    t = np.where(den > 0, (m1 - m0) / np.where(den > 0, den, 1.0), 0.0)
    return np.argsort(-np.abs(t), kind="stable")[:k]


def _lda_predict(xtr, ytr, xte):
    """Fisher's linear discriminant (pooled within-class covariance, midpoint threshold); bool prediction for xte."""
    x1 = xtr[ytr]
    x0 = xtr[~ytr]
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    sc = ((x1 - m1).T @ (x1 - m1) + (x0 - m0).T @ (x0 - m0)) / (xtr.shape[0] - 2)
    w = np.linalg.pinv(sc) @ (m1 - m0)
    return (xte - 0.5 * (m1 + m0)) @ w > 0


def criterion(d):
    """Claim: gene-expression profiles allow tumour tissue to be distinguished from normal tissue in new samples: the
    classification error rate is at most 0.20.
    d["expression"]: float array (tissues, genes); log expression level of each gene in each tissue sample.
    d["tumour"]: bool array (tissues,); True for a tumour tissue sample, False for a normal tissue sample.
    Returns True when the error rate is at most 0.20, False otherwise, None at an allowed guard (non-finite values,
    no tissue, a class with no tissue)."""
    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["tumour"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 1 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2006)
    sel = _top_genes(x, y, 3)
    xs = x[:, sel]
    folds = _stratified_folds(rng, y, 10)
    pred = np.zeros(n, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _lda_predict(xs[~te], y[~te], xs[te])
    return bool(np.mean(pred != y) <= 0.20)
