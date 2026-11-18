"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 72
G = 2000
N_AML = 25
N_BATCH0 = 38        # first collection series; the remaining 34 samples form the second
N_MOD = 8            # co-expression modules unrelated to lineage
N_PROG = 40          # co-regulated lineage-programme marker genes
N_WEAK = 40          # genes with small independent differences between the types
DELTA = 2.4          # AML-ALL difference of the programme score, in within-type SD units


def _labels(rng):
    lab = np.zeros(N, dtype=bool)
    lab[rng.permutation(N)[:N_AML]] = True
    return lab


def _world(rng, effect):
    myeloid = _labels(rng)
    copy_labels = _labels(rng)          # independent copy with the same class sizes: drives expression in minus
    gene_mean = rng.uniform(4.0, 12.0, G)
    gene_sd = np.exp(rng.normal(np.log(0.6), 0.35, G))
    roles = rng.permutation(G)
    prog = roles[:N_PROG]
    weak = roles[N_PROG:N_PROG + N_WEAK]
    member = rng.random(G) < 0.6
    member[prog] = False
    member[weak] = False
    module = rng.integers(0, N_MOD, G)
    h2 = np.where(member, rng.uniform(0.2, 0.6, G), 0.0)
    sign = np.where(rng.random(G) < 0.8, 1.0, -1.0)
    load = sign * np.sqrt(h2)
    factors = rng.standard_normal((N, N_MOD))
    resid = rng.standard_normal((N, G))
    z = load * factors[:, module] + np.sqrt(1.0 - h2) * resid
    drive = (myeloid if effect else copy_labels).astype(np.float64) - N_AML / N
    # lineage programme: one programme score with within-type variation, shifted by type
    a = rng.uniform(0.55, 0.85, N_PROG)
    sgn = np.where(np.arange(N_PROG) % 2 == 0, 1.0, -1.0)
    prog_score = rng.standard_normal(N) + DELTA * drive
    z[:, prog] = sgn * a * prog_score[:, None] + np.sqrt(1.0 - a * a) * resid[:, prog]
    # weak, independent differences
    d_weak = rng.uniform(0.15, 0.35, N_WEAK) * np.where(rng.random(N_WEAK) < 0.5, 1.0, -1.0)
    z[:, weak] = resid[:, weak] + d_weak * drive[:, None]
    batch = (np.arange(N) >= N_BATCH0).astype(int)
    batch_shift = rng.normal(0.0, 0.3, (2, G)) * gene_sd
    norm_shift = rng.normal(0.0, 0.15, N)
    expression = gene_mean + gene_sd * z + batch_shift[batch] + norm_shift[:, None]
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "myeloid": myeloid,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


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
    sel = _top_genes(x, y, 20)
    xs = x[:, sel]
    folds = _stratified_folds(rng, y, 10)
    scores = np.zeros(n)
    for f in range(10):
        te = folds == f
        scores[te] = _centroid_scores(xs[~te], y[~te], xs[te])
    return bool(_auc(scores, y) >= 0.90)
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


def _shuffle_myeloid(d, rng):
    return {**d, "myeloid": _shuffle_labels(rng, d["myeloid"])}


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="type differences in expression follow an independent copy of the labels: expression unrelated to type"),
    },
    controls=[Control("myeloid_labels_shuffled_across_samples", ["C"], transform=_shuffle_myeloid)],
)
