"""D-027: The 25 measurements in X predict the outcome y for new samples: the mean absolute error of an ordinary least squares regression of y on X (with an intercept) is at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P = 60, 25
RHO = 0.25   # correlation between the measurements (shared factor)
SIG_VAR = 2.33   # variance of the signal; noise variance 1 -> signal share 0.70
PAT = np.zeros(P) + np.isin(np.arange(P), np.arange(0, 24, 3)) * np.tile(np.array([1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0]), 3)[:P]
_V = (1.0 - RHO) * np.sum(PAT ** 2) + RHO * np.sum(PAT) ** 2
BETA = PAT * np.sqrt(SIG_VAR / _V)


def _draw(rng):
    g = rng.standard_normal((N, 1))
    X = np.sqrt(RHO) * g + np.sqrt(1.0 - RHO) * rng.standard_normal((N, P))
    sig = X @ BETA
    noise = rng.standard_normal(N)
    return np.ascontiguousarray(X), sig, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, sig, noise = _draw(rng)
    return {"X": X, "y": sig + noise}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, sig, noise = _draw(rng)
    return {"X": X, "y": sig[rng.permutation(N)] + noise}


def criterion(d):
    """Data keys: X (samples, features) = (60, 25), 25 continuous measurements per sample;
    y (samples,) = (60,), continuous outcome per sample.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-027",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the linear signal in y is reassigned to other samples (permuted), so y carries no information on X; the variance of y, the noise and X are unchanged"),
    },
    controls=[Control("D-027", ["C"], transform=permute_y)],
)
