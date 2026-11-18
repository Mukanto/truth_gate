"""D-007: Gene-expression profiles measured at diagnosis predict survival time in new patients: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 50
N_GENE = 2000
N_MOD = 8
MOD_SIZE = 120
LOG_MEDIAN = 3.4012  # log(30 months)
BETA = 0.50  # log-survival change per SD of the prognostic expression programme
SIGMA = 0.55  # residual SD of log survival


def _cohort(rng, linked):
    """Tumour expression with co-expression modules, and survival times.

    Module 0 is a prognostic programme (e.g. proliferation). When linked, log survival
    depends on that programme's latent activity; otherwise on an independent latent copy
    with the same distribution, so both marginals are unchanged.
    """
    n, g = N_PAT, N_GENE
    gene_mean = rng.uniform(5.0, 11.0, g)
    gene_sd = rng.uniform(0.3, 0.8, g)
    factors = rng.standard_normal((n, N_MOD))
    order = rng.permutation(g)
    coef = np.zeros((N_MOD, g))
    for k in range(N_MOD):
        idx = order[k * MOD_SIZE:(k + 1) * MOD_SIZE]
        sign = np.where(rng.random(MOD_SIZE) < 0.8, 1.0, -1.0)
        coef[k, idx] = sign * rng.uniform(0.4, 0.9, MOD_SIZE)
    offset = rng.normal(0.0, 0.1, (n, 1))  # residual sample-level normalisation shift
    expression = gene_mean + factors @ coef + gene_sd * rng.standard_normal((n, g)) + offset
    independent = rng.standard_normal(n)
    eps = rng.standard_normal(n)
    driver = factors[:, 0] if linked else independent
    survival = np.exp(LOG_MEDIAN + BETA * driver + SIGMA * eps)
    return {"expression": expression.astype(np.float64), "survival_months": survival.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _cohort(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _cohort(rng, False)


def criterion(d):
    """Data keys: expression (50, 2000) float, log2 expression level of each gene in each patient's tumour sample;
    survival_months (50,) float, months from diagnosis to death, observed for every patient.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_survival(d, rng):
    return {**d, "survival_months": d["survival_months"][rng.permutation(N_PAT)]}


STUDY = Study(
    name="D-007",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="survival depends on an independent copy of the prognostic latent, not on the expressed programme (no predictive information; marginals unchanged)"),
    },
    controls=[Control("survival_shuffled_across_patients", ["C"], transform=_shuffle_survival)],
)
