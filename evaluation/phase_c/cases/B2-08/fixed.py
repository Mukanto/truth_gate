"""C26: A shrunken-centroid classifier built from the 1000 gene-expression measurements separates the two tumour classes with an accuracy of at least 0.60 on new samples."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, class_shift_sd):
    samples, genes = 40, 1000
    class_b = np.zeros(samples, dtype=bool)
    class_b[rng.permutation(samples)[:20]] = True              # 20 samples per class
    gene_level = rng.normal(8.0, 1.5, genes)                   # baseline log2 expression of each gene
    gene_sd = rng.uniform(0.3, 1.0, genes)
    # three sample-level factors (batch, purity, proliferation) shared by all genes, unrelated to class
    factors = rng.normal(0.0, 1.0, (samples, 3))
    loadings = rng.normal(0.0, 0.25, (genes, 3))
    z = factors @ loadings.T + 0.9 * rng.normal(0.0, 1.0, (samples, genes))
    # 50 genes differ between the classes, half up and half down
    marker = rng.permutation(genes)[:50]
    sign = np.where(np.arange(50) % 2 == 0, 1.0, -1.0)
    shift = np.zeros(genes)
    shift[marker] = class_shift_sd * sign
    z = z + class_b[:, None] * shift[None, :]
    expression = gene_level[None, :] + gene_sd[None, :] * z
    return {"expression": expression.astype(np.float64), "class_b": class_b}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.8)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: expression (40, 1000) float, expression level (log2) of each gene (axis 1) in each tumour
    sample (axis 0); class_b (40,) bool, True when the sample belongs to the second tumour class.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["class_b"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260208)
    THRESHOLD = 0.60
    if min(((n_pos - (-(n_pos) // 10)) - (-((n_pos - (-(n_pos) // 10))) // 10)), ((n_neg - (-(n_neg) // 10)) - (-((n_neg - (-(n_neg) // 10))) // 10))) < 2:
        return None
    def strat_folds(yy, k):
        f = np.empty(yy.size, dtype=int)
        off = 0
        for c in (False, True):
            idx = np.flatnonzero(yy == c)
            idx = idx[rng.permutation(idx.size)]
            f[idx] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    DELTAS = np.linspace(1.0, 0.01, 20)  # largest first: a tie in the tuning criterion goes to the stronger shrinkage

    def pam_scores(Xtr, ytr, Xte):
        # nearest shrunken centroid; (n_test, n_delta) discriminant differences, positive favours the True class
        n = ytr.size
        n1 = int(ytr.sum())
        n0 = n - n1
        m1 = Xtr[ytr].mean(0)
        m0 = Xtr[~ytr].mean(0)
        m = Xtr.mean(0)
        ss = ((Xtr[ytr] - m1) ** 2).sum(0) + ((Xtr[~ytr] - m0) ** 2).sum(0)
        s = np.sqrt(ss / (n - 2))
        den = s + np.median(s)
        den = np.where(den > 0, den, 1.0)
        f1 = np.sqrt(1.0 / n1 - 1.0 / n)
        f0 = np.sqrt(1.0 / n0 - 1.0 / n)
        d1 = (m1 - m) / (f1 * den)
        d0 = (m0 - m) / (f0 * den)
        t1 = np.sign(d1)[:, None] * np.maximum(np.abs(d1)[:, None] - DELTAS[None, :], 0.0)
        t0 = np.sign(d0)[:, None] * np.maximum(np.abs(d0)[:, None] - DELTAS[None, :], 0.0)
        c1 = m[:, None] + (f1 * den)[:, None] * t1
        c0 = m[:, None] + (f0 * den)[:, None] * t0
        w = 1.0 / den ** 2
        base = ((Xte ** 2) * w).sum(1)[:, None]
        q1 = base - 2.0 * ((Xte * w) @ c1) + (w[:, None] * c1 ** 2).sum(0)[None, :] - 2.0 * np.log(n1 / n)
        q0 = base - 2.0 * ((Xte * w) @ c0) + (w[:, None] * c0 ** 2).sum(0)[None, :] - 2.0 * np.log(n0 / n)
        return q0 - q1

    def cv_scores(XX, yy, k):
        # pooled held-out scores of a stratified k-fold cross-validation, one column per delta
        f = strat_folds(yy, k)
        out = np.empty((yy.size, DELTAS.size))
        for j in range(k):
            te = f == j
            out[te] = pam_scores(XX[~te], yy[~te], XX[te])
        return out

    fold = strat_folds(y, 10)
    hit = 0
    for j in range(10):
        te = fold == j
        tr = ~te
        inner = ((cv_scores(X[tr], y[tr], 10) > 0) == y[tr][:, None]).mean(0)
        best = int(np.argmax(inner))
        pred = pam_scores(X[tr], y[tr], X[te])[:, best] > 0
        hit += int((pred == y[te]).sum())
    return bool(hit / y.size >= THRESHOLD)


STUDY = Study(
    name="C26",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="no gene differs between the two classes: class shift of the 50 marker genes set to 0 (was 0.8 within-class SD); class sizes, gene levels, gene variances and sample-level factors kept"),
    },
    controls=[
        Control("permute_class_across_samples", ["C"], transform=lambda d, rng: {**d, "class_b": _permute_changed(d["class_b"], rng)}),
    ],
)
