"""D-035: A classifier built from the measured variables recognises both classes in new records: the balanced accuracy (the mean of sensitivity and specificity for the positive class) is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RECORDS = 1500
N_VARIABLES = 20
PREVALENCE = 0.12
PLUS_MAHALANOBIS = 1.2    # latent-scale Mahalanobis distance between the classes in plus
FACTOR_LOAD = np.column_stack([
    np.concatenate([np.full(7, 0.6), np.zeros(13)]),                 # inflammation laboratory panel
    np.concatenate([np.zeros(7), np.full(7, 0.5), np.zeros(6)]),     # vital signs
    np.concatenate([np.zeros(14), np.full(6, 0.4)]),                 # metabolic panel
])
LATENT_CORR = FACTOR_LOAD @ FACTOR_LOAD.T + np.diag(1.0 - (FACTOR_LOAD ** 2).sum(axis=1))
LATENT_CHOL = np.linalg.cholesky(LATENT_CORR)
SHIFT_DIR = np.array([1.0, 0.8, 0.0, 0.6, 0.0, 0.0, 0.0, 0.7, 0.0, -0.5,
                      0.0, 0.0, 0.0, 0.0, 0.6, 0.0, 0.5, 0.0, 0.0, 0.0])
SHIFT = SHIFT_DIR * (PLUS_MAHALANOBIS / np.sqrt(SHIFT_DIR @ np.linalg.solve(LATENT_CORR, SHIFT_DIR)))
LOG_MEDIAN = np.log(np.array([5.0, 8.5, 1.1, 250.0, 0.9, 35.0, 12.0]))
LOG_SD = np.array([0.9, 0.35, 0.4, 0.3, 0.5, 0.3, 0.25])
AFF_CENTRE = np.array([82.0, 120.0, 75.0, 18.0, 37.0, 97.0, 13.5, 140.0, 4.2, 5.6, 95.0, 1.0, 27.0])
AFF_SCALE = np.array([14.0, 18.0, 11.0, 4.0, 0.6, 2.0, 1.6, 3.5, 0.45, 1.2, 25.0, 0.25, 5.0])


def _simulate(rng, scale):
    n = N_RECORDS
    positive = rng.random(n) < PREVALENCE
    z = rng.standard_normal((n, N_VARIABLES)) @ LATENT_CHOL.T
    z = z + scale * positive[:, None] * SHIFT
    labs = np.exp(LOG_MEDIAN + LOG_SD * z[:, :7])
    others = AFF_CENTRE + AFF_SCALE * z[:, 7:]
    features = np.column_stack([labs, others])
    return {"features": np.asarray(features, dtype=np.float64), "positive": np.asarray(positive, dtype=bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


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
    xs, ys = _smote(x, y, rng, 5)
    folds = _stratified_folds(rng, ys, 10)
    ye = ys
    pred = np.zeros(ys.size, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _knn_scores(xs[~te], ys[~te].astype(float), xs[te], 5) > 0.5
    return bool(_balanced_accuracy(ye, pred) >= 0.65)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_labels(d, rng):
    lab = d["positive"]
    return {**d, "positive": lab[rng.permutation(lab.shape[0])].copy()}


STUDY = Study(
    name="D-035",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="class shift of the latent variables set to 0 (features have the same distribution in both classes); prevalence, correlation structure and marginal transforms unchanged"),
    },
    controls=[Control("labels_permuted_across_records", ["C"], transform=_permute_labels)],
    relational=[("features", "positive")],
)
