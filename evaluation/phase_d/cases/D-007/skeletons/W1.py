"""D-007: Gene-expression profiles measured at diagnosis predict survival time in new patients: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 50
N_GENE = 2000
N_MOD = 8            # co-expression modules; module 0 = proliferation, module 1 = immune
N_BATCH = 4          # processing batches, contiguous in diagnosis order
LOG_MEDIAN = np.log(20.0)   # median survival about 20 months
B_PROLIF = -0.45     # change in log survival per SD of the proliferation module score
B_IMMUNE = 0.20      # change in log survival per SD of the immune module score
SIGMA = 0.62         # residual SD of log survival


def _world(rng, effect):
    n, g = N_PAT, N_GENE
    gene_mean = rng.uniform(4.0, 12.0, g)
    gene_sd = np.exp(rng.normal(np.log(0.6), 0.35, g))
    member = rng.random(g) < 0.6
    module = rng.integers(0, N_MOD, g)
    h2 = np.where(member, rng.uniform(0.2, 0.6, g), 0.0)
    sign = np.where(rng.random(g) < 0.8, 1.0, -1.0)
    load = sign * np.sqrt(h2)
    factors = rng.standard_normal((n, N_MOD))
    resid = rng.standard_normal((n, g))
    z = load * factors[:, module] + np.sqrt(1.0 - h2) * resid
    batch = np.repeat(np.arange(N_BATCH), -(-n // N_BATCH))[:n]
    batch_shift = rng.normal(0.0, 0.3, (N_BATCH, g)) * gene_sd
    norm_shift = rng.normal(0.0, 0.15, n)
    expression = gene_mean + gene_sd * z + batch_shift[batch] + norm_shift[:, None]
    # survival is driven by the proliferation and immune module scores; in minus by independent
    # copies of those scores (same distribution, unrelated to the measured expression)
    copies = rng.standard_normal((n, 2))
    eps = rng.standard_normal(n)
    drivers = factors[:, :2] if effect else copies
    log_t = LOG_MEDIAN + B_PROLIF * drivers[:, 0] + B_IMMUNE * drivers[:, 1] + SIGMA * eps
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "survival_months": np.asarray(np.exp(log_t), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: expression (50, 2000) float64, log2 expression of each gene (columns) in each patient's tumour
    sample (rows); survival_months (50,) float64, months from diagnosis to death of each patient (observed for all).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _nonidentity_perm(rng, n):
    p = rng.permutation(n)
    if np.all(p == np.arange(n)):
        p = np.roll(p, 1)
    return p


def _shuffle_survival(d, rng):
    p = _nonidentity_perm(rng, d["survival_months"].shape[0])
    return {**d, "survival_months": d["survival_months"][p]}


STUDY = Study(
    name="D-007",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="survival driven by independent copies of the module scores: no relation between expression and survival"),
    },
    controls=[Control("survival_shuffled_across_patients", ["C"], transform=_shuffle_survival)],
)
