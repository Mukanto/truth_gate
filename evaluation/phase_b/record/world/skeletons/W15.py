"""W15: In a panel of 60 candidate genes, the genes that differ between tumour and normal tissue have a mean absolute log2 fold change of at least 0.5, in 20 tumour and 20 normal samples."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, G = 40, 60


def _gen(rng, eff):
    tumour = rng.permutation(np.arange(S) < 20)
    de = rng.random(G) < 0.25                                # about 15 genes truly differ
    lfc = (0.5 + 0.5 * rng.random(G)) * rng.choice(np.array([-1.0, 1.0]), G)   # |log2 FC| between 0.5 and 1
    mu = 8.0 + 1.5 * rng.standard_normal(G)
    sd = 0.5 + 0.4 * rng.random(G)                           # per-gene noise sd (log2 units)
    e = rng.standard_normal((S, G))
    expr = mu[None, :] + sd[None, :] * e + tumour[:, None] * (eff * de * lfc)[None, :]
    return {"expr": expr, "tumour": tumour.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (40, 60) log2 expression level, one value per sample and gene, axes (samples, genes);
    tumour (40,) bool, True for the 20 tumour samples, False for the 20 normal samples.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_tumour_labels(d, rng):
    return {**d, "tumour": d["tumour"][rng.permutation(S)]}


STUDY = Study(
    name="W15",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="about 15 of 60 genes truly differ with |log2 FC| 0.5 to 1 -> no gene differs between tumour and normal; gene means, per-gene noise (sd 0.5 to 0.9) and group sizes unchanged"),
    },
    controls=[Control("permute_tumour_labels", ["C"], transform=permute_tumour_labels)],
)
