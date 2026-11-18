"""D-005: The measurements in X carry information about the outcome y: the R-squared (coefficient of determination) of a ridge regression of y on X (penalty 1.0 on standardised measurements, with an intercept), evaluated on new samples, is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 100, 150, 5
COMM = 0.6        # share of each biomarker's variance carried by the latent physiology factors
S_SIG = 0.55      # share of the outcome variance carried by the latent factors (plus)
G = np.array([1.0, 0.8, 0.6, 0.5, 0.3])
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.37) * 0.93 + 0.4)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))
GN = G / np.sqrt(np.sum(G ** 2))


def _draw(rng):
    Fl = rng.standard_normal((N, K))
    X = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((N, P))
    z = Fl @ GN
    noise = rng.standard_normal(N)
    return np.ascontiguousarray(X), z, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, z, noise = _draw(rng)
    return {"X": X, "y": np.sqrt(S_SIG) * z + np.sqrt(1.0 - S_SIG) * noise}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, z, noise = _draw(rng)
    zp = z[rng.permutation(N)]
    return {"X": X, "y": np.sqrt(S_SIG) * zp + np.sqrt(1.0 - S_SIG) * noise}


def criterion(d):
    """Data keys: X (samples, features) = (100, 150), 150 continuous biomarker measurements per sample;
    y (samples,) = (100,), continuous clinical score per sample.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-005",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the latent-factor part of y is reassigned to other samples (permuted), so y carries no information on X; the variance of y, the noise and X are unchanged"),
    },
    controls=[Control("D-005", ["C"], transform=permute_y)],
)
