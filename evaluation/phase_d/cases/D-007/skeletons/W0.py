"""D-007: Gene-expression profiles measured at diagnosis predict survival time in new patients: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 50
N_GENES = 2000
# co-expressed gene programmes (disjoint gene sets); programme 0 is the prognostic proliferation programme
PROGRAMME_SIZES = (120, 200, 150, 100, 90, 80, 60, 40)
LOG_SD_TOTAL = 0.6          # total SD of log survival in plus
PROGNOSTIC_CORR = 0.72      # corr(proliferation score, log survival) in plus
NOISE_LOG_SD = LOG_SD_TOTAL * np.sqrt(1.0 - PROGNOSTIC_CORR ** 2)
PLUS_COEF = PROGNOSTIC_CORR * LOG_SD_TOTAL
MEDIAN_MONTHS = 26.0


def _simulate(rng, coef):
    n, g = N_PATIENTS, N_GENES
    gene_mean = np.clip(rng.normal(7.0, 1.8, g), 2.0, 13.0)
    gene_sd = np.exp(rng.normal(np.log(0.6), 0.4, g))
    k = len(PROGRAMME_SIZES)
    factors = rng.standard_normal((n, k))
    order = rng.permutation(g)
    loading = np.zeros((k, g))
    start = 0
    for j in range(k):
        size = PROGRAMME_SIZES[j]
        idx = order[start:start + size]
        share = rng.uniform(0.3, 0.75, size)
        sign = np.where(rng.random(size) < 0.8, 1.0, -1.0)
        loading[j, idx] = sign * np.sqrt(share)
        start += size
    unique_sd = np.sqrt(1.0 - (loading ** 2).sum(axis=0))
    z = factors @ loading + rng.standard_normal((n, g)) * unique_sd
    expression = gene_mean + gene_sd * z
    log_surv = np.log(MEDIAN_MONTHS) - coef * factors[:, 0] + NOISE_LOG_SD * rng.standard_normal(n)
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "survival_months": np.asarray(np.exp(log_surv), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_COEF)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: expression (50, 2000) float, log2 expression level of each gene in each patient's tumour sample;
    survival_months (50,) float, months from diagnosis to death, observed for every patient.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_survival(d, rng):
    surv = d["survival_months"]
    return {**d, "survival_months": surv[rng.permutation(surv.shape[0])].copy()}


STUDY = Study(
    name="D-007",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="coefficient of the proliferation programme on log survival set to 0 (expression carries no survival information); residual survival noise and all expression structure unchanged"),
    },
    controls=[Control("survival_permuted_across_patients", ["C"], transform=_permute_survival)],
    relational=[("expression", "survival_months")],
)
