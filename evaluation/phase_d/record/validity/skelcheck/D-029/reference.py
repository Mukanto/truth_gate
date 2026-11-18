"""D-029: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised measurements) of the value y on the measurements X predicts y for new entries with a mean absolute error at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 600, 8, 3
COMM = 0.6        # share of each property's variance carried by 3 latent factors
S_SIG = 0.85      # share of the (log) target variance carried by the properties (plus)
LOG_SD = 1.5      # target value = exp(LOG_SD * latent), right-skewed
FLAG = 0.34       # share of rows that belong to a group of repeated records
SIZES = np.array([2, 3, 4])
SIZE_P = np.array([0.3, 0.5, 0.2])
MEAN_SIZE = 2.9
TAU_X, TAU_Y = 0.03, 0.03   # slight differences between repeated records
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.17) * 1.31 + 0.2)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))
BETA = np.array([1.0, -0.6, 0.8, 0.5, -0.7, 0.4, 0.6, -0.3])
SIGMA = LOAD @ LOAD.T + (1.0 - COMM) * np.eye(P)
VAR_Z = float(BETA @ SIGMA @ BETA)


def _draw(rng):
    G = int(round(FLAG * N / MEAN_SIZE))
    sizes = rng.choice(SIZES, size=G, p=SIZE_P)
    singles = N - int(sizes.sum())
    ne = G + singles
    Fl = rng.standard_normal((ne, K))
    Xe = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((ne, P))
    z = (Xe @ BETA) / np.sqrt(VAR_Z)
    noise = rng.standard_normal(ne)
    idx = np.concatenate([np.repeat(np.arange(G), sizes), np.arange(G, ne)])
    jx = TAU_X * rng.standard_normal((N, P))
    jy = TAU_Y * rng.standard_normal(N)
    rp = rng.permutation(N)
    return Xe, z, noise, idx, jx, jy, rp, ne


def _rows(Xe, lat, idx, jx, jy, rp):
    X = np.ascontiguousarray((Xe[idx] + jx)[rp])
    y = np.exp(LOG_SD * (lat[idx] + jy)[rp])
    return {"X": X, "y": y}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    Xe, z, noise, idx, jx, jy, rp, ne = _draw(rng)
    lat = np.sqrt(S_SIG) * z + np.sqrt(1.0 - S_SIG) * noise
    return _rows(Xe, lat, idx, jx, jy, rp)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    Xe, z, noise, idx, jx, jy, rp, ne = _draw(rng)
    zp = z[rng.permutation(ne)]
    lat = np.sqrt(S_SIG) * zp + np.sqrt(1.0 - S_SIG) * noise
    return _rows(Xe, lat, idx, jx, jy, rp)


def criterion(d):
    """Data keys: X (rows, features) = (600, 8), 8 continuous property measurements per registry entry (some entries
    appear in several rows); y (rows,) = (600,), continuous target value per row.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-029",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the properties' contribution to the target is reassigned to other entries (permuted at entry level, repeated records keep the same target), so y carries no information on X; target distribution, noise, X and the repeated records are unchanged"),
    },
    controls=[Control("D-029", ["C"], transform=permute_y)],
)
