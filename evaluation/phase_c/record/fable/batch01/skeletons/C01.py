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
    raise NotImplementedError


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
