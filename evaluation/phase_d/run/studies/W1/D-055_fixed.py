"""D-055: The daily predictors X carry information about the daily outcome y on future days: the Pearson correlation between y and the prediction of a ridge regression of y on X (penalty 1.0 on standardised predictors, with an intercept), computed over future days, is at least 0.20."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_DAYS = 1000
N_FEAT = 6
X_MEAN = np.array([14.0, 65.0, 1013.0, 22.0, 4.5, 35.0])
X_SD = np.array([7.5, 14.0, 8.0, 11.0, 1.8, 15.0])
LOAD = np.array([0.7, -0.5, -0.4, 0.6, 0.5, 0.6])        # loadings of the predictors on one shared daily factor
PHI_COMMON = 0.9                                         # autocorrelation of the shared factor
PHI_OWN = np.array([0.80, 0.60, 0.85, 0.55, 0.70, 0.65])  # autocorrelation of each predictor's own part
BETA = np.array([0.55, 0.0, -0.35, 0.40, 0.0, 0.0])       # weights of the standardised predictors in y's signal
SIGNAL_VAR = float((BETA @ LOAD) ** 2 + np.sum(BETA ** 2 * (1.0 - LOAD ** 2)))
R2 = 0.16                                                # share of y's variance carried by the signal (r = 0.40)
PHI_Y_SHORT = 0.6
PHI_Y_SLOW = 0.99
SHARE_SHORT = 0.75
SHARE_SLOW = 0.10
SHARE_WEEK = 0.15
WEEK = np.array([0.9, 0.6, 0.4, 0.3, 0.2, -1.1, -1.3])   # day-of-week profile of the outcome
WEEK_STD = (WEEK - WEEK.mean()) / WEEK.std()
Y_MEAN = 50.0
Y_SD = 8.0
PHIS = np.concatenate([[PHI_COMMON], PHI_OWN, [PHI_COMMON], PHI_OWN, [PHI_Y_SHORT, PHI_Y_SLOW]])


def _ar1(rng, phis, n):
    """Stationary unit-variance AR(1) series, one column per entry of phis."""
    eps = rng.standard_normal((n, phis.shape[0]))
    scale = np.sqrt(1.0 - phis ** 2)
    out = np.empty_like(eps)
    out[0] = eps[0]
    for t in range(1, n):
        out[t] = phis * out[t - 1] + scale * eps[t]
    return out


def _generate(rng, use_copy):
    s = _ar1(rng, PHIS, N_DAYS)
    unique = np.sqrt(1.0 - LOAD ** 2)
    z = LOAD * s[:, [0]] + unique * s[:, 1:7]              # standardised predictors
    z_copy = LOAD * s[:, [7]] + unique * s[:, 8:14]        # independent copy of the predictor process
    start = rng.integers(7)
    week = WEEK_STD[(np.arange(N_DAYS) + start) % 7]
    noise = np.sqrt(SHARE_SHORT) * s[:, 14] + np.sqrt(SHARE_SLOW) * s[:, 15] + np.sqrt(SHARE_WEEK) * week
    carrier = z_copy if use_copy else z
    signal = (carrier @ BETA) / np.sqrt(SIGNAL_VAR)
    y = Y_MEAN + Y_SD * (np.sqrt(R2) * signal + np.sqrt(1.0 - R2) * noise)
    X = X_MEAN + X_SD * z
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    y on each day contains a linear signal of the same day's predictors (3 of 6 informative) that carries 16% of
    y's variance (population r = 0.40 between y and the true signal). Predictors share an autocorrelated common
    factor and have their own AR(1) parts; y's noise is autocorrelated, drifts slowly and has a weekday cycle."""
    return _generate(rng, False)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    y's signal part is computed from an independent copy of the predictor process, so X carries no information
    about y; X, y's marginal distribution and y's time structure are as in plus."""
    return _generate(rng, True)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def ridge_fit(X, y, lam):
    """Ridge regression on columns standardised with the mean and sd of the rows given, with an
    unpenalised intercept (y centred).  Closed form; dual form when columns outnumber rows."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    ym = y.mean()
    n, p = Z.shape
    if p > n:
        beta = Z.T @ np.linalg.solve(Z @ Z.T + lam * np.eye(n), y - ym)
    else:
        beta = np.linalg.solve(Z.T @ Z + lam * np.eye(p), Z.T @ (y - ym))
    return mu, sd, beta, ym


def ridge_predict(model, X):
    """Predictions of a model returned by ridge_fit."""
    mu, sd, beta, ym = model
    return ((X - mu) / sd) @ beta + ym


def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def criterion(d):
    """Claim: on future days, the Pearson correlation between y and the prediction of a ridge regression of y on
    X (penalty 1.0, standardised predictors, intercept) is at least 0.20.

    Data keys:
      "X": float array (days_in_order, features) = (1000, 6); the 6 continuous daily predictor series, rows in
           time order.
      "y": float array (days_in_order,) = (1000,); the continuous daily outcome, in time order.

    Returns True when the correlation >= 0.20, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 days, zero variance of the predictions or of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    pred = np.empty(n)
    ev = np.zeros(n, dtype=bool)
    for blk in np.array_split(np.arange(n), 6)[1:]:
        tr = np.arange(n) < blk[0] - 5
        pred[blk] = ridge_predict(ridge_fit(X[tr], y[tr], 1.0), X[blk])
        ev[blk] = True
    r = pearson(pred[ev], y[ev])
    if r is None:
        return None
    return bool(r >= 0.20)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _circular_shift_y(d, rng):
    lag = int(rng.integers(200, 801))
    return {**d, "y": np.roll(d["y"], lag)}


STUDY = Study(
    name="D-055",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="predictive link X -> y set to none: y's signal part comes from an independent copy of the predictor process (same distribution)"),
    },
    controls=[Control("y_circularly_shifted_200_to_800_days", ["C"], transform=_circular_shift_y)],
    relational=[("X", "y")],
)
