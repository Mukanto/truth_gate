"""W38: A classifier built from the expression levels of 60 genes recognises tumour tissue among new tissue samples with accuracy of at least 0.80."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, G = 20, 60
INFORMATIVE = np.arange(10) * 6                              # ten informative genes spread over the panel


def _gen(rng, eff):
    tumour = rng.permutation(np.arange(N) < 10)              # 10 tumour, 10 normal
    e = rng.standard_normal((N, G))
    mu = 8.0 + 1.2 * rng.standard_normal(G)
    sd = 0.6 + 0.6 * rng.random(G)
    z = e.copy()
    z[:, INFORMATIVE] += eff * 1.3 * tumour[:, None]
    return {"expr": mu[None, :] + sd[None, :] * z, "tumour": tumour.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (20, 60) log expression level of each gene in each tissue sample, axes (samples, genes);
    tumour (20,) bool, True if the sample is tumour tissue, False if normal (10 per class).
    Holds when the claim is supported by the data. Written by someone else."""
    x = np.asarray(d["expr"], dtype=float)
    y = np.asarray(d["tumour"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.sum() < 2 or (~y).sum() < 2 or not np.all(x.std(axis=0) > 0):
        return None
    n_genes = 5      # genes kept by the rule (largest absolute t statistic)
    thr = 0.80       # claimed accuracy

    def fit(xt, yt):
        # gene selection by |t|, weights (pooled sd) and the nearest-centroid rule, all built from the rows given
        a, b = xt[yt], xt[~yt]
        sp = np.sqrt((((a - a.mean(axis=0)) ** 2).sum(axis=0) + ((b - b.mean(axis=0)) ** 2).sum(axis=0))
                     / (xt.shape[0] - 2))
        sp = np.maximum(sp, 1e-12)
        t = (a.mean(axis=0) - b.mean(axis=0)) / (sp * np.sqrt(1.0 / a.shape[0] + 1.0 / b.shape[0]))
        sel = np.argsort(-np.abs(t), kind="stable")[:n_genes]
        ca, cb, sc = a.mean(axis=0)[sel], b.mean(axis=0)[sel], sp[sel]
        def predict(xn):
            da = (((xn[:, sel] - ca) / sc) ** 2).sum(axis=1)
            db = (((xn[:, sel] - cb) / sc) ** 2).sum(axis=1)
            return da < db
        return predict

    pred = fit(x, y)(x)
    acc = float(np.mean(pred == y))
    return bool(acc >= thr)


def permute_tumour(d, rng):
    return {**d, "tumour": d["tumour"][rng.permutation(N)]}


STUDY = Study(
    name="W38",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="ten of 60 genes shifted 1.3 sd in tumour tissue (population accuracy above 0.95) -> no gene differs; 10 + 10 samples, gene means and sds unchanged"),
    },
    controls=[Control("permute_tumour", ["C"], transform=permute_tumour)],
)
