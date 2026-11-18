"""D-022: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_SAMPLES = 300
N_FEATURES = 10
# Process readings (units): zone-1 temperature (C), zone-2 temperature (C), pressure (bar), feed rate (kg/h),
# screw speed (rpm), ambient humidity (%), melt viscosity (Pa s), line speed (m/min), residence time (s),
# motor power (kW).
X_MEAN = np.array([185.0, 210.0, 3.2, 48.0, 1200.0, 45.0, 2.1, 12.0, 95.0, 15.0])
X_SD = np.array([4.0, 5.0, 0.25, 4.0, 60.0, 7.0, 0.3, 1.0, 8.0, 1.5])
X_CORR = np.array([
    [1.00, 0.30, 0.00, 0.00, 0.00, 0.00, -0.35, 0.00, 0.00, 0.00],
    [0.30, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25],
    [0.00, 0.00, 1.00, 0.45, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.45, 1.00, 0.00, 0.00, 0.00, 0.20, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.50],
    [0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.20, 0.00],
    [-0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.20, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.20, 0.00, 0.00, 1.00, 0.00],
    [0.00, 0.25, 0.00, 0.00, 0.50, 0.00, 0.00, 0.00, 0.00, 1.00],
])
F_SD = 0.897                  # population SD of the response surface f below (offline Monte Carlo)
R2_TRUE = 0.33                # share of quality-score variance explained by the true response surface
Y_MEAN, Y_SCALE = 78.0, 6.0


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _surface(z):
    """True quality response surface on standardised readings: linear, curvature and interaction terms."""
    return (0.45 * z[:, 0] - 0.35 * z[:, 2] + 0.25 * z[:, 5] - 0.30 * (z[:, 1] ** 2 - 1.0)
            + 0.30 * z[:, 0] * z[:, 3] - 0.25 * z[:, 4] * z[:, 6] + 0.20 * z[:, 2] * z[:, 7]
            + 0.15 * (z[:, 8] ** 2 - 1.0))


def _draw(rng, informative):
    """One set of production runs. Returns (data, truth); truth holds the true surface values."""
    n = N_SAMPLES
    z = rng.standard_normal((n, N_FEATURES)) @ np.linalg.cholesky(X_CORR).T
    x = X_MEAN + X_SD * z
    f = _surface(z) / F_SD
    shuffle = rng.permutation(n)
    used = f if informative else f[shuffle]
    y = Y_MEAN + Y_SCALE * (np.sqrt(R2_TRUE) * used + np.sqrt(1.0 - R2_TRUE) * rng.standard_normal(n))
    return {"X": x, "y": y}, {"f": f, "used": used}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys (rows = 300 production runs): X (300, 10) float64, 10 continuous process readings per run in
    their natural units (zone-1 and zone-2 temperature in C, pressure in bar, feed rate in kg/h, screw speed in
    rpm, humidity in %, melt viscosity in Pa s, line speed in m/min, residence time in s, motor power in kW);
    y (300,) float64, continuous quality score of each run.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _y_permuted(d, rng):
    return {**d, "y": _shuffled(rng, d["y"])}


STUDY = Study(
    name="D-022",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y carries no information from X: each run's true response-surface value is taken "
                              "from a randomly permuted run (marginal of y, noise level and the readings' "
                              "distribution unchanged)"),
    },
    controls=[Control("y_permuted", ["C"], transform=_y_permuted)],
)
