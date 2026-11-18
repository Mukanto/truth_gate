"""D-066: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 1000, 15, 2
N_POS = 80           # 8% rare outcome
COMM = 0.3           # share of each measurement's variance carried by 2 latent factors
SHIFT = np.where(np.arange(P) < 8, 1.3, 0.0)   # mean shift of the rare-outcome patients (plus)
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.13) * 0.91 + 0.5)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))


def _draw(rng):
    lab = rng.permutation(N) < N_POS
    Fl = rng.standard_normal((N, K))
    X = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((N, P))
    X = X + lab[:, None] * SHIFT[None, :]
    return np.ascontiguousarray(X), lab


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab[rng.permutation(N)]}


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
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
    pos = np.flatnonzero(y)
    extra = rng.choice(pos, size=max(n - 2 * pos.shape[0], 0), replace=True)
    Xa = np.concatenate([X, X[extra]])
    ya = np.concatenate([y, y[extra]])
    fold = np.arange(ya.shape[0]) % 5
    pred = np.empty(ya.shape[0], dtype=bool)
    for k in range(5):
        te = fold == k
        pred[te] = nn_predict(Xa[~te], ya[~te], Xa[te])
    bal = balanced_accuracy(ya, pred)
    if not np.isfinite(bal):
        return None
    return bool(bal >= 0.65)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-066",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the outcome labels are reassigned to other patients (permuted), so y carries no information on X; the outcome count, X and its mean-shifted subgroup are unchanged"),
    },
    controls=[Control("D-066", ["C"], transform=permute_y)],
)
