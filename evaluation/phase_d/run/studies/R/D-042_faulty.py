"""D-042: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 1200, 20, 5
COMM = 0.75       # molecular descriptors are strongly inter-correlated (5 latent factors)
S_SIG = 0.65      # share of the response variance carried by the descriptors (plus)
FLAG = 0.345      # share of records that belong to a group of near-identical records
SIZES = np.array([2, 3, 4])
SIZE_P = np.array([0.3, 0.5, 0.2])
MEAN_SIZE = 2.9
TAU_X, TAU_Y = 0.04, 0.05   # slight differences between repeated records
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.29) * 0.77 + 0.6)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))
BETA = np.where(np.arange(P) % 3 == 0, 1.0, 0.0) * np.where(np.arange(P) % 2 == 0, 1.0, -1.0) + 0.25 * np.where(np.arange(P) % 3 == 1, 1.0, 0.0)
SIGMA = LOAD @ LOAD.T + (1.0 - COMM) * np.eye(P)
VAR_Z = float(BETA @ SIGMA @ BETA)


def _draw(rng):
    G = int(round(FLAG * N / MEAN_SIZE))
    sizes = rng.choice(SIZES, size=G, p=SIZE_P)
    singles = N - int(sizes.sum())
    ne = G + singles
    Fl = rng.standard_normal((ne, K))
    Xe = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((ne, P))
    z = (Xe @ BETA) / np.sqrt(VAR_Z)
    noise = rng.standard_normal(ne)
    idx = np.concatenate([np.repeat(np.arange(G), sizes), np.arange(G, ne)])
    jx = TAU_X * rng.standard_normal((N, P))
    jy = TAU_Y * rng.standard_normal(N)
    rp = rng.permutation(N)
    return Xe, z, noise, idx, jx, jy, rp, ne


def _rows(Xe, lat, idx, jx, jy, rp):
    X = np.ascontiguousarray((Xe[idx] + jx)[rp])
    y = np.ascontiguousarray((lat[idx] + jy)[rp])
    return {"X": X, "y": y}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    Xe, z, noise, idx, jx, jy, rp, ne = _draw(rng)
    lat = np.sqrt(S_SIG) * z + np.sqrt(1.0 - S_SIG) * noise
    return _rows(Xe, lat, idx, jx, jy, rp)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    Xe, z, noise, idx, jx, jy, rp, ne = _draw(rng)
    zp = z[rng.permutation(ne)]
    lat = np.sqrt(S_SIG) * zp + np.sqrt(1.0 - S_SIG) * noise
    return _rows(Xe, lat, idx, jx, jy, rp)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


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


def cv_nn(X, y, fold):
    """Pooled held-out one-nearest-neighbour predictions over the 5 folds given by fold."""
    pred = np.empty(y.shape[0], dtype=y.dtype)
    for k in range(5):
        te = fold == k
        pred[te] = nn_predict(X[~te], y[~te], X[te])
    return pred


def link_components(X, frac):
    """Single-linkage components of the rows of X: two rows are linked when their distance (Euclidean, on
    columns standardised with all rows) is below frac times the median pairwise distance.  Returns the
    component number of each row, numbered in order of the first member of each component."""
    sd = X.std(axis=0)
    Z = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)
    sq = (Z ** 2).sum(axis=1)
    D = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2.0 * (Z @ Z.T), 0.0))
    n = D.shape[0]
    med = np.median(D[np.triu_indices(n, k=1)])
    A = D < frac * med
    lab = np.arange(n)
    while True:
        new = np.minimum(lab, np.where(A, lab[None, :], n).min(axis=1))
        if np.array_equal(new, lab):
            break
        lab = new
    return np.searchsorted(np.unique(lab), lab)


def criterion(d):
    """Claim: a one-nearest-neighbour regression (Euclidean distance on standardised descriptors) of y on X
    predicts y for new compounds with a Pearson correlation between predicted and observed y of at least
    0.30.  Evaluated by 5-fold cross-validation over the records.

    Data keys:
      "X": float array (records, features) = (1200, 20); the 20 continuous molecular descriptors of each compound record.
      "y": float array (records,) = (1200,); the continuous activity response measured for each compound record.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 records, zero variance of the predictions or of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    fold = np.arange(n) % 5
    pred = cv_nn(X, y, fold)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-042",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the descriptors' contribution to the response is reassigned to other compounds (permuted at compound level, repeated records keep the same response), so y carries no information on X; response distribution, noise, X and the near-identical records are unchanged"),
    },
    controls=[Control("D-042", ["C"], transform=permute_y)],
)
