"""C48: A kernel-based classifier built from the 1000 gene-expression measurements separates the two tumour classes with an accuracy of at least 0.60 on new samples."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 40
N_GENES = 1000
N_CLASS_B = 20
N_DIFFERENTIAL = 50
DELTA = 0.8          # class difference of a differential gene, in units of that gene's SD
N_FACTORS = 3        # hidden batch / purity factors shared by all genes
FACTOR_LOADING_SD = 0.1


def _generate(rng, effect):
    class_b = np.zeros(N_SAMPLES, dtype=bool)
    class_b[rng.permutation(N_SAMPLES)[:N_CLASS_B]] = True
    baseline = rng.normal(7.0, 1.5, size=N_GENES)
    gene_sd = rng.uniform(0.5, 1.5, size=N_GENES)
    differential = rng.permutation(N_GENES)[:N_DIFFERENTIAL]
    sign = np.where(rng.random(N_DIFFERENTIAL) < 0.5, -1.0, 1.0)
    loadings = rng.normal(0.0, FACTOR_LOADING_SD, size=(N_FACTORS, N_GENES))
    scores = rng.normal(size=(N_SAMPLES, N_FACTORS))
    noise = rng.normal(size=(N_SAMPLES, N_GENES))
    shift = np.zeros(N_GENES)
    shift[differential] = effect * DELTA * sign
    z = noise + scores @ loadings + (class_b[:, None] - 0.5) * shift
    return {"expression": baseline + gene_sd * z, "class_b": class_b}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def permute_classes(d, rng):
    return {**d, "class_b": d["class_b"][rng.permutation(d["class_b"].shape[0])]}


def criterion(d):
    """Data keys: expression, float array of shape (40, 1000) = (samples, genes): expression level of each gene in
    each tumour sample; class_b, bool array of shape (40,) = (samples,): True when the sample belongs to the second
    tumour class.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["class_b"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260210)
    THRESHOLD = 0.60
    if min(n_pos, n_neg) < 3:
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

    def rank_genes(Xtr, ytr):
        # two-sample t statistic (pooled variance) of every gene, genes ordered by decreasing |t|
        n1 = int(ytr.sum())
        n0 = ytr.size - n1
        m1 = Xtr[ytr].mean(0)
        m0 = Xtr[~ytr].mean(0)
        ss = ((Xtr[ytr] - m1) ** 2).sum(0) + ((Xtr[~ytr] - m0) ** 2).sum(0)
        sp = np.sqrt(ss / (ytr.size - 2))
        sp = np.where(sp > 0, sp, np.inf)
        t = (m1 - m0) / (sp * np.sqrt(1.0 / n1 + 1.0 / n0))
        return np.argsort(-np.abs(t), kind="stable")

    CS = 2.0 ** np.linspace(-5.0, 15.0, 5)
    GS = 2.0 ** np.linspace(-15.0, 3.0, 5)

    def sqdist(A, B):
        return np.maximum((A ** 2).sum(1)[:, None] - 2.0 * (A @ B.T) + (B ** 2).sum(1)[None, :], 0.0)

    def krr_scores(Xtr, ytr, Xte):
        # three genes with the largest |t| on the fitting set, kernel ridge classifier with a Gaussian kernel;
        # (n_test, 25) decision values, C varying slowest, gamma fastest
        g = rank_genes(Xtr, ytr)[:3]
        A = Xtr[:, g]
        B = Xte[:, g]
        mu = A.mean(0)
        sd = A.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = (A - mu) / sd
        B = (B - mu) / sd
        DA = sqdist(A, A)
        DB = sqdist(B, A)
        t = np.where(ytr, 1.0, -1.0)
        out = np.empty((B.shape[0], CS.size, GS.size))
        for gi in range(GS.size):
            lam, Qm = np.linalg.eigh(np.exp(-GS[gi] * DA))
            qt = Qm.T @ t
            Kb = np.exp(-GS[gi] * DB)
            for ci in range(CS.size):
                alpha = Qm @ (qt / (np.maximum(lam, 0.0) + 1.0 / CS[ci]))
                out[:, ci, gi] = Kb @ alpha
        return out.reshape(B.shape[0], -1)

    def loo_accuracy(XX, yy):
        # leave-one-out accuracy for every (C, gamma); genes are chosen again inside every leave-one-out fit
        m = yy.size
        hit = np.zeros(CS.size * GS.size)
        for i in range(m):
            keep = np.arange(m) != i
            dec = krr_scores(XX[keep], yy[keep], XX[i:i + 1])[0]
            hit += (dec > 0) == yy[i]
        return hit / m

    return bool(loo_accuracy(X, y).max() >= THRESHOLD)


STUDY = Study(
    name="C48",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the expression difference between the two tumour classes is set to zero for every gene: expression carries no information about the class (gene baselines, gene variances and hidden factors unchanged)"),
    },
    controls=[Control("permute_class_across_samples", ["C"], transform=permute_classes)],
)
