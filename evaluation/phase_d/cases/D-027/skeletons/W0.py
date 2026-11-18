"""D-027: The 25 measurements in X predict the outcome y for new samples: the mean absolute error of an ordinary least squares regression of y on X (with an intercept) is at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 60
N_FEATURES = 25
SIGNAL_SHARE = 0.72       # share of outcome variance explained by the linear signal in plus (population R^2)
MEAS_CORR = 0.5 * np.kron(np.eye(5), np.ones((5, 5))) + 0.5 * np.eye(N_FEATURES)   # 5 blocks of 5, r = 0.5
MEAS_CHOL = np.linalg.cholesky(MEAS_CORR)
BETA_DIR = np.array([1.0, 0.0, 0.0, -0.8, 0.0, 0.0, 0.6, 0.0, 0.0, 0.9, 0.0, 0.0, -0.5,
                     0.0, 0.0, 0.7, 0.0, 0.0, 0.4, 0.0, 0.0, 0.0, -0.6, 0.0, 0.0])
BETA = BETA_DIR * np.sqrt(SIGNAL_SHARE / (BETA_DIR @ MEAS_CORR @ BETA_DIR))
MEAS_CENTRE = np.round(np.geomspace(0.5, 400.0, N_FEATURES), 2)
MEAS_SCALE = 0.12 * MEAS_CENTRE


def _simulate(rng, scale):
    n = N_SAMPLES
    z = rng.standard_normal((n, N_FEATURES)) @ MEAS_CHOL.T
    x = MEAS_CENTRE + MEAS_SCALE * z
    y = 40.0 + 8.0 * (scale * (z @ BETA) + np.sqrt(1.0 - SIGNAL_SHARE) * rng.standard_normal(n))
    return {"X": np.asarray(x, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: X (60, 25) float, 25 continuous measurements for each sample (columns in their own units);
    y (60,) float, continuous outcome of each sample.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_y(d, rng):
    y = d["y"]
    return {**d, "y": y[rng.permutation(y.shape[0])].copy()}


STUDY = Study(
    name="D-027",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="all regression coefficients of y on X set to 0 (X carries no information on y); noise SD and measurement distribution unchanged"),
    },
    controls=[Control("y_permuted_across_samples", ["C"], transform=_permute_y)],
    relational=[("X", "y")],
)
