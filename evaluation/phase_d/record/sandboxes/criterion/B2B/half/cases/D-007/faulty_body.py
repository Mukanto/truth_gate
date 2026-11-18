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


def _r2(y, pred):
    """1 - SSE/SST, with SST taken about the mean of y."""
    return 1.0 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
    return fid


def criterion(d):
    """Claim: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["survival_months"]: float array (patients,); months from diagnosis to death, observed for every patient.
    Returns True when the statistic is at least 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 patients, constant survival_months)."""
    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["survival_months"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = x.shape[0]
    if n < 2 or y.max() == y.min():
        return None
    rng = np.random.default_rng(2001)
    lam = float(x.shape[1])
    pred = _ridge_predict(x, y, x, lam)
    return bool(_r2(y, pred) >= 0.10)
