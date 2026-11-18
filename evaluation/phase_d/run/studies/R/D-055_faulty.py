"""D-055: The daily predictors X carry information about the daily outcome y on future days: the Pearson correlation between y and the prediction of a ridge regression of y on X (penalty 1.0 on standardised predictors, with an intercept), computed over future days, is at least 0.20."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

T, P = 1000, 6
PHI = np.array([0.92, 0.88, 0.84, 0.80, 0.76, 0.70])   # day-to-day autocorrelation of the predictors
XCORR = 0.2                                            # shared part of the predictors' innovations
PHI_Y = 0.92                                           # autocorrelation of the outcome's own noise
S_SIG = 0.28                                           # share of the outcome variance carried by the predictors (plus)
BETA = np.array([1.0, -0.8, 0.6, -0.5, 0.4, -0.3])
_SX = np.sqrt(1.0 - PHI ** 2)[:, None] * np.sqrt(1.0 - PHI ** 2)[None, :] * XCORR / (1.0 - PHI[:, None] * PHI[None, :])
SIGX = _SX * (1.0 - np.eye(P)) + np.eye(P)
VAR_Z = float(BETA @ SIGX @ BETA)


def _ar(e, phi):
    out = np.empty_like(e)
    out[0] = e[0]
    k = np.sqrt(1.0 - phi ** 2)
    for t in range(1, e.shape[0]):
        out[t] = phi * out[t - 1] + k * e[t]
    return out


def _draw(rng):
    g = rng.standard_normal((T, 1))
    ec = np.sqrt(XCORR) * g + np.sqrt(1.0 - XCORR) * rng.standard_normal((T, P))
    X = _ar(ec, PHI)
    z = (X @ BETA) / np.sqrt(VAR_Z)
    noise = _ar(rng.standard_normal((T, 1)), PHI_Y)[:, 0]
    return np.ascontiguousarray(X), z, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, z, noise = _draw(rng)
    return {"X": X, "y": np.sqrt(S_SIG) * z + np.sqrt(1.0 - S_SIG) * noise}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, z, noise = _draw(rng)
    lag = int(rng.integers(T // 4, 3 * T // 4 + 1))
    zr = np.roll(z, lag)
    return {"X": X, "y": np.sqrt(S_SIG) * zr + np.sqrt(1.0 - S_SIG) * noise}


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
    rng = np.random.default_rng(0)
    fold = np.empty(n, dtype=int)
    fold[rng.permutation(n)] = np.arange(n) % 5
    ev = np.ones(n, dtype=bool)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te], y[~te], 1.0), X[te])
    r = pearson(pred[ev], y[ev])
    if r is None:
        return None
    return bool(r >= 0.20)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def shift_y(d, rng):
    lag = int(rng.integers(T // 4, 3 * T // 4 + 1))
    return {"X": np.array(d["X"]), "y": np.roll(d["y"], lag)}


STUDY = Study(
    name="D-055",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the predictors' contribution to y is taken from a day-shifted copy of the predictor series, so y carries no information on X; the outcome variance, its own autocorrelation and X are unchanged"),
    },
    controls=[Control("D-055", ["C"], transform=shift_y)],
)
