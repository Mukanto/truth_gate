"""D-027: The 25 measurements in X predict the outcome y for new samples: the mean absolute error of an ordinary least squares regression of y on X (with an intercept) is at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_SAMPLES = 60
N_FEATURES = 25
R2_TRUE = 0.70                # share of outcome variance carried by the linear predictor in the population
# Measurements come in three correlated panels (latent factors); loading of each measurement on its panel.
PANEL = np.array([0] * 9 + [1] * 8 + [2] * 8)
PANEL_LOADING = np.array([0.6, 0.55, 0.5])
# True regression weights on the standardised measurements (six moderate, six small, thirteen zero).
BETA = np.array([0.50, 0.0, 0.12, 0.0, -0.40, 0.0, 0.12, 0.0, 0.0,
                 0.35, 0.0, 0.12, 0.0, 0.30, 0.0, 0.12, 0.0,
                 -0.30, 0.0, 0.12, 0.0, 0.25, 0.0, 0.12, 0.0])
X_MEAN = 10.0 * (1.0 + np.arange(N_FEATURES) % 7)
X_SD = 1.0 + 0.5 * (np.arange(N_FEATURES) % 5)
Y_MEAN, Y_SCALE = 100.0, 15.0


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _covariance():
    """Population correlation matrix of the standardised measurements."""
    lam = PANEL_LOADING[PANEL]
    same = PANEL[:, None] == PANEL[None, :]
    cov = np.where(same, np.outer(lam, lam), 0.0)
    np.fill_diagonal(cov, 1.0)
    return cov


def _draw(rng, informative):
    """One sample set. Returns (data, truth); truth holds the true linear predictor."""
    n, p = N_SAMPLES, N_FEATURES
    lam = PANEL_LOADING[PANEL]
    factors = rng.standard_normal((n, 3))
    z = factors[:, PANEL] * lam + np.sqrt(1.0 - lam ** 2) * rng.standard_normal((n, p))
    x = X_MEAN + X_SD * z
    signal = z @ BETA / np.sqrt(BETA @ _covariance() @ BETA)
    shuffle = rng.permutation(n)
    used = signal if informative else signal[shuffle]
    y = Y_MEAN + Y_SCALE * (np.sqrt(R2_TRUE) * used + np.sqrt(1.0 - R2_TRUE) * rng.standard_normal(n))
    return {"X": x, "y": y}, {"signal": signal, "used": used}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys (rows = 60 samples): X (60, 25) float64, 25 continuous measurements per sample (in their own
    units); y (60,) float64, continuous outcome of each sample.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _y_permuted(d, rng):
    return {**d, "y": _shuffled(rng, d["y"])}


STUDY = Study(
    name="D-027",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y carries no information from X: each sample's true linear predictor is taken "
                              "from a randomly permuted sample (marginal of y, noise level and the measurements' "
                              "distribution unchanged)"),
    },
    controls=[Control("y_permuted", ["C"], transform=_y_permuted)],
)
