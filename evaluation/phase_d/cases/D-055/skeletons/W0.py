"""D-055: The daily predictors X carry information about the daily outcome y on future days: the Pearson correlation between y and the prediction of a ridge regression of y on X (penalty 1.0 on standardised predictors, with an intercept), computed over future days, is at least 0.20."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_DAYS = 1000
N_FEAT = 6
PHI_X = np.array([0.8, 0.6, 0.7, 0.4, 0.5, 0.95])      # day-to-day autocorrelation of each predictor
R_INNOV = np.array([
    [1.0, -0.4, 0.1, -0.1, 0.5, 0.2],
    [-0.4, 1.0, -0.2, 0.0, -0.5, 0.0],
    [0.1, -0.2, 1.0, -0.3, 0.2, 0.1],
    [-0.1, 0.0, -0.3, 1.0, -0.1, -0.4],
    [0.5, -0.5, 0.2, -0.1, 1.0, 0.1],
    [0.2, 0.0, 0.1, -0.4, 0.1, 1.0],
])                                                     # correlation of the daily innovations
X_MEAN = np.array([15.0, 65.0, 1013.0, 4.0, 6.0, 35.0])
X_SD = np.array([7.0, 14.0, 8.0, 2.0, 3.5, 12.0])
BETA_DIR = np.array([0.6, -0.4, 0.3, 0.0, 0.25, 0.3])  # direction of the true linear effect of X on y
TARGET_R = 0.33        # population correlation between y and its true linear predictor (plus)
PHI_E = 0.3            # autocorrelation of the outcome noise
Y_MEAN = 120.0
Y_SD = 15.0
BLOCK = 50


def _generate(rng, signal_on):
    one_m = 1.0 - PHI_X ** 2
    q = R_INNOV * np.sqrt(np.outer(one_m, one_m))
    sigma = q / (1.0 - np.outer(PHI_X, PHI_X))         # stationary covariance (unit variances)
    lq = np.linalg.cholesky(q)
    ls = np.linalg.cholesky(sigma)
    innov = rng.standard_normal((N_DAYS, N_FEAT)) @ lq.T
    x0 = ls @ rng.standard_normal(N_FEAT)
    eta = rng.standard_normal(N_DAYS)
    z = np.empty((N_DAYS, N_FEAT))
    e = np.empty(N_DAYS)
    z[0] = x0
    e[0] = eta[0]
    se = np.sqrt(1.0 - PHI_E ** 2)
    for t in range(1, N_DAYS):
        z[t] = PHI_X * z[t - 1] + innov[t]
        e[t] = PHI_E * e[t - 1] + se * eta[t]
    s2 = TARGET_R ** 2 / (1.0 - TARGET_R ** 2)
    beta = BETA_DIR * np.sqrt(s2 / float(BETA_DIR @ sigma @ BETA_DIR))
    latent = signal_on * (z @ beta) + e
    X = X_MEAN + X_SD * z
    y = Y_MEAN + Y_SD * latent
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def criterion(d):
    """Data keys: X (1000, 6) float64, six continuous daily predictor series, rows are days in time order;
    y (1000,) float64, continuous daily outcome, same days in the same order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shift_outcome(d, rng):
    k = int(rng.integers(150, 851))
    return {**d, "y": np.roll(d["y"], k)}


def _block_permute_predictors(d, rng):
    nb = N_DAYS // BLOCK
    p = rng.permutation(nb)
    src = np.empty(nb, dtype=np.int64)
    src[p] = np.roll(p, -1)                             # a single cycle: no block keeps its own days
    idx = (src[:, None] * BLOCK + np.arange(BLOCK)[None, :]).ravel()
    return {**d, "X": d["X"][idx].copy()}


STUDY = Study(
    name="D-055",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="true linear effect of X on y set to zero (y = same autocorrelated noise only); X unchanged"),
    },
    controls=[
        Control("outcome_circular_shift", ["C"], transform=_shift_outcome),
        Control("predictor_blocks_permuted", ["C"], transform=_block_permute_predictors),
    ],
    relational=[("y", "X")],
)
