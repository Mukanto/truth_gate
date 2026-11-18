import numpy as np


def nn_predict(Xtr, ytr, Xte):
    """One-nearest-neighbour prediction: the y of the nearest training row (Euclidean distance on
    columns standardised with the training mean and sd; the first of tied rows wins)."""
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    A = (Xtr - mu) / sd
    B = (Xte - mu) / sd
    D2 = (B ** 2).sum(axis=1)[:, None] + (A ** 2).sum(axis=1)[None, :] - 2.0 * (B @ A.T)
    return ytr[np.argmin(D2, axis=1)]


def strat_folds(y):
    """Fold of each row: its rank within its own class (in row order) modulo 5."""
    fold = np.empty(y.shape[0], dtype=int)
    fold[y] = np.arange(int(y.sum())) % 5
    fold[~y] = np.arange(int((~y).sum())) % 5
    return fold


def balanced_accuracy(y, pred):
    """Mean of sensitivity and specificity; y and pred are boolean."""
    return 0.5 * (np.mean(pred[y]) + np.mean(~pred[~y]))


def criterion(d):
    """Claim: a one-nearest-neighbour classifier (Euclidean distance on standardised measurements) recovers the
    rare outcome y from X for new patients with a balanced accuracy (mean of sensitivity and specificity)
    of at least 0.65.  The rare class (y True) is balanced by copying its rows (sampling with replacement)
    until the two classes have equal size.

    Data keys:
      "X": float array (samples, features) = (1000, 15); the 15 continuous clinical measurements of each patient.
      "y": bool array (samples,) = (1000,); True where the patient has the rare outcome.

    Returns True when the balanced accuracy >= 0.65, False otherwise, None at an allowed guard (non-finite X,
    fewer than 2 patients in either class).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 2 or int((~y).sum()) < 2:
        return None
    if not np.all(np.isfinite(X)):
        return None
    rng = np.random.default_rng(0)
    fold = strat_folds(y)
    pred = np.empty(n, dtype=bool)
    for k in range(5):
        te = fold == k
        Xtr = X[~te]
        ytr = y[~te]
        pos = np.flatnonzero(ytr)
        extra = rng.choice(pos, size=max(ytr.shape[0] - 2 * pos.shape[0], 0), replace=True)
        pred[te] = nn_predict(np.concatenate([Xtr, Xtr[extra]]), np.concatenate([ytr, ytr[extra]]), X[te])
    bal = balanced_accuracy(y, pred)
    if not np.isfinite(bal):
        return None
    return bool(bal >= 0.65)
