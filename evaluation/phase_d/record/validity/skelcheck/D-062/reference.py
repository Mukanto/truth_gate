"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIES = 12
N_IND = 30
BODY_MEDIAN = 150.0
BODY_SPECIES_SD = 0.4
FEMUR_RATIO = 0.20
HUMERUS_RATIO = 0.17
RATIO_SPECIES_SD = 0.10
CV_BASE = 0.05
CV_SPECIES_SD = 0.10
R_FEMUR_BODY = 0.4
R_HUMERUS_BODY = 0.4
PARTIAL_SD = 0.15


def _gen(rng, partial_mean):
    body_mu = BODY_MEDIAN * np.exp(BODY_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    fem_mu = body_mu * FEMUR_RATIO * np.exp(RATIO_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    hum_mu = body_mu * HUMERUS_RATIO * np.exp(RATIO_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    cv_b = CV_BASE * np.exp(CV_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    cv_f = CV_BASE * np.exp(CV_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    cv_h = CV_BASE * np.exp(CV_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    partial = partial_mean * np.ones((N_SPECIES, 1)) + PARTIAL_SD * (partial_mean != 0.0) * rng.standard_normal((N_SPECIES, 1))
    partial = np.clip(partial, -0.9, 0.9)
    zb = rng.standard_normal((N_SPECIES, N_IND))
    u = rng.standard_normal((N_SPECIES, N_IND))
    w = rng.standard_normal((N_SPECIES, N_IND))
    zf = R_FEMUR_BODY * zb + np.sqrt(1.0 - R_FEMUR_BODY ** 2) * u
    zh = R_HUMERUS_BODY * zb + np.sqrt(1.0 - R_HUMERUS_BODY ** 2) * (partial * u + np.sqrt(1.0 - partial ** 2) * w)
    body = body_mu * (1.0 + cv_b * zb)
    femur = fem_mu * (1.0 + cv_f * zf)
    humerus = hum_mu * (1.0 + cv_h * zh)
    return {
        "femur": np.asarray(femur, dtype=float),
        "humerus": np.asarray(humerus, dtype=float),
        "body_length": np.asarray(body, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.4)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: femur (12, 30) float, femur length in mm, species x individuals;
    humerus (12, 30) float, humerus length in mm;
    body_length (12, 30) float, head-and-body length in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_humerus_within_species(d, rng):
    z = np.asarray(d["body_length"], dtype=float)
    h = np.asarray(d["humerus"], dtype=float)
    s, k = h.shape
    block = 6
    order = np.argsort(z, axis=1, kind="stable")
    out = h.copy()
    for i in range(s):
        for start in range(0, k, block):
            idx = order[i, start:start + block]
            out[i, idx] = h[i, idx[rng.permutation(idx.shape[0])]]
    return {"femur": np.asarray(d["femur"], dtype=float), "humerus": out, "body_length": z}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="within-species partial correlation of femur and humerus given body length set from a mean of 0.4 (SD 0.15 across species) to 0 in every species"),
    },
    controls=[Control("permute_humerus_within_species", ["C"], transform=permute_humerus_within_species)],
)
