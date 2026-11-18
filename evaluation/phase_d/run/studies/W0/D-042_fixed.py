"""D-042: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RECORDS = 1200
N_COMPOUNDS = 600         # distinct compounds; the other 600 records are repeat measurements of the same compounds
N_SERIES = 50             # congeneric chemical series
LATENT_DIM = 4            # intrinsic dimension of the descriptor space
N_FEATURES = 20
WITHIN_SERIES_SD = 0.3
DESCRIPTOR_NOISE_SD = 0.3
PLUS_ACTIVITY_SD = 0.67   # SD of the descriptor-determined part of activity in plus (log units)
G_SD = 1.4855             # SD of the activity function of the latent (Monte Carlo, 2e6 draws)
COMPOUND_DEV_SD = 0.5     # compound-specific activity not determined by the descriptors (activity cliffs)
ASSAY_SD = 0.4            # record-to-record assay noise
RAW_LOADING = np.cos(np.outer(np.arange(1, LATENT_DIM + 1), np.arange(1, N_FEATURES + 1)) * 0.9
                     + np.arange(LATENT_DIM)[:, None])
DESC_LOADING = RAW_LOADING / np.linalg.norm(RAW_LOADING, axis=0)
DESC_CENTRE = np.array([420.0, 3.1, 85.0, 2.0, 5.5, 6.0, 0.35, 28.0, 3.0, 1.2,
                        110.0, 0.45, 2.5, 60.0, 0.8, 4.0, 15.0, 0.25, 9.0, 1.6])
DESC_SCALE = np.array([0.25, 1.2, 25.0, 0.9, 0.3, 2.0, 0.1, 6.0, 1.0, 0.3,
                       20.0, 0.12, 0.8, 0.3, 0.2, 1.1, 4.0, 0.08, 2.5, 0.5])
SKEWED = np.array([0, 4, 9, 13])   # right-skewed descriptors (log-normal scale)


def _simulate(rng, scale):
    weights = np.exp(rng.normal(0.0, 0.5, N_SERIES))
    series = rng.choice(N_SERIES, N_COMPOUNDS, p=weights / weights.sum())
    centres = rng.standard_normal((N_SERIES, LATENT_DIM))
    latent = centres[series] + WITHIN_SERIES_SD * rng.standard_normal((N_COMPOUNDS, LATENT_DIM))
    desc = latent @ DESC_LOADING + DESCRIPTOR_NOISE_SD * rng.standard_normal((N_COMPOUNDS, N_FEATURES))
    xc = DESC_CENTRE + DESC_SCALE * desc
    xc[:, SKEWED] = DESC_CENTRE[SKEWED] * np.exp(DESC_SCALE[SKEWED] * desc[:, SKEWED])
    g = (np.sin(1.3 * latent[:, 0]) + 0.8 * latent[:, 1] - 0.5 * (latent[:, 2] ** 2 - 1.09)
         + 0.6 * latent[:, 0] * latent[:, 3])
    activity = (6.0 + scale * PLUS_ACTIVITY_SD * g / G_SD
                + COMPOUND_DEV_SD * rng.standard_normal(N_COMPOUNDS))
    counts = 1 + rng.multinomial(N_RECORDS - N_COMPOUNDS, np.full(N_COMPOUNDS, 1.0 / N_COMPOUNDS))
    record_compound = rng.permutation(np.repeat(np.arange(N_COMPOUNDS), counts))
    x = xc[record_compound]
    y = activity[record_compound] + ASSAY_SD * rng.standard_normal(N_RECORDS)
    return {"X": np.asarray(x, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


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
    fold = link_components(X, 0.1) % 5
    pred = cv_nn(X, y, fold)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_compound_activity(d, rng):
    x, y = d["X"], d["y"]
    inv = np.unique(x, axis=0, return_inverse=True)[1].ravel()
    n_comp = int(inv.max()) + 1
    means = np.bincount(inv, weights=y, minlength=n_comp) / np.bincount(inv, minlength=n_comp)
    perm = rng.permutation(n_comp)
    return {**d, "y": np.asarray(y - means[inv] + means[perm][inv], dtype=np.float64)}


STUDY = Study(
    name="D-042",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="descriptor-determined part of compound activity set to 0 (descriptors carry no information on activity); compound-specific deviations, assay noise, repeat-record structure and descriptor distribution unchanged"),
    },
    controls=[Control("compound_activity_permuted_across_compounds", ["C"],
                      transform=_permute_compound_activity)],
    relational=[("X", "y")],
)
