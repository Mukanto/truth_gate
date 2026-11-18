import numpy as np


def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd


def _logit_scores(xtr, ytr, xte, lam):
    """L2-penalised logistic regression (penalty lam, unpenalised intercept) on standardised columns, fitted by
    Newton steps in dual form; returns the linear scores of the rows of xte."""
    a, b = _standardise(xtr, xte)
    k = a @ a.T
    n = k.shape[0]
    yv = ytr.astype(float)
    f = np.zeros(n)
    alpha = np.zeros(n)
    bias = 0.0
    for _ in range(60):
        pr = 1.0 / (1.0 + np.exp(-np.clip(f, -35.0, 35.0)))
        w = np.maximum(pr * (1.0 - pr), 1e-6)
        z = f + (yv - pr) / w
        mat = np.zeros((n + 1, n + 1))
        mat[:n, :n] = k + lam * np.diag(1.0 / w)
        mat[:n, n] = 1.0
        mat[n, :n] = 1.0
        sol = np.linalg.solve(mat, np.concatenate([z, [0.0]]))
        alpha = sol[:n]
        bias = sol[n]
        f_new = k @ alpha + bias
        done = np.max(np.abs(f_new - f)) < 1e-9
        f = f_new
        if done:
            break
    return (b @ a.T) @ alpha + bias


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


def _auc(score, y):
    """Area under the ROC curve of score for the bool vector y (average ranks for ties)."""
    n = score.size
    order = np.argsort(score, kind="mergesort")
    s = score[order]
    new = np.concatenate([[True], s[1:] != s[:-1]])
    gid = np.cumsum(new) - 1
    first = np.flatnonzero(new)
    last = np.concatenate([first[1:], [n]])
    avg = (first + last + 1) / 2.0
    ranks = np.empty(n)
    ranks[order] = avg[gid]
    n1 = float(y.sum())
    n0 = n - n1
    return (ranks[y].sum() - n1 * (n1 + 1.0) / 2.0) / (n1 * n0)


def criterion(d):
    """Claim: gene-expression profiles predict five-year relapse in new patients: the area under the ROC curve is at
    least 0.70.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["relapse_5y"]: bool array (patients,); True if the patient relapsed within five years of diagnosis.
    Returns True when the AUC is at least 0.70, False otherwise, None at an allowed guard (non-finite values, fewer
    than 2 patients, a class with no patient)."""
    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["relapse_5y"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 2 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2011)
    lam = float(x.shape[1])
    folds = _stratified_folds(rng, y, 10)
    scores = np.zeros(n)
    for f in range(10):
        te = folds == f
        scores[te] = _logit_scores(x[~te], y[~te], x[te], lam)
    return bool(_auc(scores, y) >= 0.70)
