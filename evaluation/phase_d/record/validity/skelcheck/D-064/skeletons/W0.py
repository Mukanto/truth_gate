"""D-064: Expression profiles together with clinical covariates predict tumour response in new patients: the Pearson correlation between predicted and observed response is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 80
N_GENES = 1500
N_COV = 8
N_PROG = 9              # background expression programmes unrelated to response
PROG_SIZE = 100         # genes per background programme
MODULE_SIZE = 60        # genes of the response-related programme
MODULE_LOADING = 0.65   # loading of module genes on the response-related programme
GRADE_LINK = 0.3        # correlation of the response-related programme with covariate 2 (grade)
R_CLIN = np.array([
    [1.0, 0.1, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0],
    [0.1, 1.0, 0.0, 0.0, 0.25, 0.1, 0.0, 0.0],
    [0.3, 0.0, 1.0, 0.3, 0.0, 0.0, 0.0, 0.0],
    [0.4, 0.0, 0.3, 1.0, 0.2, 0.0, 0.0, 0.0],
    [0.0, 0.25, 0.0, 0.2, 1.0, 0.0, 0.0, 0.0],
    [0.0, 0.1, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.3],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0],
])                      # correlation of the clinical covariates
W_MODULE = 0.50         # weight of the response-related programme in the true response signal
W_SIZE = -0.30          # weight of covariate 0 (tumour size)
W_AGE = 0.20            # weight of covariate 1 (age)
R2_PLUS = 0.36          # share of response variance explained by the true signal (plus)
RESP_MEAN = 30.0        # mean percentage shrinkage
RESP_SD = 22.0          # SD of percentage shrinkage (plus)


def _generate(rng, signal_on):
    lc = np.linalg.cholesky(R_CLIN)
    c = rng.standard_normal((N_PAT, N_COV)) @ lc.T
    f0 = GRADE_LINK * c[:, 2] + np.sqrt(1.0 - GRADE_LINK ** 2) * rng.standard_normal(N_PAT)
    fb = rng.standard_normal((N_PAT, N_PROG))
    perm = rng.permutation(N_GENES)
    load = np.zeros((N_PROG + 1, N_GENES))
    load[0, perm[:MODULE_SIZE]] = MODULE_LOADING
    for k in range(N_PROG):
        genes = perm[MODULE_SIZE + k * PROG_SIZE: MODULE_SIZE + (k + 1) * PROG_SIZE]
        load[k + 1, genes] = rng.uniform(0.3, 0.6, PROG_SIZE)
    factors = np.column_stack([f0, fb])
    unique_sd = np.sqrt(1.0 - (load ** 2).sum(axis=0))
    z = factors @ load + unique_sd[None, :] * rng.standard_normal((N_PAT, N_GENES))
    gene_mean = 7.0 + 1.5 * rng.standard_normal(N_GENES)
    gene_sd = np.exp(-0.5 + 0.3 * rng.standard_normal(N_GENES))
    expression = gene_mean[None, :] + gene_sd[None, :] * z
    w = np.array([W_MODULE, W_SIZE, W_AGE])
    cov3 = np.array([
        [1.0, GRADE_LINK * R_CLIN[2, 0], GRADE_LINK * R_CLIN[2, 1]],
        [GRADE_LINK * R_CLIN[2, 0], 1.0, R_CLIN[0, 1]],
        [GRADE_LINK * R_CLIN[2, 1], R_CLIN[0, 1], 1.0],
    ])
    var_s = float(w @ cov3 @ w)
    var_e = var_s * (1.0 - R2_PLUS) / R2_PLUS
    s = W_MODULE * f0 + W_SIZE * c[:, 0] + W_AGE * c[:, 1]
    e = np.sqrt(var_e) * rng.standard_normal(N_PAT)
    response = RESP_MEAN + RESP_SD * (signal_on * s + e) / np.sqrt(var_s + var_e)
    response = np.minimum(response, 100.0)
    clinical = (c - c.mean(axis=0)) / c.std(axis=0)
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "clinical": np.asarray(clinical, dtype=np.float64),
        "response": np.asarray(response, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def criterion(d):
    """Data keys: expression (80, 1500) float64, log2 expression of each gene (columns) in each patient's tumour (rows);
    clinical (80, 8) float64, standardised clinical covariates of each patient (age, tumour size and similar);
    response (80,) float64, percentage tumour shrinkage of each patient after treatment.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_response(d, rng):
    return {**d, "response": rng.permutation(d["response"])}


STUDY = Study(
    name="D-064",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="true response signal from the expression programme and the clinical covariates set to zero (response = same noise only); expression and clinical data unchanged"),
    },
    controls=[
        Control("response_permuted_across_patients", ["C"], transform=_permute_response),
    ],
)
