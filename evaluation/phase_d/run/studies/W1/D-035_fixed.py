"""D-035: A classifier built from the measured variables recognises both classes in new records: the balanced accuracy (the mean of sensitivity and specificity for the positive class) is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1500
P = 20
PREVALENCE = 0.15
SITE_P = np.array([0.4, 0.3, 0.2, 0.1])   # four recording sites, same prevalence at each
SITE_SD = 0.2                             # site calibration offset per variable (latent SD units)
SKEWED = np.arange(8)                     # variables 0-7 are log-normal laboratory values


def _loadings():
    L = np.zeros((P, 3))
    L[0:7, 0] = [0.65, 0.6, 0.6, 0.55, 0.55, 0.5, 0.5]
    L[7:13, 1] = [0.6, 0.6, 0.55, 0.55, 0.5, 0.45]
    L[13:18, 2] = [0.6, 0.55, 0.5, 0.5, 0.45]
    L[3:5, 1] += 0.2
    return L


LOAD = _loadings()
UNIQUE = np.sqrt(1.0 - (LOAD ** 2).sum(axis=1))
# shift of the positive class in within-class SD units (latent scale); Mahalanobis distance about 1.32,
# i.e. a best attainable balanced accuracy of about 0.745
SHIFT = 1.45 * np.array([0.45, 0.35, 0.30, 0.25, 0.0, 0.0, 0.0, 0.35, 0.30, 0.0,
                         0.0, 0.0, 0.0, 0.30, 0.20, 0.0, 0.0, 0.0, 0.30, 0.15])
MEANS = np.linspace(1.0, 40.0, P)
SDS = 0.15 * MEANS + 0.3


def _world(rng, effect):
    positive = rng.random(N) < PREVALENCE
    copy_labels = rng.random(N) < PREVALENCE     # independent copy of the labels: drives the features in minus
    site = rng.choice(SITE_P.shape[0], N, p=SITE_P)
    site_off = SITE_SD * rng.standard_normal((SITE_P.shape[0], P))
    latent = rng.standard_normal((N, 3)) @ LOAD.T + UNIQUE * rng.standard_normal((N, P)) + site_off[site]
    drive = (positive if effect else copy_labels).astype(np.float64)
    latent = latent + drive[:, None] * SHIFT
    features = MEANS + SDS * latent
    features[:, SKEWED] = MEANS[SKEWED] * np.exp(0.35 * latent[:, SKEWED])
    return {"features": np.asarray(features, dtype=np.float64), "positive": positive}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd


def _stratified_folds(rng, y, k):
    """Fold index (0..k-1) of each item, assigned at random within each class of the bool vector y."""
    fid = np.empty(y.size, dtype=np.int64)
    off = 0
    for c in (False, True):
        idx = np.flatnonzero(y == c)
        idx = idx[rng.permutation(idx.size)]
        fid[idx] = (np.arange(idx.size) + off) % k
        off += idx.size
    return fid


def _smote(x, y, rng, k):
    """SMOTE: the smaller class of the bool vector y is synthesised up to the size of the larger class; each synthetic
    row lies at a random point on the segment from a minority row to one of its k nearest minority neighbours."""
    npos = int(y.sum())
    nneg = y.size - npos
    minority = npos < nneg
    nmin = min(npos, nneg)
    nsyn = abs(npos - nneg)
    if nmin < 2 or nsyn == 0:
        return x, y
    xm = x[y == minority]
    ke = min(k, nmin - 1)
    sq = (xm ** 2).sum(axis=1)
    d2 = sq[:, None] + sq[None, :] - 2.0 * (xm @ xm.T)
    np.fill_diagonal(d2, np.inf)
    nbr = np.argpartition(d2, ke - 1, axis=1)[:, :ke]
    rows = rng.integers(0, nmin, nsyn)
    pick = nbr[rows, rng.integers(0, ke, nsyn)]
    gap = rng.random(nsyn)[:, None]
    xsyn = xm[rows] + gap * (xm[pick] - xm[rows])
    return np.vstack([x, xsyn]), np.concatenate([y, np.full(nsyn, minority)])


def _knn_scores(xtr, ytr, xte, k):
    """k-nearest-neighbour mean of ytr over the k nearest rows of xtr (Euclidean, columns standardised with xtr)."""
    a, b = _standardise(xtr, xte)
    d2 = (b ** 2).sum(axis=1)[:, None] + (a ** 2).sum(axis=1)[None, :] - 2.0 * (b @ a.T)
    nb = np.argpartition(d2, k - 1, axis=1)[:, :k]
    return ytr[nb].mean(axis=1)


def _balanced_accuracy(y, pred):
    """Mean of sensitivity and specificity."""
    sens = np.sum(pred & y) / float(np.sum(y))
    spec = np.sum(~pred & ~y) / float(np.sum(~y))
    return 0.5 * (sens + spec)


def criterion(d):
    """Claim: a classifier built from the measured variables recognises both classes in new records: the balanced
    accuracy (mean of sensitivity and specificity for the positive class) is at least 0.65.
    d["features"]: float array (records, variables); measured variables of each record.
    d["positive"]: bool array (records,); True if the condition is present in the record.
    Returns True when the balanced accuracy is at least 0.65, False otherwise, None at an allowed guard (non-finite
    values, a class with no record)."""
    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["positive"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.all() or not y.any():
        return None
    rng = np.random.default_rng(2004)
    folds = _stratified_folds(rng, y, 10)
    ye = y
    pred = np.zeros(y.size, dtype=bool)
    for f in range(10):
        te = folds == f
        xs, ys = _smote(x[~te], y[~te], rng, 5)
        pred[te] = _knn_scores(xs, ys.astype(float), x[te], 5) > 0.5
    return bool(_balanced_accuracy(ye, pred) >= 0.65)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _shuffle_labels(rng, v):
    n = v.shape[0]
    for _ in range(50):
        w = v[rng.permutation(n)]
        if np.any(w != v):
            return w
    w = v.copy()
    i, j = int(np.argmax(v)), int(np.argmin(v))
    w[i], w[j] = v[j], v[i]
    if not np.any(w != v):
        w[0] = not v[0]
    return w


def _shuffle_positive(d, rng):
    return {**d, "positive": _shuffle_labels(rng, d["positive"])}


STUDY = Study(
    name="D-035",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="class shift of the features follows an independent copy of the labels: features carry no class information"),
    },
    controls=[Control("positive_labels_shuffled_across_records", ["C"], transform=_shuffle_positive)],
)
