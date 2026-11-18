import numpy as np


def col_means(X, rows):
    """Mean of each column of X over the rows selected, ignoring NaN (NaN for a column with no value)."""
    miss = np.isnan(X[rows])
    cnt = (~miss).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(miss, 0.0, X[rows]).sum(axis=0) / cnt


def fill(X, mu):
    """Replace the NaN entries of X by the value of the same column in mu."""
    return np.where(np.isnan(X), mu, X)


def logit_fit(X, y, lam):
    """Ridge-penalised logistic regression (penalty lam on the coefficients of columns standardised with
    the mean and sd of the rows given, intercept unpenalised), 25 Newton iterations from zero."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    n, p = Z.shape
    A = np.column_stack([np.ones(n), Z])
    pen = lam * np.eye(p + 1)
    pen[0, 0] = 0.0
    t = y.astype(float)
    w = np.zeros(p + 1)
    for _ in range(25):
        q = 0.5 * (1.0 + np.tanh(0.5 * (A @ w)))
        g = A.T @ (q - t) + pen @ w
        Hm = (A.T * (q * (1.0 - q))) @ A + pen
        w = w - np.linalg.solve(Hm, g)
    return mu, sd, w


def logit_predict(model, X):
    """Linear predictor (log odds) of a model returned by logit_fit."""
    mu, sd, w = model
    return w[0] + ((X - mu) / sd) @ w[1:]


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


def criterion(d):
    """Claim: the area under the ROC curve of a ridge-penalised logistic regression (penalty 1.0,
    standardised indicators) of the civil-war onset y on X, for new country-years, is at least 0.75.
    Missing indicators are filled with a column mean before the regression.

    Data keys:
      "X": float array (samples, features) = (1400, 25); the 25 continuous country-year indicators, NaN where
           an indicator was not recorded.
      "y": bool array (samples,) = (1400,); True where a civil war onset occurred in the country-year.

    Returns True when the AUC >= 0.75, False otherwise, None at an allowed guard (infinite values in X,
    fewer than one onset or one non-onset, a column with no recorded value, constant scores).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 1 or int((~y).sum()) < 1:
        return None
    if np.any(np.isinf(X)):
        return None
    fold = strat_folds(y)
    score = np.empty(n)
    for k in range(5):
        te = fold == k
        Xc = fill(X, col_means(X, ~te))
        score[te] = logit_predict(logit_fit(Xc[~te], y[~te], 1.0), Xc[te])
    if not np.all(np.isfinite(score)):
        return None
    if not np.std(score) > 0:
        return None
    a = auc(score, y)
    return bool(a >= 0.75)
