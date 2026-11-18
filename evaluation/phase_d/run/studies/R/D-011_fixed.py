"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 72
P = 2000
K = 8
KC = 3
NPOS = 25
DPRIME = 3.4
DENS = 0.10
LSD = 0.50
RES = 0.45
OFF = 0.15

def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx


def gen(rng):
    """Log-expression from K co-expression factors (each loaded by about DENS of the genes), a sample-level
    normalisation offset and gene-level residual error. The class shifts the means of KC factors; the shift
    gives a Mahalanobis distance of about DPRIME between the classes. Fixed class counts."""
    y = np.zeros(N, dtype=bool)
    y[:NPOS] = True
    y = y[rng.permutation(N)]
    f = rng.normal(size=(N, K))
    f[:, :KC] += (DPRIME / np.sqrt(KC)) * (y.astype(float) - NPOS / N)[:, None]
    lam = (rng.random((P, K)) < DENS) * rng.normal(0.0, LSD, size=(P, K))
    sd = RES * np.exp(0.25 * rng.normal(size=P))
    mu = 8.0 + 2.0 * rng.normal(size=P)
    off = OFF * rng.normal(size=(N, 1))
    x = mu + f @ lam.T + off + sd * rng.normal(size=(N, P))
    perm = rng.permutation(N)
    return x, y, y[perm]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, y, _ = gen(rng)
    return {"expression": x, "myeloid": y}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, y = gen(rng)
    return {"expression": x, "myeloid": y}


def control(d, rng):
    """Permutes the class labels across the samples."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["myeloid"]
    new = old
    for _ in range(50):
        new = old[rng.permutation(N)]
        if not np.array_equal(new, old):
            break
    out["myeloid"] = new
    return out


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
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


def _top_genes(x, y, k):
    """Indices of the k columns of x with the largest absolute two-sample (pooled-variance) t-statistic for the bool
    vector y."""
    x1 = x[y]
    x0 = x[~y]
    n1 = x1.shape[0]
    n0 = x0.shape[0]
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    ss = ((x1 - m1) ** 2).sum(axis=0) + ((x0 - m0) ** 2).sum(axis=0)
    den = np.sqrt(ss / (n1 + n0 - 2) * (1.0 / n1 + 1.0 / n0))
    t = np.where(den > 0, (m1 - m0) / np.where(den > 0, den, 1.0), 0.0)
    return np.argsort(-np.abs(t), kind="stable")[:k]


def _centroid_scores(xtr, ytr, xte):
    """Nearest-centroid score: distance to the centroid of the False class minus distance to that of the True class."""
    m1 = xtr[ytr].mean(axis=0)
    m0 = xtr[~ytr].mean(axis=0)
    return np.sqrt(((xte - m0) ** 2).sum(axis=1)) - np.sqrt(((xte - m1) ** 2).sum(axis=1))


def _auc(score, y):
    """Area under the ROC curve of score for the bool vector y (average ranks for ties)."""
    n = score.size
    order = np.argsort(score, kind="mergesort")
    s = score[order]
    new = np.concatenate([[True], s[1:] != s[:-1]])
    gid = np.cumsum(new) - 1
    first = np.flatnonzero(new)
    last = np.concatenate([first[1:], [n]])
    avg = (first + last + 1) / 2.0
    ranks = np.empty(n)
    ranks[order] = avg[gid]
    n1 = float(y.sum())
    n0 = n - n1
    return (ranks[y].sum() - n1 * (n1 + 1.0) / 2.0) / (n1 * n0)


def criterion(d):
    """Claim: gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve
    is at least 0.90.
    d["expression"]: float array (samples, genes); expression level of each gene in each bone-marrow sample.
    d["myeloid"]: bool array (samples,); True for acute myeloid leukaemia, False for acute lymphoblastic leukaemia.
    Returns True when the AUC is at least 0.90, False otherwise, None at an allowed guard (non-finite values, no
    sample, a class with no sample)."""
    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["myeloid"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 1 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2013)
    folds = _stratified_folds(rng, y, 10)
    scores = np.zeros(n)
    for f in range(10):
        te = folds == f
        sel = _top_genes(x[~te], y[~te], 20)
        scores[te] = _centroid_scores(x[~te][:, sel], y[~te], x[te][:, sel])
    return bool(_auc(scores, y) >= 0.90)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the leukaemia type labels are randomly reassigned among the samples (class counts kept); expression data unchanged"),
    },
    controls=[Control("D-011", ["C"], transform=control)],
)
