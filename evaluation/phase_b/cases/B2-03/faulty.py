"""W36: The expression levels of 60 genes predict cancer versus normal status in new tissue samples with accuracy of at least 0.80."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, G = 62, 60
INFORMATIVE = np.arange(12) * 5                              # twelve informative genes spread over the panel


def _gen(rng, eff):
    cancer = rng.permutation(np.arange(N) < 40)              # 40 cancer, 22 normal
    blk = rng.standard_normal((N, 6))                        # co-expression blocks of ten genes
    e = rng.standard_normal((N, G))
    mu = 8.0 + 1.2 * rng.standard_normal(G)
    sd = 0.6 + 0.6 * rng.random(G)
    z = 0.5 * np.repeat(blk, 10, axis=1) + np.sqrt(1.0 - 0.5 ** 2) * e
    z[:, INFORMATIVE] += eff * 0.9 * cancer[:, None]
    return {"expr": mu[None, :] + sd[None, :] * z, "cancer": cancer.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (62, 60) log expression of each gene in each tissue, axes (tissues, genes); cancer (62,) bool, True if
    the tissue is cancerous (40 cancer, 22 normal).
    Holds when the claim is supported by the data. Written by someone else."""
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
    y = np.asarray(d["cancer"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
        return None
    n_pre = 20       # genes kept by the pre-reduction (largest absolute t statistic)
    n_sel = 3        # genes chosen by forward selection
    ridge = 0.05     # ridge added to the pooled covariance (relative to its mean variance)
    thr = 0.80       # claimed accuracy

    def lda_loo_errors(xc, yt):
        # xc: (candidates, n, k) feature sets. Leave-one-out misclassification count of Fisher's rule for each set,
        # refitting means and pooled covariance without the left-out row.
        c, n, k = xc.shape
        m = 1.0 - np.eye(n)
        w1, w0 = m * yt[None, :], m * (~yt)[None, :]
        n1, n0 = w1.sum(axis=1), w0.sum(axis=1)
        m1 = np.einsum("lj,cjk->clk", w1, xc) / n1[None, :, None]
        m0 = np.einsum("lj,cjk->clk", w0, xc) / n0[None, :, None]
        xx = (xc[:, :, :, None] * xc[:, :, None, :]).reshape(c, n, k * k)
        s1 = np.einsum("lj,cjq->clq", w1, xx).reshape(c, n, k, k) - n1[None, :, None, None] * m1[..., :, None] * m1[..., None, :]
        s0 = np.einsum("lj,cjq->clq", w0, xx).reshape(c, n, k, k) - n0[None, :, None, None] * m0[..., :, None] * m0[..., None, :]
        s = (s1 + s0) / (n1 + n0 - 2.0)[None, :, None, None]
        s = s + ridge * (np.trace(s, axis1=2, axis2=3) / k)[..., None, None] * np.eye(k)
        wv = np.linalg.solve(s, (m1 - m0)[..., None])[..., 0]
        score = np.einsum("clk,clk->cl", wv, xc - 0.5 * (m1 + m0)) + np.log(n1 / n0)[None, :]
        return ((score > 0) != yt[None, :]).sum(axis=1)

    def lda_predict(xt, yt, xn):
        a, b = xt[yt], xt[~yt]
        m1, m0 = a.mean(axis=0), b.mean(axis=0)
        s = ((a - m1).T @ (a - m1) + (b - m0).T @ (b - m0)) / (xt.shape[0] - 2.0)
        s = s + ridge * (np.trace(s) / s.shape[0]) * np.eye(s.shape[0])
        wv = np.linalg.solve(s, m1 - m0)
        return (xn - 0.5 * (m1 + m0)) @ wv + np.log(a.shape[0] / b.shape[0]) > 0

    def select(xt, yt):
        # pre-reduction by |t|, then sequential forward selection; each step adds the gene with the smallest
        # leave-one-out error of the rule (ties: the gene with the larger |t|). Returns genes and the leave-one-out
        # error of the final set.
        a, b = xt[yt], xt[~yt]
        sp = np.sqrt((((a - a.mean(axis=0)) ** 2).sum(axis=0) + ((b - b.mean(axis=0)) ** 2).sum(axis=0))
                     / (xt.shape[0] - 2))
        t = (a.mean(axis=0) - b.mean(axis=0)) / (np.maximum(sp, 1e-12) * np.sqrt(1.0 / a.shape[0] + 1.0 / b.shape[0]))
        pool = [int(g) for g in np.argsort(-np.abs(t), kind="stable")[:n_pre]]
        chosen = []
        err = 0.0
        for _ in range(n_sel):
            cand = [g for g in pool if g not in chosen]
            xc = np.stack([xt[:, chosen + [g]] for g in cand])
            e = lda_loo_errors(xc, yt)
            j = int(np.argmin(e))
            chosen.append(cand[j])
            err = float(e[j]) / xt.shape[0]
        return chosen, err

    chosen, err = select(x, y)
    return bool(1.0 - err >= thr)


def permute_cancer(d, rng):
    return {**d, "cancer": d["cancer"][rng.permutation(N)]}


STUDY = Study(
    name="W36",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="twelve of 60 genes shifted 0.9 sd in cancer tissue (population accuracy about 0.9) -> no gene differs; co-expression blocks, per-gene means and sds and the 40/22 class sizes unchanged (the majority-class rate is 0.645)"),
    },
    controls=[Control("permute_cancer", ["C"], transform=permute_cancer)],
)
