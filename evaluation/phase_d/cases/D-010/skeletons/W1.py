"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1200
N_DIST = 150
REF_MEAN = np.array([57.0, 27.5, 128.0])   # reference means of age, BMI, SBP (for standardising)
REF_SD = np.array([14.0, 4.66, 15.8])      # reference SDs of age, BMI, SBP
B_COV = np.array([0.20, 0.12, 0.12])       # effect on standardised y per SD of age, BMI, SBP
TAU = 0.245                                # SD of the district effect (district ICC about 0.06)
SIGMA = np.sqrt(0.845)                     # residual SD (standardised scale)


def _patients(rng, pop, depriv):
    dist = rng.choice(N_DIST, N, p=pop)
    age = np.clip(rng.normal(57.0, 14.0, N), 18.0, 95.0)
    bmi = np.clip(27.5 + 1.2 * depriv[dist] + rng.normal(0.0, 4.5, N), 15.0, 60.0)
    sbp = np.clip(128.0 + 0.45 * (age - 57.0) + 0.7 * (bmi - 27.5) + 2.0 * depriv[dist]
                  + rng.normal(0.0, 14.0, N), 80.0, 230.0)
    return dist, np.column_stack([age, bmi, sbp])


def _world(rng, effect):
    pop = np.exp(rng.normal(0.0, 0.8, N_DIST))
    pop = pop / pop.sum()
    depriv = rng.standard_normal(N_DIST)
    u_dist = 0.6 * depriv + 0.8 * rng.standard_normal(N_DIST)
    dist, cov = _patients(rng, pop, depriv)
    # an independent copy of the cohort (same districts, same covariate distribution): drives y in minus
    dist_copy, cov_copy = _patients(rng, pop, depriv)
    eps = rng.standard_normal(N)
    d_y, c_y = (dist, cov) if effect else (dist_copy, cov_copy)
    lin = ((c_y - REF_MEAN) / REF_SD) @ B_COV + TAU * u_dist[d_y] + SIGMA * eps
    y = 60.0 + 12.0 * lin
    category = np.zeros((N, N_DIST), dtype=bool)
    category[np.arange(N), dist] = True
    return {
        "category": category,
        "covariates": np.asarray(cov, dtype=np.float64),
        "y": np.asarray(y, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: category (1200, 150) bool, True where the patient's (row) home postal district is the district of
    that column (one True per row); covariates (1200, 3) float64, age in
    years, body-mass index in kg/m^2 and systolic pressure in mmHg of each patient; y (1200,) float64, continuous
    health outcome of each patient.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _nonidentity_perm(rng, n):
    p = rng.permutation(n)
    if np.all(p == np.arange(n)):
        p = np.roll(p, 1)
    return p


def _shuffle_y(d, rng):
    p = _nonidentity_perm(rng, d["y"].shape[0])
    return {**d, "y": d["y"][p]}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y driven by an independent copy of the cohort's districts and covariates: no predictive information"),
    },
    controls=[Control("y_shuffled_across_patients", ["C"], transform=_shuffle_y)],
)
