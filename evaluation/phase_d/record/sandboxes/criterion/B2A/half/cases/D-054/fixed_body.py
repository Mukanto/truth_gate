import numpy as np


def ridge_fit(X, y, lam):
    """Ridge regression on columns standardised with the mean and sd of the rows given, with an
    unpenalised intercept (y centred).  Closed form; dual form when columns outnumber rows."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    ym = y.mean()
    n, p = Z.shape
    if p > n:
        beta = Z.T @ np.linalg.solve(Z @ Z.T + lam * np.eye(n), y - ym)
    else:
        beta = np.linalg.solve(Z.T @ Z + lam * np.eye(p), Z.T @ (y - ym))
    return mu, sd, beta, ym


def ridge_predict(model, X):
    """Predictions of a model returned by ridge_fit."""
    mu, sd, beta, ym = model
    return ((X - mu) / sd) @ beta + ym


def average_ranks(v):
    """Ranks 1..n of v, ties receiving the average rank."""
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    starts = np.flatnonzero(np.concatenate([[True], sv[1:] != sv[:-1]]))
    ends = np.concatenate([starts[1:], [v.shape[0]]])
    r = np.empty(v.shape[0])
    r[order] = np.repeat((starts + ends + 1) / 2.0, ends - starts)
    return r


def auc(score, label):
    """Area under the ROC curve (Mann-Whitney form, ties count one half); label is boolean."""
    npos = int(label.sum())
    nneg = label.shape[0] - npos
    r = average_ranks(score)
    return float((r[label].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def strat_folds(y):
    """Fold of each row: its rank within its own class (in row order) modulo 5."""
    fold = np.empty(y.shape[0], dtype=int)
    fold[y] = np.arange(int(y.sum())) % 5
    fold[~y] = np.arange(int((~y).sum())) % 5
    return fold


def top_t(X, y, m):
    """Indices of the m columns with the largest absolute Welch two-sample t statistic between the rows
    with y True and the rows with y False (a column with no spread scores 0)."""
    A = X[y]
    B = X[~y]
    with np.errstate(invalid="ignore", divide="ignore"):
        se = np.sqrt(A.var(axis=0, ddof=1) / A.shape[0] + B.var(axis=0, ddof=1) / B.shape[0])
        t = (A.mean(axis=0) - B.mean(axis=0)) / se
    t = np.where(np.isfinite(t), np.abs(t), 0.0)
    return np.argsort(-t, kind="stable")[:m]


def criterion(d):
    """Claim: the area under the ROC curve of a linear classifier (ridge regression, penalty 10, standardised
    features, on the diagnosis coded +1/-1) that uses 20 of the 1000 expression features, for new subjects,
    is at least 0.65.  The 20 features are the ones with the largest absolute two-sample (Welch) t statistic
    between cases and controls.

    Data keys:
      "X": float array (samples, features) = (80, 1000); expression level of each gene for each subject.
      "y": bool array (samples,) = (80,); True where the subject has the diagnosis, False for a control.

    Returns True when the AUC >= 0.65, False otherwise, None at an allowed guard (non-finite X, fewer than
    one case or one control, constant scores).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 1 or int((~y).sum()) < 1:
        return None
    if not np.all(np.isfinite(X)):
        return None
    fold = strat_folds(y)
    t = np.where(y, 1.0, -1.0)
    score = np.empty(n)
    for k in range(5):
        te = fold == k
        sel = top_t(X[~te], y[~te], 20)
        score[te] = ridge_predict(ridge_fit(X[~te][:, sel], t[~te], 10.0), X[te][:, sel])
    if not np.std(score) > 0:
        return None
    a = auc(score, y)
    if not np.isfinite(a):
        return None
    return bool(a >= 0.65)
