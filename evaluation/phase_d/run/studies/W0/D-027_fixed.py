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
