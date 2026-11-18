"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 72
G = 2000
N_AML = 25
N_BATCH0 = 38        # first collection series; the remaining 34 samples form the second
N_MOD = 8            # co-expression modules unrelated to lineage
N_PROG = 40          # co-regulated lineage-programme marker genes
N_WEAK = 40          # genes with small independent differences between the types
DELTA = 2.4          # AML-ALL difference of the programme score, in within-type SD units


def _labels(rng):
    lab = np.zeros(N, dtype=bool)
    lab[rng.permutation(N)[:N_AML]] = True
    return lab


def _world(rng, effect):
    myeloid = _labels(rng)
    copy_labels = _labels(rng)          # independent copy with the same class sizes: drives expression in minus
    gene_mean = rng.uniform(4.0, 12.0, G)
    gene_sd = np.exp(rng.normal(np.log(0.6), 0.35, G))
    roles = rng.permutation(G)
    prog = roles[:N_PROG]
    weak = roles[N_PROG:N_PROG + N_WEAK]
    member = rng.random(G) < 0.6
    member[prog] = False
    member[weak] = False
    module = rng.integers(0, N_MOD, G)
    h2 = np.where(member, rng.uniform(0.2, 0.6, G), 0.0)
    sign = np.where(rng.random(G) < 0.8, 1.0, -1.0)
    load = sign * np.sqrt(h2)
    factors = rng.standard_normal((N, N_MOD))
    resid = rng.standard_normal((N, G))
    z = load * factors[:, module] + np.sqrt(1.0 - h2) * resid
    drive = (myeloid if effect else copy_labels).astype(np.float64) - N_AML / N
    # lineage programme: one programme score with within-type variation, shifted by type
    a = rng.uniform(0.55, 0.85, N_PROG)
    sgn = np.where(np.arange(N_PROG) % 2 == 0, 1.0, -1.0)
    prog_score = rng.standard_normal(N) + DELTA * drive
    z[:, prog] = sgn * a * prog_score[:, None] + np.sqrt(1.0 - a * a) * resid[:, prog]
    # weak, independent differences
    d_weak = rng.uniform(0.15, 0.35, N_WEAK) * np.where(rng.random(N_WEAK) < 0.5, 1.0, -1.0)
    z[:, weak] = resid[:, weak] + d_weak * drive[:, None]
    batch = (np.arange(N) >= N_BATCH0).astype(int)
    batch_shift = rng.normal(0.0, 0.3, (2, G)) * gene_sd
    norm_shift = rng.normal(0.0, 0.15, N)
    expression = gene_mean + gene_sd * z + batch_shift[batch] + norm_shift[:, None]
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "myeloid": myeloid,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: expression (72, 2000) float64, log2-scale expression level of each gene (columns) in each
    bone-marrow sample (rows); myeloid (72,) bool, True for acute myeloid leukaemia, False for acute lymphoblastic
    leukaemia.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_labels(rng, v):
    n = v.shape[0]
    for _ in range(50):
        w = v[rng.permutation(n)]
        if np.any(w != v):
            return w
    w = v.copy()
    i, j = int(np.argmax(v)), int(np.argmin(v))
    w[i], w[j] = v[j], v[i]
    if not np.any(w != v):
        w[0] = not v[0]
    return w


def _shuffle_myeloid(d, rng):
    return {**d, "myeloid": _shuffle_labels(rng, d["myeloid"])}


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="type differences in expression follow an independent copy of the labels: expression unrelated to type"),
    },
    controls=[Control("myeloid_labels_shuffled_across_samples", ["C"], transform=_shuffle_myeloid)],
)
