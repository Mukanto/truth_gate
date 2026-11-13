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
    raise NotImplementedError


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
