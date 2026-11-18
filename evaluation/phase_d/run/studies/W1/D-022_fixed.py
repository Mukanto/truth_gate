"""D-022: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 300              # production runs, in time order
P = 10
LOT = 10             # raw-material lots of 10 consecutive runs
MEANS = np.array([182.0, 2.45, 35.0, 0.82, 61.0, 4.1, 120.0, 7.2, 15.5, 0.33])
SDS = np.array([4.0, 0.12, 2.5, 0.05, 3.0, 0.35, 8.0, 0.15, 1.2, 0.04])
LAM = np.array([0.6, 0.55, 0.5, 0.6, 0.45, 0.5, 0.4, 0.0, 0.0, 0.0])    # loading on the drifting process state
GAM = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 0.6, 0.5])    # loading on the feedstock lot
SENSOR = 0.2         # sensor noise, in units of each reading's SD
F_MEAN = -0.1284     # mean and SD of the quality function under the stationary distribution of the process
F_SD = 0.8825
SIGNAL = 0.30        # share of quality-score variance explained by the process (the claimed effect)


def _ar1_time(rng, n, k, rho):
    e = rng.standard_normal((n, k))
    out = np.empty((n, k))
    out[0] = e[0]
    s = np.sqrt(1.0 - rho * rho)
    for t in range(1, n):
        out[t] = rho * out[t - 1] + s * e[t]
    return out


def _process(rng):
    state = _ar1_time(rng, N, 1, 0.8)
    lot = np.repeat(rng.standard_normal((N // LOT, 1)), LOT, axis=0)
    own = _ar1_time(rng, N, P, 0.5)
    return state * LAM + lot * GAM + np.sqrt(1.0 - LAM ** 2 - GAM ** 2) * own


def _quality(z):
    f = (0.45 * z[:, 0] - 0.35 * z[:, 1] ** 2 + 0.30 * z[:, 2] * z[:, 3] + 0.25 * z[:, 4]
         - 0.20 * z[:, 0] * z[:, 5] + 0.15 * z[:, 6] ** 2 - 0.20 * z[:, 8] + 0.15 * z[:, 7] * z[:, 9])
    return (f - F_MEAN) / F_SD


def _world(rng, effect):
    z = _process(rng)
    z_copy = _process(rng)          # independent copy of the process (same time structure): drives y in minus
    sensor = rng.standard_normal((N, P))
    lot_y = np.repeat(rng.standard_normal(N // LOT), LOT)
    drift_y = _ar1_time(rng, N, 1, 0.6)[:, 0]
    white = rng.standard_normal(N)
    signal = _quality(z if effect else z_copy)
    noise = np.sqrt(1.0 - SIGNAL) * (np.sqrt(0.15) * lot_y + np.sqrt(0.20) * drift_y + np.sqrt(0.65) * white)
    y = 70.0 + 6.0 * (np.sqrt(SIGNAL) * signal + noise)
    X = MEANS + SDS * (z + SENSOR * sensor)
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def poly_features(Z):
    """Intercept, linear terms, squares and all pairwise products of the columns of Z."""
    n, p = Z.shape
    iu, ju = np.triu_indices(p)
    return np.column_stack([np.ones(n), Z, Z[:, iu] * Z[:, ju]])


def poly_fit(X, y):
    """Second-order polynomial regression by ordinary least squares on standardised columns."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    coef = np.linalg.lstsq(poly_features((X - mu) / sd), y, rcond=None)[0]
    return mu, sd, coef


def poly_predict(model, X):
    """Predictions of a model returned by poly_fit."""
    mu, sd, coef = model
    return poly_features((X - mu) / sd) @ coef


def criterion(d):
    """Claim: a second-order polynomial regression of y on X (intercept, the 10 readings, their squares and all
    pairwise products, ordinary least squares) predicts y for new runs with a Pearson correlation between
    predicted and observed y of at least 0.30.

    Data keys:
      "X": float array (samples, features) = (300, 10); the 10 continuous process readings of each production run.
      "y": float array (samples,) = (300,); the continuous quality score of each production run.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 runs, zero variance of the predictions or of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = poly_predict(poly_fit(X[~te], y[~te]), X[te])
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _shift_y(d, rng):
    n = d["y"].shape[0]
    k = int(rng.integers(n // 10, n - n // 10 + 1))
    return {**d, "y": np.roll(d["y"], k)}


STUDY = Study(
    name="D-022",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="quality driven by an independent copy of the process (same time structure): y unrelated to X"),
    },
    controls=[Control("y_circularly_shifted_against_X_by_30_to_270_runs", ["C"], transform=_shift_y)],
    relational=[("X", "y")],
)
