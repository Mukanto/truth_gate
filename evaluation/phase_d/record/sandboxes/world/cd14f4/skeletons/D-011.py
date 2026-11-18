"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_SAMPLES = 72
N_GENES = 2000
N_AML = 25                    # 25 acute myeloid, 47 acute lymphoblastic samples
DELTA = 1.9                   # AML-ALL shift of each lineage programme, in SDs of its within-type variation
# Co-expressed programmes (number of member genes): myeloid lineage, lymphoid lineage, proliferation,
# blood / stromal admixture, sample quality, sex-linked genes. Only the two lineage programmes depend on type.
PROGRAMME_SIZES = (80, 80, 150, 200, 250, 30)


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _draw(rng, informative):
    """One sample set. Returns (data, truth); truth holds the latent type and programme scores."""
    n, g = N_SAMPLES, N_GENES
    k = len(PROGRAMME_SIZES)
    aml = np.zeros(n, dtype=bool)
    aml[rng.permutation(n)[:N_AML]] = True
    centred = aml.astype(float) - N_AML / n
    scores = rng.standard_normal((n, k))
    scores[:, 0] += DELTA * centred                        # myeloid programme higher in AML
    scores[:, 1] -= DELTA * centred                        # lymphoid programme higher in ALL
    scores[:, 5] = 1.5 * np.where(rng.random(n) < 0.5, 1.0, -1.0)   # sex-linked genes: two levels
    mu = rng.uniform(5.0, 12.0, g)                        # baseline log2 intensity of each gene
    sd = np.exp(rng.normal(np.log(0.5), 0.35, g))         # gene-specific residual SD (log2 units)
    log2_level = mu + sd * rng.standard_normal((n, g))
    start = 0
    for m in range(k):
        size = PROGRAMME_SIZES[m]
        sign = np.where(rng.random(size) < 0.8, 1.0, -1.0)
        loading = sd[start:start + size] * rng.uniform(0.5, 1.0, size) * sign
        log2_level[:, start:start + size] += np.outer(scores[:, m], loading)
        start += size
    log2_level = log2_level[:, rng.permutation(g)]       # programme genes are scattered over the array
    other = aml[rng.permutation(n)]
    myeloid = aml.copy() if informative else other
    data = {"expression": np.exp2(log2_level), "myeloid": myeloid}
    return data, {"aml": aml, "scores": scores}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys (rows = 72 bone-marrow samples): expression (72, 2000) float64, expression level of each gene
    (columns) on the linear intensity scale (positive values); myeloid (72,) bool, True for acute myeloid
    leukaemia, False for acute lymphoblastic leukaemia (25 True, 47 False).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _labels_permuted(d, rng):
    return {**d, "myeloid": _shuffled(rng, d["myeloid"])}


def _genes_scrambled(d, rng):
    return {**d, "expression": rng.permuted(d["expression"], axis=0)}


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="the recorded leukaemia type carries no expression information: labels are the "
                              "latent types of a randomly permuted set of samples (25/47 split, expression "
                              "programmes including the type-driven bimodality unchanged)"),
    },
    controls=[
        Control("labels_permuted", ["C"], transform=_labels_permuted),
        Control("genes_scrambled", ["C"], transform=_genes_scrambled),
    ],
)
