"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 1200
N_DISTRICTS = 150
COV_SHARE = 0.10        # share of outcome variance from the three covariates in plus
DISTRICT_SHARE = 0.07   # share of outcome variance from district effects in plus (ICC-like)
NOISE_SHARE = 0.83      # share of outcome variance from individual noise (unchanged in minus)
COV_CORR = np.array([[1.00, 0.10, 0.35],
                     [0.10, 1.00, 0.25],
                     [0.35, 0.25, 1.00]])   # individual correlation of standardised age, BMI, SBP
COV_CHOL = np.linalg.cholesky(COV_CORR)
DISTRICT_SHIFT = np.array([0.0, 0.3, 0.2])  # loading of the covariates on district deprivation
BETA_DIR = np.array([1.0, 0.8, 0.7])
BETA = BETA_DIR * np.sqrt(COV_SHARE / (BETA_DIR @ COV_CORR @ BETA_DIR))


def _simulate(rng, scale):
    n, k = N_SAMPLES, N_DISTRICTS
    weights = np.exp(rng.normal(0.0, 0.6, k))
    district = rng.choice(k, size=n, p=weights / weights.sum())
    deprivation = rng.standard_normal(k)
    ind = rng.standard_normal((n, 3)) @ COV_CHOL.T
    z = ind * np.sqrt(1.0 - DISTRICT_SHIFT ** 2) + deprivation[district][:, None] * DISTRICT_SHIFT
    age = np.clip(55.0 + 14.0 * z[:, 0], 18.0, 95.0)
    bmi = 27.0 * np.exp(0.16 * z[:, 1])
    sbp = 132.0 + 17.0 * z[:, 2]
    district_effect = np.sqrt(DISTRICT_SHARE) * (0.6 * deprivation + 0.8 * rng.standard_normal(k))
    signal = z @ BETA + district_effect[district]
    y = 50.0 + 10.0 * (scale * signal + np.sqrt(NOISE_SHARE) * rng.standard_normal(n))
    category = np.zeros((n, k), dtype=bool)
    category[np.arange(n), district] = True
    return {
        "category": category,
        "covariates": np.asarray(np.column_stack([age, bmi, sbp]), dtype=np.float64),
        "y": np.asarray(y, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: category (1200, 150) bool, True where the patient's home postal district is the district of that
    column (exactly one True per row); covariates (1200, 3) float, age (years), body-mass index (kg/m2) and systolic
    pressure (mmHg) of each patient; y (1200,) float, continuous health outcome of each patient.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_y(d, rng):
    y = d["y"]
    return {**d, "y": y[rng.permutation(y.shape[0])].copy()}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="covariate coefficients and district effects on y set to 0 (no predictive information); individual noise, district sizes and covariate distributions unchanged"),
    },
    controls=[Control("y_permuted_across_patients", ["C"], transform=_permute_y)],
    relational=[("covariates", "y")],
)
