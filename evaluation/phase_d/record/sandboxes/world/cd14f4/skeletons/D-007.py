"""D-007: Gene-expression profiles measured at diagnosis predict survival time in new patients: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_PATIENTS = 50
N_GENES = 2000
# Co-expressed gene programmes (number of member genes). Programme 0 is a prognostic, proliferation-like
# programme; the others (immune, stromal, ...) vary between tumours but carry no survival information.
PROGRAMME_SIZES = (120, 220, 260, 150, 100, 80)
LOG_MEDIAN_MONTHS = 3.0910   # log(22): median survival about 22 months
B_PROGNOSTIC = 0.46          # change in log survival per SD of the prognostic programme
SD_LOG_RESIDUAL = 0.59       # survival variation not carried by the tumour expression (log scale)


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _draw(rng, informative):
    """One cohort. Returns (data, truth); truth holds the latent programme scores used for checks."""
    n, g = N_PATIENTS, N_GENES
    k = len(PROGRAMME_SIZES)
    mu = rng.uniform(4.0, 12.0, g)                        # baseline log2 level of each gene
    sd = np.exp(rng.normal(np.log(0.45), 0.35, g))        # gene-specific residual SD (log2 units)
    scores = rng.standard_normal((n, k))                  # programme activity of each tumour
    scores[:, 2] = 0.4 * scores[:, 1] + np.sqrt(0.84) * scores[:, 2]   # immune and stromal programmes correlate
    expression = mu + sd * rng.standard_normal((n, g))
    start = 0
    for m in range(k):
        size = PROGRAMME_SIZES[m]
        sign = np.where(rng.random(size) < 0.85, 1.0, -1.0)
        loading = sd[start:start + size] * rng.uniform(0.6, 1.1, size) * sign
        expression[:, start:start + size] += np.outer(scores[:, m], loading)
        start += size
    expression = expression[:, rng.permutation(g)]       # programme genes are scattered over the array
    shuffle = rng.permutation(n)
    prognostic = scores[:, 0] if informative else scores[shuffle, 0]
    log_months = LOG_MEDIAN_MONTHS + B_PROGNOSTIC * prognostic + SD_LOG_RESIDUAL * rng.standard_normal(n)
    data = {"expression": expression, "survival_months": np.exp(log_months)}
    return data, {"prognostic": prognostic, "scores": scores}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys: expression (50, 2000) float64, log2 expression level of each gene (columns) in each
    patient's tumour sample (rows); survival_months (50,) float64, months from diagnosis to death,
    observed for every patient (no censoring), rows aligned with expression.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _survival_permuted(d, rng):
    return {**d, "survival_months": _shuffled(rng, d["survival_months"])}


def _genes_scrambled(d, rng):
    return {**d, "expression": rng.permuted(d["expression"], axis=0)}


STUDY = Study(
    name="D-007",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="survival carries no expression information: the prognostic programme score entering "
                              "log survival is taken from a randomly permuted patient (survival marginal, residual "
                              "noise and expression structure unchanged)"),
    },
    controls=[
        Control("survival_permuted", ["C"], transform=_survival_permuted),
        Control("genes_scrambled", ["C"], transform=_genes_scrambled),
    ],
)
