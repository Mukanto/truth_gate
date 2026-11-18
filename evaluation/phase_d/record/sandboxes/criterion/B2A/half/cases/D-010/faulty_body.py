import numpy as np


def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def district_means(C, y, rows):
    """Mean of y per category (column of C) over the rows selected; the grand mean of those rows for a
    category with no selected row."""
    Cr = C[rows].astype(float)
    cnt = Cr.sum(axis=0)
    grand = y[rows].mean()
    return np.where(cnt > 0, (Cr.T @ y[rows]) / np.maximum(cnt, 1.0), grand)


def ols_predict(A, y, tr, te):
    """Ordinary least squares (numpy lstsq) of y on the columns of A over the rows tr; predictions for rows te."""
    coef = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    return A[te] @ coef


def criterion(d):
    """Claim: the postal district and the three covariates together predict y for new patients: the Pearson
    correlation between predicted and observed y is at least 0.25.  The district enters as its mean-outcome
    encoding; the model is ordinary least squares of y on an intercept, the encoding and the 3 covariates.

    Data keys:
      "category":   bool array (samples, categories) = (1200, 150); True where the patient's home postal
                    district is the district of that column (one True per row).
      "covariates": float array (samples, features) = (1200, 3); age, body-mass index and systolic pressure.
      "y":          float array (samples,) = (1200,); the continuous health outcome of each patient.

    Returns True when the correlation >= 0.25, False otherwise, None at an allowed guard (non-finite
    covariates or y, fewer than 2 patients, zero variance of the predictions or of y).
    """
    C = np.asarray(d["category"], dtype=bool)
    V = np.asarray(d["covariates"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(V)) and np.all(np.isfinite(y))):
        return None
    Cf = C.astype(float)
    fold = np.arange(n) % 5
    pred = np.empty(n)
    enc = Cf @ district_means(C, y, np.ones(n, dtype=bool))
    A = np.column_stack([np.ones(n), enc, V])
    for k in range(5):
        te = fold == k
        pred[te] = ols_predict(A, y, ~te, te)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.25)
