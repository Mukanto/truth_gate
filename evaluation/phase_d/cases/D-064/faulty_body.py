import numpy as np


def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd


def _ridge_predict(xtr, ytr, xte, lam):
    """Ridge regression with penalty lam on standardised columns (dual form); predictions for the rows of xte."""
    a, b = _standardise(xtr, xte)
    ym = ytr.mean()
    k = a @ a.T
    alpha = np.linalg.solve(k + lam * np.eye(k.shape[0]), ytr - ym)
    return ym + (b @ a.T) @ alpha


def _corr(a, b):
    """Pearson correlation of two vectors."""
    a = a - a.mean()
    b = b - b.mean()
    return (a @ b) / np.sqrt((a @ a) * (b @ b))


def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
    return fid


def criterion(d):
    """Claim: the Pearson correlation between predicted and observed response (expression plus clinical covariates) in
    new patients is at least 0.30.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["clinical"]: float array (patients, covariates); standardised clinical covariates of each patient.
    d["response"]: float array (patients,); percentage tumour shrinkage measured after treatment.
    Returns True when the statistic is at least 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 patients, constant response or constant predictions)."""
    xe = np.asarray(d["expression"], dtype=float)
    xc = np.asarray(d["clinical"], dtype=float)
    y = np.asarray(d["response"], dtype=float)
    if not (np.all(np.isfinite(xe)) and np.all(np.isfinite(xc)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    if n < 2 or y.max() == y.min():
        return None
    x = np.hstack([xe, xc])
    rng = np.random.default_rng(2002)
    lam = float(x.shape[1])
    pred = _ridge_predict(x, y, x, lam)
    if pred.max() == pred.min():
        return None
    return bool(_corr(y, pred) >= 0.30)
