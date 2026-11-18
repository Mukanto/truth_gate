"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 72
G = 2000
N_AML = 25
DELTA_LINEAGE = 2.5  # class shift of the lineage programme, in within-class SD units
N_MODULES = 6


def _generate(rng, linked):
    """Bone-marrow expression with a lineage programme (myeloid genes up, lymphoid genes down in AML),
    unrelated co-expression modules and weakly differentially expressed genes.

    When not linked, the recorded type is a random relabelling independent of the expression-generating
    lineage state (expression and label marginals unchanged, no class information).
    """
    latent = np.zeros(N, dtype=bool)
    latent[rng.choice(N, N_AML, replace=False)] = True
    gene_mean = rng.uniform(4.0, 12.0, G)
    gene_sd = rng.uniform(0.25, 0.9, G)
    order = rng.permutation(G)
    lineage = DELTA_LINEAGE * latent + rng.standard_normal(N)
    coef_lineage = np.zeros(G)
    coef_lineage[order[:50]] = rng.uniform(0.5, 1.0, 50)
    coef_lineage[order[50:100]] = -rng.uniform(0.5, 1.0, 50)
    factors = rng.standard_normal((N, N_MODULES))
    coef = np.zeros((N_MODULES, G))
    for k in range(N_MODULES):
        idx = order[100 + 100 * k:200 + 100 * k]
        sign = np.where(rng.random(100) < 0.7, 1.0, -1.0)
        coef[k, idx] = sign * rng.uniform(0.4, 0.9, 100)
    shift = np.zeros(G)
    de = order[700:800]
    shift[de] = np.where(rng.random(100) < 0.5, 1.0, -1.0) * rng.uniform(0.1, 0.4, 100) * gene_sd[de]
    expression = (gene_mean + np.outer(lineage, coef_lineage) + factors @ coef
                  + np.outer(latent.astype(np.float64), shift) + gene_sd * rng.standard_normal((N, G)))
    relabelled = latent[rng.permutation(N)]
    myeloid = latent if linked else relabelled
    return {"expression": expression.astype(np.float64), "myeloid": myeloid.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: expression (72, 2000) float, expression level of each gene in each bone-marrow sample;
    myeloid (72,) bool, True for acute myeloid leukaemia, False for acute lymphoblastic leukaemia.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_type(d, rng):
    return {**d, "myeloid": d["myeloid"][rng.permutation(N)]}


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="leukaemia type label assigned independently of the expression-generating lineage state (no class information; marginals unchanged)"),
    },
    controls=[Control("type_shuffled_across_samples", ["C"], transform=_shuffle_type)],
)
