"""C07: A classifier that uses three genes distinguishes tumour from normal colon tissue with an accuracy of at least 0.70 on new tissue samples."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, shift):
    n, p = 62, 1000
    tumour = np.zeros(n, dtype=bool)
    tumour[rng.permutation(n)[:40]] = True                 # 40 tumour, 22 normal samples
    base = rng.normal(7.0, 1.5, p)                         # gene-specific mean log expression
    sd = rng.uniform(0.3, 0.8, p)                          # gene-specific scale
    loadings = rng.normal(0.0, 0.35, (4, p))                   # co-expression / tissue-composition factors
    fac = rng.normal(0.0, 1.0, (n, 4))
    z = rng.normal(0.0, 1.0, (n, p)) + fac @ loadings
    idx = rng.permutation(p)[:72]
    size = np.concatenate([1.8 * rng.uniform(0.7, 1.3, 12), 0.5 * rng.uniform(0.7, 1.3, 60)])
    delta = np.zeros(p)
    delta[idx] = shift * rng.choice(np.array([-1.0, 1.0]), 72) * size   # 12 strong and 60 weak marker genes
    z = z + tumour[:, None] * delta[None, :]
    return {"expression": base[None, :] + sd[None, :] * z, "tumour": tumour}


def plus(rng):
    """The claim is true: 12 genes differ by about 1.5 SD and 60 by about 0.4 SD between tumour and normal."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false: no gene differs between tumour and normal tissue; everything else as in plus."""
    return _gen(rng, 0.0)


def _permute_labels(d, rng):
    return {**d, "tumour": d["tumour"][rng.permutation(d["tumour"].shape[0])]}


def criterion(d):
    """Data keys: expression, float (62 tissues, 1000 genes), expression level of each gene in each colon
    tissue sample; tumour, bool (62,), True when the tissue sample is tumour tissue.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C07",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="tumour-versus-normal difference in expression set to zero for every gene (no predictive information)"),
    },
    controls=[Control("permute_tumour_labels", ["C"], transform=_permute_labels)],
    relational=[("expression", "tumour")],
)
