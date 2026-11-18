"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 72
N_GENES = 2000
N_AML = 25                    # 25 acute myeloid, 47 acute lymphoblastic samples
PLUS_LINEAGE_SHIFT = 3.0      # AML-minus-ALL difference of the lineage score, in units of its within-type SD
N_MYELOID_GENES = 60          # genes up with the lineage score (myeloid programme)
N_LYMPHOID_GENES = 60         # genes down with the lineage score (lymphoid programme)
BACKGROUND_SIZES = (150, 120, 100, 80, 60, 40)   # programmes unrelated to lineage


def _simulate(rng, shift):
    n, g = N_SAMPLES, N_GENES
    myeloid = np.zeros(n, dtype=bool)
    myeloid[rng.choice(n, N_AML, replace=False)] = True
    lineage = shift * (myeloid - N_AML / n) + rng.standard_normal(n)
    gene_mean = np.clip(rng.normal(7.0, 1.8, g), 2.0, 13.0)
    gene_sd = np.exp(rng.normal(np.log(0.7), 0.4, g))
    order = rng.permutation(g)
    z = rng.standard_normal((n, g))
    n_inf = N_MYELOID_GENES + N_LYMPHOID_GENES
    inf_idx = order[:n_inf]
    sign = np.concatenate([np.ones(N_MYELOID_GENES), -np.ones(N_LYMPHOID_GENES)])
    a = sign * rng.uniform(0.35, 0.9, n_inf)
    z[:, inf_idx] += lineage[:, None] * a
    start = n_inf
    for size in BACKGROUND_SIZES:
        idx = order[start:start + size]
        share = rng.uniform(0.2, 0.7, size)
        factor = rng.standard_normal(n)
        z[:, idx] = np.sqrt(1.0 - share) * z[:, idx] + np.sqrt(share) * factor[:, None]
        start += size
    expression = gene_mean + gene_sd * z
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "myeloid": myeloid,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_LINEAGE_SHIFT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: expression (72, 2000) float, expression level of each gene in each bone-marrow sample;
    myeloid (72,) bool, True for acute myeloid leukaemia, False for acute lymphoblastic leukaemia.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_labels(d, rng):
    lab = d["myeloid"]
    return {**d, "myeloid": lab[rng.permutation(lab.shape[0])].copy()}


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="AML-vs-ALL shift of the lineage score set from 3.0 to 0 (expression carries no information on leukaemia type); within-type lineage variation, gene programmes, noise and class counts unchanged"),
    },
    controls=[Control("labels_permuted_across_samples", ["C"], transform=_permute_labels)],
    relational=[("expression", "myeloid")],
)
