"""D-055: The daily predictors X carry information about the daily outcome y on future days: the Pearson correlation between y and the prediction of a ridge regression of y on X (penalty 1.0 on standardised predictors, with an intercept), computed over future days, is at least 0.20."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_T = 1000
_P = 6
# Predictors: common slow factor (phi 0.9) plus predictor-specific AR(1) parts (phi 0.6).
_LOAD = np.array([0.70, 0.60, 0.50, 0.65, 0.40, 0.55])
_PHI = np.concatenate([[0.9], np.full(_P, 0.6), [0.9], np.full(_P, 0.6), [0.5]])
_BETA = np.array([0.50, -0.35, 0.25, 0.00, 0.30, 0.00])
_SIGMA_X = np.outer(_LOAD, _LOAD) + np.diag(1.0 - _LOAD ** 2)
_SIGNAL_SD = float(np.sqrt(_BETA @ _SIGMA_X @ _BETA))
_R2 = 0.16
_X_MEAN = np.array([15.0, 65.0, 1013.0, 4.0, 180.0, 30.0])
_X_SCALE = np.array([6.0, 12.0, 7.0, 1.5, 60.0, 9.0])
_WEEK = np.array([0.30, 0.10, 0.05, 0.00, -0.05, -0.15, -0.25])
_WEEK_STD = (_WEEK - _WEEK.mean()) / _WEEK.std()
_Y_MEAN = 100.0
_Y_SCALE = 15.0


def _ar1_block(rng):
    """15 stationary AR(1) series of unit variance: f, u1..u6, f', u'1..u'6, e."""
    k = _PHI.shape[0]
    innov = rng.standard_normal((_T, k)) * np.sqrt(1.0 - _PHI ** 2)
    out = np.empty((_T, k))
    out[0] = rng.standard_normal(k)
    for t in range(1, _T):
        out[t] = _PHI * out[t - 1] + innov[t]
    return out


def _predictors(f, u):
    return f[:, None] * _LOAD[None, :] + u * np.sqrt(1.0 - _LOAD ** 2)[None, :]


def _generate(rng, informative):
    s = _ar1_block(rng)
    z_obs = _predictors(s[:, 0], s[:, 1:1 + _P])            # the predictors that are recorded
    z_other = _predictors(s[:, 1 + _P], s[:, 2 + _P:2 + 2 * _P])  # an independent copy with the same dynamics
    e = s[:, -1]                                              # AR(1) outcome noise (phi 0.5)
    week_start = int(rng.integers(7))
    trend_slope = 0.3 + 0.05 * rng.standard_normal()
    z_driver = z_obs if informative else z_other
    signal = (z_driver @ _BETA) / _SIGNAL_SD
    days = np.arange(_T)
    weekly = 0.25 * _WEEK_STD[(days + week_start) % 7]
    trend = trend_slope * days / _T
    y = _Y_MEAN + _Y_SCALE * (np.sqrt(_R2) * signal + np.sqrt(1.0 - _R2) * e + weekly + trend)
    X = _X_MEAN[None, :] + _X_SCALE[None, :] * z_obs
    return {"X": X.astype(np.float64), "y": y.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: X (1000, 6) float, six continuous daily predictor series, rows are days in time order;
    y (1000,) float, continuous daily outcome, same days in the same order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _circular_shift_y(d, rng):
    k = int(rng.integers(150, 851))
    return {**d, "y": np.roll(d["y"], k)}


STUDY = Study(
    name="D-055",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y driven by an independent copy of the predictor process instead of the recorded X (no information of X about y); y and X keep their plus distributions and autocorrelation"),
    },
    controls=[Control("y_circularly_shifted", ["C"], transform=_circular_shift_y)],
)
