"""D-060: The 500 features in X predict the outcome y for new samples: the R-squared of a ridge-penalised linear regression of y that uses 20 of the 500 features (penalty 10 on standardised features, with an intercept) is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P = 100, 500
NB, BS = 20, 25      # 20 imaging regions of 25 features
LOAD = 0.7           # region loading: correlation 0.49 between features of a region
A0, A1 = 0.30, 0.04  # variance of y carried by region 0 and region 1 (plus)
NOISE_VAR = 0.66


def _draw(rng):
    Fl = rng.standard_normal((N, NB))
    E = rng.standard_normal((N, P))
    X = LOAD * np.repeat(Fl, BS, axis=1) + np.sqrt(1.0 - LOAD ** 2) * E
    sig = np.sqrt(A0) * Fl[:, 0] + np.sqrt(A1) * Fl[:, 1]
    noise = np.sqrt(NOISE_VAR) * rng.standard_normal(N)
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
    """Data keys: X (samples, features) = (100, 500), 500 continuous imaging-derived features per sample;
    y (samples,) = (100,), continuous symptom score.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-060",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the region-driven part of y is reassigned to other samples (permuted), so y carries no information on X; the variance of y, the noise and X are unchanged"),
    },
    controls=[Control("D-060", ["C"], transform=permute_y)],
)
