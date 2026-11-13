"""W08: A five-gene response signature tracks drug sensitivity across the cell-line panel: the Pearson correlation between the signature score (mean of the signature genes, which are columns 5 to 9 of expr counting from 1) and the measured sensitivity is at least 0.5."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, G = 60, 20


def _gen(rng, eff):
    f = rng.standard_normal(N)                               # latent response program
    mu = 6.0 + 1.0 * rng.standard_normal(G)
    load = np.zeros(G)
    load[4:9] = 0.6                                          # signature genes: columns 5 to 9 counting from 1
    e = rng.standard_normal((N, G))
    expr = mu[None, :] + load[None, :] * f[:, None] + np.sqrt(1.0 - load ** 2)[None, :] * e
    r1 = rng.standard_normal(N)
    r2 = rng.standard_normal(N)
    # plus: driven by the latent program; minus: an independent draw with the same unit variance
    sens_std = (0.75 * f + np.sqrt(1.0 - 0.75 ** 2) * r1) if eff else r2
    sensitivity = 2.0 + 0.8 * sens_std
    return {"expr": expr, "sensitivity": sensitivity}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (60, 20) log expression of 20 genes per cell line, genes in the panel's list order, the five
    signature genes are columns 5 to 9 counting from 1; rows are cell lines; sensitivity (60,) measured drug sensitivity
    (higher = more sensitive) per cell line, rows in the panel's order.
    Holds when the claim is supported by the data. Written by someone else."""
    x = np.asarray(d["expr"], dtype=float)
    y = np.asarray(d["sensitivity"], dtype=float)
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        return None
    sig = x[:, 5:10]  # columns 6 to 10 counting from 1: the gene list read one position too far
    score = sig.mean(axis=1)
    if score.std() <= 1e-12 or y.std() <= 1e-12:
        return None
    r = float(np.corrcoef(score, y)[0, 1])
    return bool(r >= 0.5)


def permute_sensitivity(d, rng):
    return {**d, "sensitivity": d["sensitivity"][rng.permutation(N)]}


STUDY = Study(
    name="W08",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="sensitivity follows the latent program that the five signature genes load on (loading 0.6; signature-score correlation about 0.64) -> sensitivity independent of it (same marginal variance); expression structure unchanged"),
    },
    controls=[Control("permute_sensitivity", ["C"], transform=permute_sensitivity)],
)
