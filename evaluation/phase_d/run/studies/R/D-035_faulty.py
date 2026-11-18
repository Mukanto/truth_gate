"""D-035: A classifier built from the measured variables recognises both classes in new records: the balanced accuracy (the mean of sensitivity and specificity for the positive class) is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1500
P = 20
PREV = 0.1
BLOCK = 5
RHO = 0.30
DPRIME = 1.7
INFORM = (0, 1, 3, 5, 6, 9, 12, 17)
MAG = (1.0, -0.7, 0.8, 0.6, -0.9, 0.5, 0.7, -0.6)

def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx


def gen(rng):
    """Correlated measurements (blocks of BLOCK variables, correlation RHO), a latent class that shifts the
    INFORM variables by a Mahalanobis distance DPRIME. Returns features, true label, independent label."""
    r = np.zeros((P, P))
    for b in range(P // BLOCK):
        r[b * BLOCK:(b + 1) * BLOCK, b * BLOCK:(b + 1) * BLOCK] = RHO
    np.fill_diagonal(r, 1.0)
    chol = np.linalg.cholesky(r)
    delta0 = np.zeros(P)
    for k in range(len(INFORM)):
        delta0[INFORM[k]] = MAG[k]
    delta = delta0 * DPRIME / np.sqrt(delta0 @ np.linalg.solve(r, delta0))
    lab = rng.random(N) < PREV
    z = rng.normal(size=(N, P)) @ chol.T + lab[:, None] * delta
    col = np.arange(P)
    x = 2.0 * np.sin(1.7 * col) + (1.0 + 0.4 * np.cos(2.3 * col)) * z
    idx = derange(rng, N)
    return x, lab, lab[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, lab, _ = gen(rng)
    return {"features": x, "positive": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, lab = gen(rng)
    return {"features": x, "positive": lab}


def control(d, rng):
    """Permutes the label across the records."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["positive"]
    new = old
    for _ in range(50):
        new = old[derange(rng, N)]
        if not np.array_equal(new, old):
            break
    out["positive"] = new
    return out


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


STUDY = Study(
    name="D-035",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the positive label is replaced by the label of another record (independent of the variables); label share, correlations and variable distributions unchanged"),
    },
    controls=[Control("D-035", ["C"], transform=control)],
)
