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
    raise NotImplementedError


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
