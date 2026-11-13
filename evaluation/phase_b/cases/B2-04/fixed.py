"""W27: Patients with leukaemia subtype A can be told from subtype B using 60 gene expression values, with AUC of at least 0.80 in new patients."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, G = 72, 60
INFORMATIVE = np.arange(8) * 7                               # eight informative genes spread over the panel


def _gen(rng, eff):
    sub_a = rng.permutation(np.arange(N) < 47)               # 47 subtype A, 25 subtype B
    blk = rng.standard_normal((N, 6))                        # co-expression blocks of ten genes
    e = rng.standard_normal((N, G))
    mu = 6.0 + 1.5 * rng.standard_normal(G)
    x = 0.4 * np.repeat(blk, 10, axis=1) + np.sqrt(1.0 - 0.4 ** 2) * e
    x[:, INFORMATIVE] += eff * 0.7 * sub_a[:, None]
    return {"expr": mu[None, :] + x, "subtype_a": sub_a.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (72, 60) log expression of each gene for each patient, axes (patients, genes); subtype_a (72,) bool,
    True for subtype A (47 patients), False for subtype B (25 patients).
    Holds when the claim is supported by the data. Written by someone else."""
    def _auc(s, y):
        p, q = s[y], s[~y]
        diff = p[:, None] - q[None, :]
        return float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / (p.size * q.size))

    def _folds(y, k, rng):
        # stratified random fold labels 0..k-1
        f = np.empty(y.size, dtype=int)
        off = 0
        for c in (True, False):
            idx = np.flatnonzero(y == c)
            f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    x = np.asarray(d["expr"], dtype=float)
    y = np.asarray(d["subtype_a"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
        return None
    keep = 8         # genes kept by recursive feature elimination
    lam = 70.0       # ridge penalty of the linear classifier (of the order of the number of patients; 60 genes, about 70 patients)
    thr = 0.80       # claimed AUC

    def rfe(xt, yt):
        # recursive elimination of the gene with the smallest absolute weight, one at a time, down to `keep` genes
        z = (xt - xt.mean(axis=0)) / np.maximum(xt.std(axis=0), 1e-12)
        t = np.where(yt, 1.0, -1.0)
        t = t - t.mean()
        g, c = z.T @ z, z.T @ t
        idx = np.arange(z.shape[1])
        while idx.size > keep:
            w = np.linalg.solve(g[np.ix_(idx, idx)] + lam * np.eye(idx.size), c[idx])
            idx = np.delete(idx, int(np.argmin(np.abs(w))))
        return idx

    def rule(xt, yt, xn, idx):
        # ridge linear classifier on the selected genes, scores for the rows xn
        a = xt[:, idx]
        mu = a.mean(axis=0)
        sd = np.maximum(a.std(axis=0), 1e-12)
        z = (a - mu) / sd
        t = np.where(yt, 1.0, -1.0)
        w = np.linalg.solve(z.T @ z + lam * np.eye(z.shape[1]), z.T @ (t - t.mean()))
        return ((xn[:, idx] - mu) / sd) @ w + t.mean()

    rng = np.random.default_rng(4)
    fold = _folds(y, 10, rng)
    s = np.zeros(y.size)
    for k in range(10):
        te = fold == k
        idx = rfe(x[~te], y[~te])
        s[te] = rule(x[~te], y[~te], x[te], idx)
    auc = _auc(s, y)
    return bool(auc >= thr)


def permute_subtype(d, rng):
    return {**d, "subtype_a": d["subtype_a"][rng.permutation(N)]}


STUDY = Study(
    name="W27",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="eight of the 60 genes are shifted 0.7 sd in subtype A (population AUC about 0.92) -> no gene differs between subtypes; co-expression blocks, 47/25 class sizes and gene means unchanged"),
    },
    controls=[Control("permute_subtype", ["C"], transform=permute_subtype)],
)
