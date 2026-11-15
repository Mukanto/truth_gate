"""C32: A shrunken-centroid classifier built from the 1000 gene-expression measurements separates patients who respond to the treatment from those who do not, with an area under the ROC curve of at least 0.65 on new patients."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 40
N_GENES = 1000
N_RESPONDERS = 16
N_INFORMATIVE = 30
SHIFT = 1.1          # responder minus non-responder difference of an informative gene, in units of its residual SD
N_FACTORS = 5        # shared sources of variation unrelated to response (batch, purity, proliferation ...)
LOADING_SD = 0.3


def _cohort(rng, shift):
    responder = np.zeros(N_PATIENTS, dtype=bool)
    responder[rng.choice(N_PATIENTS, N_RESPONDERS, replace=False)] = True
    gene_mean = rng.normal(7.0, 1.5, N_GENES)
    gene_sd = np.exp(rng.normal(-0.3, 0.35, N_GENES))
    factors = rng.normal(0.0, 1.0, (N_PATIENTS, N_FACTORS))
    loadings = rng.normal(0.0, LOADING_SD, (N_FACTORS, N_GENES))
    z = factors @ loadings + rng.normal(0.0, 1.0, (N_PATIENTS, N_GENES))
    informative = rng.choice(N_GENES, N_INFORMATIVE, replace=False)
    sign = rng.choice(np.array([-1.0, 1.0]), N_INFORMATIVE)
    delta = np.zeros(N_GENES)
    delta[informative] = sign * shift
    z = z + responder[:, None] * delta[None, :]
    expression = gene_mean[None, :] + gene_sd[None, :] * z
    return {"expression": expression.astype(np.float64), "responder": responder}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _cohort(rng, SHIFT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _cohort(rng, 0.0)


def _permute_responder(d, rng):
    return {**d, "responder": rng.permutation(d["responder"])}


def criterion(d):
    """Data keys: expression, float (40, 1000) = (patients, genes), expression level of each gene in the tumour of
    each patient; responder, bool (40,), True when the patient responds to the treatment.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C32",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the expression difference between responders and non-responders is set to 0 for every gene"),
    },
    controls=[Control("permute_responder", ["C"], transform=_permute_responder)],
)
