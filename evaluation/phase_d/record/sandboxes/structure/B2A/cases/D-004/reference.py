"""D-004: On future days, a ridge regression forecast of the outcome y from the day's five predictors X (penalty 1.0 on standardised predictors, with an intercept, one model for all stations) has a squared error at least 5% below that of the persistence forecast (the previous day's outcome at the same station), with squared errors pooled over stations: 1 - MSE(model) / MSE(persistence) >= 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

S, T, F = 40, 250, 5
PHI_C, PHI_L = 0.93, 0.5          # AR(1) of the common and the local part of the predictors
W_B, W_C, W_L = 0.05, 0.75, 0.20  # variance shares: station offset, common-in-time, local
XCORR = 0.3                       # correlation between predictors in their common part
PHI_YC, PHI_YL = 0.95, 0.20       # AR(1) of the outcome's common and local noise
C_VAR, L_VAR = 0.30, 0.50         # outcome noise variances (common slow part, station-day part)
SIG = 0.20                        # share of the outcome variance carried by the predictors (plus)
BETA = np.array([1.0, -0.9, 0.7, -0.6, 0.5])
OFF = W_C * XCORR
VAR_Z = float((1.0 - OFF) * np.sum(BETA ** 2) + OFF * np.sum(BETA) ** 2)


def _ar(e, phi):
    out = np.empty_like(e)
    out[0] = e[0]
    k = np.sqrt(1.0 - phi ** 2)
    for t in range(1, e.shape[0]):
        out[t] = phi * out[t - 1] + k * e[t]
    return out


def _draw(rng):
    g = rng.standard_normal((T, 1))
    ec = np.sqrt(XCORR) * g + np.sqrt(1.0 - XCORR) * rng.standard_normal((T, F))
    C = _ar(ec, PHI_C)
    L = _ar(rng.standard_normal((T, S, F)), PHI_L)
    b = rng.standard_normal((S, F))
    X = np.sqrt(W_B) * b[None, :, :] + np.sqrt(W_C) * C[:, None, :] + np.sqrt(W_L) * L
    X = np.ascontiguousarray(X.transpose(1, 0, 2))
    z = (X @ BETA) / np.sqrt(VAR_Z)
    c = _ar(rng.standard_normal((T, 1)), PHI_YC)
    l = _ar(rng.standard_normal((T, S)), PHI_YL)
    noise = (np.sqrt(C_VAR) * c + np.sqrt(L_VAR) * l).T
    return X, z, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, z, noise = _draw(rng)
    y = np.sqrt(SIG) * z + noise
    return {"X": X, "y": np.ascontiguousarray(y)}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, z, noise = _draw(rng)
    lag = int(rng.integers(T // 4, 3 * T // 4 + 1))
    perm = rng.permutation(S)
    zr = np.roll(z[perm], lag, axis=1)
    y = np.sqrt(SIG) * zr + noise
    return {"X": X, "y": np.ascontiguousarray(y)}


def criterion(d):
    """Data keys: X (stations, days_in_order, features) = (40, 250, 5), 5 continuous daily predictors per station and
    day; y (stations, days_in_order) = (40, 250), continuous daily outcome per station.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def shift_y(d, rng):
    lag = int(rng.integers(T // 4, 3 * T // 4 + 1))
    y = np.roll(d["y"][rng.permutation(S)], lag, axis=1)
    return {"X": np.array(d["X"]), "y": np.ascontiguousarray(y)}


STUDY = Study(
    name="D-004",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the predictors' contribution to y is taken from another station order and a day-shifted copy of the predictor series, so y carries no information on X; the outcome variance, its own autocorrelation and X are unchanged"),
    },
    controls=[Control("D-004", ["C"], transform=shift_y)],
)
