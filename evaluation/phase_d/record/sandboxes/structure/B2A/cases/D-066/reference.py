"""D-066: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 1000, 15, 2
N_POS = 80           # 8% rare outcome
COMM = 0.3           # share of each measurement's variance carried by 2 latent factors
SHIFT = np.where(np.arange(P) < 8, 1.3, 0.0)   # mean shift of the rare-outcome patients (plus)
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.13) * 0.91 + 0.5)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))


def _draw(rng):
    lab = rng.permutation(N) < N_POS
    Fl = rng.standard_normal((N, K))
    X = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((N, P))
    X = X + lab[:, None] * SHIFT[None, :]
    return np.ascontiguousarray(X), lab


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab[rng.permutation(N)]}


def criterion(d):
    """Data keys: X (samples, features) = (1000, 15), 15 continuous clinical measurements per patient;
    y (samples,) = (1000,), bool, True where the patient has the rare outcome (80 of 1000).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-066",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the outcome labels are reassigned to other patients (permuted), so y carries no information on X; the outcome count, X and its mean-shifted subgroup are unchanged"),
    },
    controls=[Control("D-066", ["C"], transform=permute_y)],
)
