"""D-042: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 1200, 20, 5
COMM = 0.75       # molecular descriptors are strongly inter-correlated (5 latent factors)
S_SIG = 0.65      # share of the response variance carried by the descriptors (plus)
FLAG = 0.345      # share of records that belong to a group of near-identical records
SIZES = np.array([2, 3, 4])
SIZE_P = np.array([0.3, 0.5, 0.2])
MEAN_SIZE = 2.9
TAU_X, TAU_Y = 0.04, 0.05   # slight differences between repeated records
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.29) * 0.77 + 0.6)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))
BETA = np.where(np.arange(P) % 3 == 0, 1.0, 0.0) * np.where(np.arange(P) % 2 == 0, 1.0, -1.0) + 0.25 * np.where(np.arange(P) % 3 == 1, 1.0, 0.0)
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
    y = np.ascontiguousarray((lat[idx] + jy)[rp])
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
    """Data keys: X (records, features) = (1200, 20), 20 continuous molecular descriptors per compound record (some
    compounds appear in several records with slight differences); y (records,) = (1200,), continuous activity
    response per record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-042",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the descriptors' contribution to the response is reassigned to other compounds (permuted at compound level, repeated records keep the same response), so y carries no information on X; response distribution, noise, X and the near-identical records are unchanged"),
    },
    controls=[Control("D-042", ["C"], transform=permute_y)],
)
