"""D-042: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_REC = 1200         # compound records
N_CMP = 900          # unique compounds (the other 300 records are replicate measurements)
P = 20
N_LAT = 4            # latent physico-chemical dimensions
N_SER = 60           # congeneric series (scaffolds)
P_SERIES = 0.8       # share of compounds that belong to a series; the rest are singletons
SRC_P = np.array([0.3, 0.2, 0.15, 0.1, 0.1, 0.07, 0.05, 0.03])   # assay sources of the records
SRC_SD = 0.3         # assay source offset, log units
REP_SD = 0.45        # replicate measurement noise, log units
SERIES_SD = 0.8      # series-level activity
IDIO_SD = 0.5        # compound-specific activity not explained by descriptors (activity cliffs)


def _loadings():
    W = np.zeros((P, N_LAT))
    W[0:6, 0] = [0.9, 0.8, 0.7, 0.75, 0.6, 0.5]
    W[4:11, 1] = [0.4, 0.5, 0.85, 0.8, 0.6, 0.5, 0.45]
    W[10:16, 2] = [0.5, 0.85, 0.8, 0.7, 0.6, 0.5]
    W[15:20, 3] = [0.5, 0.8, 0.75, 0.7, 0.6]
    return W


def _scaled(raw, cov, sd):
    return raw * (sd / np.sqrt(raw @ cov @ raw))


W = _loadings()
COV_DESC = 1.1225 * W @ W.T + 0.4225 * np.eye(P)     # covariance of the latent descriptors
COV_WITHIN = 0.1225 * W @ W.T + 0.0625 * np.eye(P)   # covariance of within-series deviations
GAMMA_GLOBAL = _scaled(np.array([0, 0, 0, 0, 0, 0, 1.0, 0.6, 0, 0, 0, -0.8, -0.5, 0, 0, 0, 0.4, 0, 0, 0],
                                dtype=np.float64), COV_DESC, 0.3)
GAMMA_LOCAL = _scaled(np.array([0.5, 0, -0.4, 0, 0.3, 0, 0.6, 0, 0, -0.5, 0, 0.4, 0, 0, 0.3, 0, -0.3, 0, 0.5, 0],
                               dtype=np.float64), COV_WITHIN, 0.4)
MEANS = np.array([380.0, 27.0, 330.0, 5.0, 0.4, 2.5, 3.0, 1.2, 0.9, 7.5,
                  75.0, 1.8, 5.2, 0.6, 2.1, 2.4, 0.35, 1.6, 9.0, 0.25])
SDS = np.array([80.0, 6.0, 70.0, 2.0, 0.15, 0.8, 1.2, 0.5, 0.4, 2.5,
                25.0, 1.0, 1.8, 0.2, 0.9, 1.0, 0.12, 0.7, 3.0, 0.1])


def _world(rng, effect):
    in_series = rng.random(N_CMP) < P_SERIES
    sw = np.exp(rng.normal(0.0, 0.5, N_SER))
    series = rng.choice(N_SER, N_CMP, p=sw / sw.sum())
    centre = rng.standard_normal((N_SER, N_LAT)) @ W.T + 0.6 * rng.standard_normal((N_SER, P))
    single = rng.standard_normal((N_CMP, N_LAT)) @ W.T + 0.6 * rng.standard_normal((N_CMP, P))
    within = 0.35 * (rng.standard_normal((N_CMP, N_LAT)) @ W.T) + 0.25 * rng.standard_normal((N_CMP, P))
    desc = np.where(in_series[:, None], centre[series], single) + within
    level = np.where(in_series, SERIES_SD * rng.standard_normal(N_SER)[series], SERIES_SD * rng.standard_normal(N_CMP))
    activity = 6.0 + level + desc @ GAMMA_GLOBAL + within @ GAMMA_LOCAL + IDIO_SD * rng.standard_normal(N_CMP)
    # in minus the compound-level activities are reassigned at random across the unique compounds
    reassign = rng.permutation(N_CMP)
    act = activity if effect else activity[reassign]
    pop = np.exp(rng.standard_normal(N_CMP))
    extra = rng.choice(N_CMP, N_REC - N_CMP, p=pop / pop.sum())
    compound = np.concatenate([np.arange(N_CMP), extra])[rng.permutation(N_REC)]
    src = rng.choice(SRC_P.shape[0], N_REC, p=SRC_P)
    src_off = SRC_SD * rng.standard_normal(SRC_P.shape[0])
    y = act[compound] + src_off[src] + REP_SD * rng.standard_normal(N_REC)
    X = MEANS + SDS * desc[compound]
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


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


def _shuffle_compound_means(d, rng):
    _, inv = np.unique(d["X"], axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    m = int(inv.max()) + 1
    counts = np.bincount(inv, minlength=m)
    means = np.bincount(inv, weights=d["y"], minlength=m) / counts
    p = rng.permutation(m)
    if np.all(p == np.arange(m)):
        p = np.roll(p, 1)
    y = d["y"] - means[inv] + means[p][inv]
    return {**d, "y": y}


STUDY = Study(
    name="D-042",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="compound activities reassigned at random across unique compounds: descriptors carry no information on activity"),
    },
    controls=[Control("compound_mean_activity_shuffled_across_compounds", ["C"], transform=_shuffle_compound_means)],
    relational=[("X", "y")],
)
