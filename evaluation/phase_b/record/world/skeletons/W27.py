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
    raise NotImplementedError


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
