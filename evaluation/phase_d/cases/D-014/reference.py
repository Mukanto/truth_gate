"""D-014: The laboratory values in X predict the outcome y for new patients: the R-squared of a ridge regression of y on the 20 laboratory values (penalty 1.0 on standardised values, with an intercept) is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 250, 20, 3
COMM = 0.5       # share of each laboratory value's variance carried by 3 latent factors
S_SIG = 0.40     # share of the outcome variance carried by the complete laboratory values (plus)
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.21) * 1.13 + 0.7)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))
BETA = np.array([1.0, -0.8, 0.0, 0.6, 0.0, 0.5, 0.0, -0.4, 0.0, 0.3, 0.0, 0.0, 0.7, 0.0, 0.0, -0.5, 0.0, 0.0, 0.4, 0.0])
SIGMA = LOAD @ LOAD.T + (1.0 - COMM) * np.eye(P)
VAR_Z = float(BETA @ SIGMA @ BETA)
# missingness: column rates 0.10..0.40 (mean 0.25), multiplied by a patient-level propensity with mean 1
RATE = np.linspace(0.10, 0.40, P)[(np.arange(P) * 7) % P]


def _draw(rng):
    Fl = rng.standard_normal((N, K))
    Xc = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((N, P))
    z = (Xc @ BETA) / np.sqrt(VAR_Z)
    noise = rng.standard_normal(N)
    prop = rng.gamma(4.0, 0.25, size=(N, 1))
    miss = rng.random((N, P)) < np.minimum(RATE[None, :] * prop, 0.95)
    X = np.where(miss, np.nan, Xc)
    return X, z, noise


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
    """Data keys: X (samples, features) = (250, 20), 20 laboratory values per patient, NaN where a value was not
    measured; y (samples,) = (250,), continuous clinical outcome.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-014",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the laboratory-value part of y is reassigned to other patients (permuted), so y carries no information on X; the variance of y, the noise, X and the missingness are unchanged"),
    },
    controls=[Control("D-014", ["C"], transform=permute_y)],
)
