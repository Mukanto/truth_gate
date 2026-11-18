"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIES = 12
N_IND = 30
# true within-species partial correlation of (log) femur and humerus given body length; 11 of 12 are >= 0.2
RHO = np.array([0.55, 0.30, 0.45, 0.38, 0.12, 0.50, 0.42, 0.33, 0.60, 0.25, 0.47, 0.36])
BL_MIN = 80.0                  # smallest species mean head-and-body length (mm)
BL_RANGE = 5.0                 # largest / smallest species mean (80 to 400 mm)


def _generate(rng, rho):
    s, n = N_SPECIES, N_IND
    log_mu = np.log(BL_MIN) + np.log(BL_RANGE) * rng.random(s)
    log_fem_ratio = np.log(0.26) + 0.12 * rng.standard_normal(s)
    log_hum_ratio = np.log(0.82) + 0.08 * rng.standard_normal(s)
    slope_f = 0.95 + 0.08 * rng.standard_normal(s)
    slope_h = 0.90 + 0.08 * rng.standard_normal(s)
    sd_bl = 0.05 + 0.04 * rng.random(s)
    sd_f = 0.040 + 0.015 * rng.random(s)
    sd_h = 0.045 + 0.015 * rng.random(s)
    male = rng.random((s, n)) < 0.5
    dev = 0.04 * (male.astype(np.float64) - 0.5) + sd_bl[:, None] * rng.standard_normal((s, n))
    z1 = rng.standard_normal((s, n))
    z2 = rng.standard_normal((s, n))
    r = rho[:, None]
    log_bl = log_mu[:, None] + dev
    log_f = log_mu[:, None] + log_fem_ratio[:, None] + slope_f[:, None] * dev + sd_f[:, None] * z1
    log_h = (log_mu[:, None] + log_fem_ratio[:, None] + log_hum_ratio[:, None] + slope_h[:, None] * dev
             + sd_h[:, None] * (r * z1 + np.sqrt(1.0 - r ** 2) * z2))
    return {
        "femur": np.asarray(np.exp(log_f), dtype=np.float64),
        "humerus": np.asarray(np.exp(log_h), dtype=np.float64),
        "body_length": np.asarray(np.exp(log_bl), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Within each species both bones scale with body length; their residuals given body length are correlated with
    a species-specific partial correlation (mean 0.40, 11 of 12 species at least 0.2). Species differ widely in
    size, bone proportions and variances."""
    return _generate(rng, RHO)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    The within-species partial correlation of femur and humerus given body length is 0 in every species; the
    allometry on body length, the species structure and all variances are as in plus."""
    return _generate(rng, np.zeros(N_SPECIES))


def criterion(d):
    """Data keys: femur (12, 30) float, femur length (mm) of individual i of species s; humerus (12, 30) float,
    humerus length (mm) of the same individual; body_length (12, 30) float, head-and-body length (mm) of the same
    individual. Axis 0 is the species, axis 1 the individual within the species.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _swap_humerus_between_length_neighbours(d, rng):
    bl = d["body_length"]
    hum = d["humerus"]
    idx = np.argsort(bl, axis=1)
    rows = np.arange(bl.shape[0])[:, None]
    a = idx[:, 0::2]
    b = idx[:, 1::2]
    out = hum.copy()
    out[rows, a] = hum[rows, b]
    out[rows, b] = hum[rows, a]
    return {**d, "humerus": out}


def _permute_humerus_within_species(d, rng):
    hum = d["humerus"]
    order = np.argsort(rng.random(hum.shape), axis=1)
    out = np.take_along_axis(hum, order, axis=1)
    if np.array_equal(out, hum):
        out = np.roll(hum, 1, axis=1)
    return {**d, "humerus": out}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-species partial correlation of femur and humerus given body length set to 0 in all 12 species"),
    },
    controls=[
        Control("humerus_swapped_between_body_length_neighbours", ["C"], transform=_swap_humerus_between_length_neighbours),
        Control("humerus_permuted_within_species", ["C"], transform=_permute_humerus_within_species),
    ],
)
