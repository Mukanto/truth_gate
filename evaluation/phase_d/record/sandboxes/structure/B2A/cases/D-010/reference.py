"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, D = 1200, 150
RCOV = np.array([[1.0, 0.10, 0.35], [0.10, 1.0, 0.30], [0.35, 0.30, 1.0]])   # age, BMI, systolic pressure
CHOL = np.linalg.cholesky(RCOV)
DIST_SHIFT_VAR = 0.09     # district-level share of the covariates' variance
BETA = np.array([0.24, 0.18, 0.10])   # effects per sd of age, BMI, pressure
U_VAR = 0.06              # district random-effect variance (ICC of y about 0.06)
NOISE_VAR = 0.81


def _draw(rng):
    w = rng.gamma(2.0, size=D)
    counts = 1 + rng.multinomial(N - D, w / w.sum())
    did = rng.permutation(np.repeat(np.arange(D), counts))
    category = np.zeros((N, D), dtype=bool)
    category[np.arange(N), did] = True
    shift = rng.standard_normal((D, 3))
    zc = np.sqrt(1.0 - DIST_SHIFT_VAR) * (rng.standard_normal((N, 3)) @ CHOL.T) + np.sqrt(DIST_SHIFT_VAR) * shift[did]
    cov = np.empty((N, 3))
    cov[:, 0] = 52.0 + 14.0 * zc[:, 0]
    cov[:, 1] = 27.0 + 4.5 * zc[:, 1]
    cov[:, 2] = 130.0 + 16.0 * zc[:, 2]
    u = np.sqrt(U_VAR) * rng.standard_normal(D)
    sig = zc @ BETA + u[did]
    noise = np.sqrt(NOISE_VAR) * rng.standard_normal(N)
    return category, cov, sig, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    category, cov, sig, noise = _draw(rng)
    return {"category": category, "covariates": cov, "y": sig + noise}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    category, cov, sig, noise = _draw(rng)
    return {"category": category, "covariates": cov, "y": sig[rng.permutation(N)] + noise}


def criterion(d):
    """Data keys: category (samples, categories) = (1200, 150), bool, True where the patient's home postal district
    is the district of that column (one True per row); covariates (samples, features) = (1200, 3), age, body-mass
    index, systolic pressure; y (samples,) = (1200,), continuous health outcome.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"category": np.array(d["category"]), "covariates": np.array(d["covariates"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the covariate and district contributions to y are reassigned to other patients (permuted), so y carries no information on district or covariates; the variance of y, the noise, the district sizes and the covariates are unchanged"),
    },
    controls=[Control("D-010", ["C"], transform=permute_y)],
)
