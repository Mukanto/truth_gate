"""D-022: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 300
P = 10
# three latent process states drive correlated readings (standardised scale)
LATENT_COEF = np.array([
    [0.7, 0.6, 0.0, 0.5, 0.0, 0.0, 0.4, 0.0, 0.0, 0.3],
    [0.0, 0.3, 0.7, 0.0, 0.6, 0.0, 0.0, 0.5, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.3, 0.0, 0.7, 0.4, 0.0, 0.6, 0.5],
])
UNIQUE_SD = np.sqrt(1.0 - (LATENT_COEF ** 2).sum(axis=0))
# physical units: temperatures, pressures, flows, pH, speeds, ...
UNIT_MEAN = np.array([180.0, 2.5, 35.0, 12.0, 0.8, 65.0, 7.2, 410.0, 1.5, 22.0])
UNIT_SD = np.array([5.0, 0.2, 4.0, 1.5, 0.05, 6.0, 0.3, 25.0, 0.12, 2.5])
NOISE_SD = 3.264  # gives a population R-squared of 0.30 for the quadratic quality surface (var f = 4.57)


def _readings(rng):
    z = rng.standard_normal((N, 3)) @ LATENT_COEF + UNIQUE_SD * rng.standard_normal((N, P))
    return z


def _quality(z):
    """Quadratic response surface: linear effects, an optimum, curvature and two interactions."""
    return (1.0 * z[:, 0] - 0.7 * z[:, 3] + 0.5 * z[:, 6]
            - 0.8 * (z[:, 1] - 0.4) ** 2 - 0.5 * z[:, 2] ** 2
            + 0.7 * z[:, 0] * z[:, 4] - 0.5 * z[:, 5] * z[:, 7])


def _generate(rng, linked):
    """When not linked, y follows the surface evaluated at an independent run (same distribution)."""
    z = _readings(rng)
    z_other = _readings(rng)
    eps = rng.standard_normal(N)
    f = _quality(z) if linked else _quality(z_other)
    y = 75.0 + 1.5 * (f + NOISE_SD * eps)
    x = UNIT_MEAN + UNIT_SD * z
    return {"X": x.astype(np.float64), "y": y.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: X (300, 10) float, 10 continuous process readings recorded for each production run;
    y (300,) float, continuous quality score of each production run.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_y(d, rng):
    return {**d, "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-022",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y follows the quality surface of an independent run, not of the recorded readings (no predictive information; marginals unchanged)"),
    },
    controls=[Control("y_shuffled_across_runs", ["C"], transform=_shuffle_y)],
)
