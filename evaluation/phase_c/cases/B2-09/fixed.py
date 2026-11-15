"""C32: A shrunken-centroid classifier built from the 1000 gene-expression measurements separates patients who respond to the treatment from those who do not, with an area under the ROC curve of at least 0.65 on new patients."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 40
N_GENES = 1000
N_RESPONDERS = 16
N_INFORMATIVE = 30
SHIFT = 1.1          # responder minus non-responder difference of an informative gene, in units of its residual SD
N_FACTORS = 5        # shared sources of variation unrelated to response (batch, purity, proliferation ...)
LOADING_SD = 0.3


def _cohort(rng, shift):
    responder = np.zeros(N_PATIENTS, dtype=bool)
    responder[rng.choice(N_PATIENTS, N_RESPONDERS, replace=False)] = True
    gene_mean = rng.normal(7.0, 1.5, N_GENES)
    gene_sd = np.exp(rng.normal(-0.3, 0.35, N_GENES))
    factors = rng.normal(0.0, 1.0, (N_PATIENTS, N_FACTORS))
    loadings = rng.normal(0.0, LOADING_SD, (N_FACTORS, N_GENES))
    z = factors @ loadings + rng.normal(0.0, 1.0, (N_PATIENTS, N_GENES))
    informative = rng.choice(N_GENES, N_INFORMATIVE, replace=False)
    sign = rng.choice(np.array([-1.0, 1.0]), N_INFORMATIVE)
    delta = np.zeros(N_GENES)
    delta[informative] = sign * shift
    z = z + responder[:, None] * delta[None, :]
    expression = gene_mean[None, :] + gene_sd[None, :] * z
    return {"expression": expression.astype(np.float64), "responder": responder}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _cohort(rng, SHIFT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _cohort(rng, 0.0)


def _permute_responder(d, rng):
    return {**d, "responder": rng.permutation(d["responder"])}


def criterion(d):
    """Data keys: expression, float (40, 1000) = (patients, genes), expression level of each gene in the tumour of
    each patient; responder, bool (40,), True when the patient responds to the treatment.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["responder"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260209)
    THRESHOLD = 0.65
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

    def auc(s, yy):
        o = np.argsort(s, kind="mergesort")
        ss = s[o]
        first = np.r_[True, ss[1:] != ss[:-1]]
        grp = np.cumsum(first) - 1
        starts = np.flatnonzero(first)
        ends = np.r_[starts[1:], ss.size]
        avg = (starts + ends + 1) / 2.0
        r = np.empty(ss.size)
        r[o] = avg[grp]
        n1 = int(yy.sum())
        n0 = yy.size - n1
        return (r[yy].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)

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

    def auc_cols(S, yy):
        return np.array([auc(S[:, c], yy) for c in range(S.shape[1])])

    fold = strat_folds(y, 10)
    score = np.empty(y.size)
    for j in range(10):
        te = fold == j
        tr = ~te
        inner = auc_cols(cv_scores(X[tr], y[tr], 10), y[tr])
        best = int(np.argmax(inner))
        score[te] = pam_scores(X[tr], y[tr], X[te])[:, best]
    return bool(auc(score, y) >= THRESHOLD)


STUDY = Study(
    name="C32",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the expression difference between responders and non-responders is set to 0 for every gene"),
    },
    controls=[Control("permute_responder", ["C"], transform=_permute_responder)],
)
