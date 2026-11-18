"""D-022: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 300
N_FEATURES = 10
SIGNAL_SHARE = 0.37       # share of quality-score variance explained by the true process function in plus
READING_CORR = 0.4 ** np.abs(np.subtract.outer(np.arange(N_FEATURES), np.arange(N_FEATURES)))
READING_CHOL = np.linalg.cholesky(READING_CORR)
F_SD = 0.8178             # SD of the true process function under READING_CORR (Monte Carlo, 2e6 draws)
READING_CENTRE = np.array([182.0, 2.4, 41.0, 6.8, 1250.0, 0.55, 23.0, 88.0, 3.1, 140.0])
READING_SCALE = np.array([4.0, 0.25, 3.5, 0.3, 60.0, 0.05, 1.5, 6.0, 0.4, 9.0])


def _process_function(z):
    return (0.35 * z[:, 0] + 0.25 * z[:, 2] - 0.20 * z[:, 5]
            - 0.30 * (z[:, 3] ** 2 - 1.0) - 0.20 * (z[:, 7] ** 2 - 1.0)
            + 0.30 * z[:, 1] * z[:, 4] - 0.25 * z[:, 6] * z[:, 8])


def _simulate(rng, scale):
    n = N_SAMPLES
    z = rng.standard_normal((n, N_FEATURES)) @ READING_CHOL.T
    x = READING_CENTRE + READING_SCALE * z
    signal = np.sqrt(SIGNAL_SHARE) * _process_function(z) / F_SD
    y = 72.0 + 5.0 * (scale * signal + np.sqrt(1.0 - SIGNAL_SHARE) * rng.standard_normal(n))
    return {"X": np.asarray(x, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: X (300, 10) float, 10 continuous process readings recorded for each production run (columns in
    their own units); y (300,) float, continuous quality score of each production run.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_y(d, rng):
    y = d["y"]
    return {**d, "y": y[rng.permutation(y.shape[0])].copy()}


STUDY = Study(
    name="D-022",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="the process function (linear, square and interaction terms) in y set to 0 (readings carry no information on quality); noise SD and reading distribution unchanged"),
    },
    controls=[Control("y_permuted_across_runs", ["C"], transform=_permute_y)],
    relational=[("X", "y")],
)
