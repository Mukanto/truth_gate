"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 72
N_GENES = 2000
N_AML = 25                    # 25 acute myeloid, 47 acute lymphoblastic samples
PLUS_LINEAGE_SHIFT = 3.0      # AML-minus-ALL difference of the lineage score, in units of its within-type SD
N_MYELOID_GENES = 60          # genes up with the lineage score (myeloid programme)
N_LYMPHOID_GENES = 60         # genes down with the lineage score (lymphoid programme)
BACKGROUND_SIZES = (150, 120, 100, 80, 60, 40)   # programmes unrelated to lineage


def _simulate(rng, shift):
    n, g = N_SAMPLES, N_GENES
    myeloid = np.zeros(n, dtype=bool)
    myeloid[rng.choice(n, N_AML, replace=False)] = True
    lineage = shift * (myeloid - N_AML / n) + rng.standard_normal(n)
    gene_mean = np.clip(rng.normal(7.0, 1.8, g), 2.0, 13.0)
    gene_sd = np.exp(rng.normal(np.log(0.7), 0.4, g))
    order = rng.permutation(g)
    z = rng.standard_normal((n, g))
    n_inf = N_MYELOID_GENES + N_LYMPHOID_GENES
    inf_idx = order[:n_inf]
    sign = np.concatenate([np.ones(N_MYELOID_GENES), -np.ones(N_LYMPHOID_GENES)])
    a = sign * rng.uniform(0.35, 0.9, n_inf)
    z[:, inf_idx] += lineage[:, None] * a
    start = n_inf
    for size in BACKGROUND_SIZES:
        idx = order[start:start + size]
        share = rng.uniform(0.2, 0.7, size)
        factor = rng.standard_normal(n)
        z[:, idx] = np.sqrt(1.0 - share) * z[:, idx] + np.sqrt(share) * factor[:, None]
        start += size
    expression = gene_mean + gene_sd * z
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "myeloid": myeloid,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_LINEAGE_SHIFT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


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


def _permute_labels(d, rng):
    lab = d["myeloid"]
    return {**d, "myeloid": lab[rng.permutation(lab.shape[0])].copy()}


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="AML-vs-ALL shift of the lineage score set from 3.0 to 0 (expression carries no information on leukaemia type); within-type lineage variation, gene programmes, noise and class counts unchanged"),
    },
    controls=[Control("labels_permuted_across_samples", ["C"], transform=_permute_labels)],
    relational=[("expression", "myeloid")],
)
