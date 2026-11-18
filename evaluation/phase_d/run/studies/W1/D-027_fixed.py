"""D-027: The 25 measurements in X predict the outcome y for new samples: the mean absolute error of an ordinary least squares regression of y on X (with an intercept) is at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 60
P = 25
RUN_SIZE = 30        # two assay runs of 30 samples
RUN_SD = 0.3         # run offset per measurement, in units of the measurement's SD
MEAS_SD = 0.3        # measurement error, in units of the measurement's SD


def _loadings():
    L = np.zeros((P, 3))
    L[0:9, 0] = np.linspace(0.75, 0.5, 9)
    L[9:17, 1] = np.linspace(0.7, 0.45, 8)
    L[17:23, 2] = np.linspace(0.65, 0.45, 6)
    L[5:9, 2] += 0.25
    L[13:17, 0] += 0.2
    return L


def _beta():
    b = np.zeros(P)
    b[[0, 3, 6, 10, 12, 18, 21, 24]] = [0.35, 0.25, 0.15, -0.30, 0.20, 0.25, -0.20, 0.20]
    return b


LOAD = _loadings()
UNIQUE = np.sqrt(1.0 - (LOAD ** 2).sum(axis=1))
BETA = _beta()
SIGMA = 0.3787       # residual SD: population R^2 of the best linear predictor of y from X is 0.70
MEANS = np.linspace(5.0, 125.0, P)
SDS = 0.12 * MEANS + 0.5


def _true_values(rng):
    return rng.standard_normal((N, 3)) @ LOAD.T + UNIQUE * rng.standard_normal((N, P))


def _world(rng, effect):
    t = _true_values(rng)
    t_copy = _true_values(rng)      # independent copy of the samples' true values: drives y in minus
    run = np.repeat(np.arange(N // RUN_SIZE), RUN_SIZE)
    run_off = RUN_SD * rng.standard_normal((N // RUN_SIZE, P))
    meas = MEAS_SD * rng.standard_normal((N, P))
    eps = rng.standard_normal(N)
    y = 50.0 + 10.0 * ((t if effect else t_copy) @ BETA + SIGMA * eps)
    X = MEANS + SDS * (t + run_off[run] + meas)
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def ols_predict(A, y, tr, te):
    """Ordinary least squares (numpy lstsq) of y on the columns of A over the rows tr; predictions for rows te."""
    coef = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    return A[te] @ coef


def fold_mean_baseline(y, fold):
    """For each row, the mean of y over the rows outside its fold (the training-fold mean predictor)."""
    base = np.empty(y.shape[0])
    for k in range(5):
        te = fold == k
        base[te] = y[~te].mean()
    return base


def criterion(d):
    """Claim: the mean absolute error of an ordinary least squares regression of y on the 25 measurements X
    (with an intercept), for new samples, is at least 10% below that of predicting the mean of y:
    1 - MAE(model) / MAE(mean predictor) >= 0.10.

    Data keys:
      "X": float array (samples, features) = (60, 25); the 25 continuous measurements of each sample.
      "y": float array (samples,) = (60,); the continuous outcome of each sample.

    Returns True when the skill >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero MAE of the mean predictor).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    A = np.column_stack([np.ones(n), X])
    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = ols_predict(A, y, ~te, te)
    base = fold_mean_baseline(y, fold)
    mae0 = np.mean(np.abs(y - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(y - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.10)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _nonidentity_perm(rng, n):
    p = rng.permutation(n)
    if np.all(p == np.arange(n)):
        p = np.roll(p, 1)
    return p


def _shuffle_y(d, rng):
    p = _nonidentity_perm(rng, d["y"].shape[0])
    return {**d, "y": d["y"][p]}


STUDY = Study(
    name="D-027",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y driven by an independent copy of the samples' true values: X carries no information on y"),
    },
    controls=[Control("y_shuffled_across_samples", ["C"], transform=_shuffle_y)],
)
