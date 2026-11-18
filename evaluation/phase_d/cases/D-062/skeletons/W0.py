"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIES = 12
N_IND = 30
BODY_MEDIAN = 150.0     # median species mean head-and-body length, mm
BODY_LOG_SD = 0.5       # spread of species mean body length (log scale)
BODY_CV = 0.08          # within-species coefficient of variation of body length
FEMUR_RATIO = 0.22      # femur length / body length, mean over species
FEMUR_RATIO_SD = 0.03
HUMERUS_RATIO = 0.18    # humerus length / body length, mean over species
HUMERUS_RATIO_SD = 0.025
RESID_CV = 0.045        # SD of limb length at a given body length, relative to the species mean limb length
RHO_MEAN = 0.36         # mean within-species partial correlation of femur and humerus given body length (plus)
RHO_SD = 0.07           # between-species SD of that partial correlation
BLOCK = 5


def _generate(rng, rho_on):
    mu = BODY_MEDIAN * np.exp(BODY_LOG_SD * rng.standard_normal(N_SPECIES))
    body = mu[:, None] * (1.0 + BODY_CV * rng.standard_normal((N_SPECIES, N_IND)))
    rf = FEMUR_RATIO + FEMUR_RATIO_SD * rng.standard_normal(N_SPECIES)
    rh = HUMERUS_RATIO + HUMERUS_RATIO_SD * rng.standard_normal(N_SPECIES)
    rho = np.clip(RHO_MEAN + RHO_SD * rng.standard_normal(N_SPECIES), 0.15, 0.6) * rho_on
    z1 = rng.standard_normal((N_SPECIES, N_IND))
    z2 = rng.standard_normal((N_SPECIES, N_IND))
    ef = z1
    eh = rho[:, None] * z1 + np.sqrt(1.0 - rho ** 2)[:, None] * z2
    femur = rf[:, None] * body + RESID_CV * (rf * mu)[:, None] * ef
    humerus = rh[:, None] * body + RESID_CV * (rh * mu)[:, None] * eh
    return {
        "femur": np.asarray(femur, dtype=np.float64),
        "humerus": np.asarray(humerus, dtype=np.float64),
        "body_length": np.asarray(body, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def criterion(d):
    """Data keys: femur (12, 30) float64, femur length in mm, rows are species, columns individuals;
    humerus (12, 30) float64, humerus length in mm of the same individuals;
    body_length (12, 30) float64, head-and-body length in mm of the same individuals.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _matched_rotate(values, covariate, rng, block):
    rows, n = values.shape
    order = np.argsort(covariate, axis=1)
    sorted_vals = np.take_along_axis(values, order, axis=1)
    nb = n // block
    shift = rng.integers(1, block, size=(rows, nb))
    pos = np.arange(n)
    blk = pos // block
    src = blk[None, :] * block + (pos[None, :] % block + shift[:, blk]) % block
    rotated = np.take_along_axis(sorted_vals, src, axis=1)
    out = np.empty_like(values)
    np.put_along_axis(out, order, rotated, axis=1)
    return out


def _permute_humerus_within_species(d, rng):
    idx = np.argsort(rng.random((N_SPECIES, N_IND)), axis=1)
    return {**d, "humerus": np.take_along_axis(d["humerus"], idx, axis=1)}


def _rotate_humerus_length_matched(d, rng):
    return {**d, "humerus": _matched_rotate(d["humerus"], d["body_length"], rng, BLOCK)}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-species partial correlation of femur and humerus given body length set to zero in every species; size scaling and noise unchanged"),
    },
    controls=[
        Control("humerus_permuted_within_species", ["C"], transform=_permute_humerus_within_species),
        Control("humerus_exchanged_among_length_matched_individuals", ["C"], transform=_rotate_humerus_length_matched),
    ],
)
