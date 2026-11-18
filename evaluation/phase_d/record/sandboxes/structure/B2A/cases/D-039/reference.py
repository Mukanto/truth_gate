"""D-039: On future months, the monthly forecasts of a ridge regression of y on the three predictors X (penalty 1.0 on standardised predictors, with an intercept) are informative about the monthly outcome: the slope of the ordinary least squares regression of observed y on the forecast, computed over future months, is at least 0.5."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

T, P = 400, 3
PHI = np.array([0.95, 0.90, 0.85])   # month-to-month autocorrelation of the three predictors
XCORR = 0.2                          # shared part of the predictors' innovations
PHI_Y = 0.8                          # autocorrelation of the outcome's own noise
S_SIG = 0.5                          # share of the outcome variance carried by the predictors (plus)
BETA = np.array([1.0, -0.8, 0.6])
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


def criterion(d):
    """Data keys: X (months_in_order, features) = (400, 3), 3 continuous monthly predictor series;
    y (months_in_order,) = (400,), continuous monthly outcome.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def shift_y(d, rng):
    lag = int(rng.integers(T // 4, 3 * T // 4 + 1))
    return {"X": np.array(d["X"]), "y": np.roll(d["y"], lag)}


STUDY = Study(
    name="D-039",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the predictors' contribution to y is taken from a month-shifted copy of the predictor series, so y carries no information on X; the outcome variance, its own autocorrelation and X are unchanged"),
    },
    controls=[Control("D-039", ["C"], transform=shift_y)],
)
