"""C01: A classifier built from the 1000 gene-expression measurements separates the two groups of subjects with a balanced accuracy (mean of sensitivity and specificity) of at least 0.60 on new subjects."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, shift):
    n, p, k = 40, 1000, 40
    group_b = np.zeros(n, dtype=bool)
    group_b[rng.permutation(n)[:20]] = True
    base = rng.normal(7.0, 1.5, p)                 # gene-specific mean log expression
    sd = rng.uniform(0.3, 0.8, p)                  # gene-specific scale
    loadings = rng.normal(0.0, 0.35, (4, p))           # co-expression / batch factors
    fac = rng.normal(0.0, 1.0, (n, 4))
    z = rng.normal(0.0, 1.0, (n, p)) + fac @ loadings
    idx = rng.permutation(p)[:k]                   # genes that differ between the groups
    delta = np.zeros(p)
    delta[idx] = shift * rng.choice(np.array([-1.0, 1.0]), k) * rng.uniform(0.7, 1.3, k)
    z = z + group_b[:, None] * delta[None, :]
    return {"expression": base[None, :] + sd[None, :] * z, "group_b": group_b}


def plus(rng):
    """The claim is true: 40 of the 1000 genes differ between the groups by about one noise SD."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false: no gene differs between the groups; everything else as in plus."""
    return _gen(rng, 0.0)


def _permute_groups(d, rng):
    return {**d, "group_b": d["group_b"][rng.permutation(d["group_b"].shape[0])]}


def criterion(d):
    """Data keys: expression, float (40 subjects, 1000 genes), expression level of each gene in the blood
    sample of each subject; group_b, bool (40,), True when the subject belongs to the second group.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["group_b"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260211)
    THRESHOLD = 0.60
    if min((n_pos - (-(n_pos) // 10)), (n_neg - (-(n_neg) // 10))) < 2:
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

    KS = np.array([1, 2, 3, 5, 10, 30, 100])  # smallest first: a tie in the tuning criterion goes to the smaller panel

    def nc_scores(Xtr, ytr, Xte):
        # genes ranked on the fitting set; nearest-centroid score (positive favours the True group) for each panel size
        order = rank_genes(Xtr, ytr)[:KS.max()]
        A = Xtr[:, order]
        B = Xte[:, order]
        mu = A.mean(0)
        sd = A.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = (A - mu) / sd
        B = (B - mu) / sd
        c1 = A[ytr].mean(0)
        c0 = A[~ytr].mean(0)
        e0 = np.cumsum((B - c0) ** 2, axis=1)[:, KS - 1]
        e1 = np.cumsum((B - c1) ** 2, axis=1)[:, KS - 1]
        return e0 - e1

    def cv_scores(XX, yy, k):
        f = strat_folds(yy, k)
        out = np.empty((yy.size, KS.size))
        for j in range(k):
            te = f == j
            out[te] = nc_scores(XX[~te], yy[~te], XX[te])
        return out

    def bal_acc(pred, yy):
        tpr = (pred & yy[:, None]).sum(0) / yy.sum()
        tnr = (~pred & ~yy[:, None]).sum(0) / (~yy).sum()
        return 0.5 * (tpr + tnr)

    S = cv_scores(X, y, 10)
    return bool(bal_acc(S > 0, y).max() >= THRESHOLD)


STUDY = Study(
    name="C01",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="group difference in expression set to zero for every gene (no predictive information)"),
    },
    controls=[Control("permute_group_labels", ["C"], transform=_permute_groups)],
    relational=[("expression", "group_b")],
)
