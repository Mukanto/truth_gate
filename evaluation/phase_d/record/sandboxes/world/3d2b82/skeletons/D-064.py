"""D-064: Expression profiles together with clinical covariates predict tumour response in new patients: the Pearson correlation between predicted and observed response is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_N = 80
_G = 1500
_K = 10
_Q = 8
_MOD_SIZE = 75
_BATCH = 20
# Clinical latent correlation: 0 age, 1 tumour size, 2 grade, 3 stage, 4 performance status, 5 BMI,
# 6 sex (dichotomised), 7 nodal status (dichotomised).
_R_C = np.array([
    [1.00, 0.05, 0.00, 0.05, 0.30, 0.10, 0.00, 0.00],
    [0.05, 1.00, 0.20, 0.50, 0.15, 0.00, 0.05, 0.30],
    [0.00, 0.20, 1.00, 0.25, 0.10, 0.00, 0.00, 0.20],
    [0.05, 0.50, 0.25, 1.00, 0.20, 0.00, 0.00, 0.45],
    [0.30, 0.15, 0.10, 0.20, 1.00, 0.05, 0.00, 0.10],
    [0.10, 0.00, 0.00, 0.00, 0.05, 1.00, 0.10, 0.00],
    [0.00, 0.05, 0.00, 0.00, 0.00, 0.10, 1.00, 0.00],
    [0.00, 0.30, 0.20, 0.45, 0.10, 0.00, 0.00, 1.00],
])
_L_C = np.linalg.cholesky(_R_C)
_A_SIZE = 0.30    # tumour size loads on the proliferation module (factor 0)
_A_GRADE = 0.35   # grade loads on the proliferation module
# Response signal: lp = -0.30 size + 0.20 grade + 0.50 sensitivity module (factor 1) + 0.25 proliferation (factor 0)
_B = np.array([-0.30, 0.20, 0.50, 0.25])
_C12 = np.sqrt(1 - _A_SIZE ** 2) * np.sqrt(1 - _A_GRADE ** 2) * _R_C[1, 2] + _A_SIZE * _A_GRADE
_SIG = np.array([
    [1.0, _C12, 0.0, _A_SIZE],
    [_C12, 1.0, 0.0, _A_GRADE],
    [0.0, 0.0, 1.0, 0.0],
    [_A_SIZE, _A_GRADE, 0.0, 1.0],
])
_LP_SD = float(np.sqrt(_B @ _SIG @ _B))
_R2 = 0.36
_MODULE_OF_GENE = np.minimum(np.arange(_G) // _MOD_SIZE, _K - 1)
_IN_MODULE = np.arange(_G) < _K * _MOD_SIZE


def _clinical_latent(rng, f0):
    c = rng.standard_normal((_N, _Q)) @ _L_C.T
    c[:, 1] = np.sqrt(1 - _A_SIZE ** 2) * c[:, 1] + _A_SIZE * f0
    c[:, 2] = np.sqrt(1 - _A_GRADE ** 2) * c[:, 2] + _A_GRADE * f0
    return c


def _generate(rng, informative):
    # Co-expression modules: 10 latent factors, 75 genes each; 750 genes outside any module.
    f = rng.standard_normal((_N, _K))
    load = np.where(_IN_MODULE, rng.uniform(0.40, 0.85, _G), 0.0)
    gene_mean = rng.uniform(3.0, 12.0, _G)
    gene_sd = np.clip(np.exp(np.log(0.6) + 0.4 * rng.standard_normal(_G)), 0.15, 2.0)
    noise = rng.standard_normal((_N, _G))
    # Processing batches: 4 consecutive batches of 20 patients, gene-specific shifts.
    batch = np.repeat(0.25 * gene_sd[None, :] * rng.standard_normal((_N // _BATCH, _G)), _BATCH, axis=0)
    z = f[:, _MODULE_OF_GENE] * load[None, :] + noise * np.sqrt(1.0 - load ** 2)[None, :]
    expression = gene_mean[None, :] + gene_sd[None, :] * z + batch
    c_obs = _clinical_latent(rng, f[:, 0])
    # Independent copy of the response drivers (used only where X carries no information).
    f_other = rng.standard_normal((_N, 2))
    c_other = _clinical_latent(rng, f_other[:, 0])
    noise_resp = rng.standard_normal(_N)
    if informative:
        drivers = np.column_stack([c_obs[:, 1], c_obs[:, 2], f[:, 1], f[:, 0]])
    else:
        drivers = np.column_stack([c_other[:, 1], c_other[:, 2], f_other[:, 1], f_other[:, 0]])
    lp = drivers @ _B / _LP_SD
    response = 30.0 + 25.0 * (np.sqrt(_R2) * lp + np.sqrt(1.0 - _R2) * noise_resp)
    response = np.minimum(response, 100.0)
    # Recorded clinical covariates: sex and nodal status are binary, then all are standardised.
    clinical = c_obs.copy()
    clinical[:, 6] = (c_obs[:, 6] > 0.0).astype(np.float64)
    clinical[:, 7] = (c_obs[:, 7] > 0.3).astype(np.float64)
    sd = clinical.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    clinical = (clinical - clinical.mean(axis=0)) / sd
    return {"expression": expression.astype(np.float64), "clinical": clinical.astype(np.float64),
            "response": response.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: expression (80, 1500) float, log2 expression of each gene (columns) in each patient's tumour
    sample (rows); clinical (80, 8) float, standardised clinical covariates of the same patients (age, tumour
    size and similar); response (80,) float, percentage tumour shrinkage after treatment of the same patients.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_response_within_batch(d, rng):
    r = d["response"]
    nb = r.shape[0] // _BATCH
    idx = np.argsort(rng.random((nb, _BATCH)), axis=1)
    ident = np.all(idx == np.arange(_BATCH)[None, :], axis=1)
    idx[ident] = np.roll(np.arange(_BATCH), 1)
    new = np.take_along_axis(r.reshape(nb, _BATCH), idx, axis=1).reshape(r.shape[0])
    return {**d, "response": new}


STUDY = Study(
    name="D-064",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="response driven by an independent copy of the clinical and expression drivers (no predictive information); response distribution and all X structure unchanged"),
    },
    controls=[Control("response_permuted_within_batch", ["C"], transform=_permute_response_within_batch)],
    relational=[("expression", "response")],
)
