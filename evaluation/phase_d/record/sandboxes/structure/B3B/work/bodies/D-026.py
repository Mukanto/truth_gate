import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 400
P = 6
L_MEAN = 12.0
L_SIGMA = 0.14917
DIM_MEAN = np.array([3.0, 8.0, 5.5, 4.2, 6.5, 2.4])
B = np.array([0.55, 0.65, 0.60, 0.70, 0.62, 0.58])
SD_TOTAL = np.array([0.08, 0.07, 0.09, 0.075, 0.085, 0.08])
LOAD_PLUS = np.array([0.055, 0.05, 0.06, 0.05, 0.055, 0.045])


def _gen(rng, load):
    zl = rng.standard_normal(N)
    f = rng.standard_normal(N)
    eps = rng.standard_normal((N, P))
    length = L_MEAN * np.exp(L_SIGMA * zl - 0.5 * L_SIGMA ** 2)
    uniq = np.sqrt(SD_TOTAL ** 2 - load ** 2)
    u = load[None, :] * f[:, None] + uniq[None, :] * eps
    rel = (length / L_MEAN)[:, None]
    skel = DIM_MEAN[None, :] * rel ** B[None, :] * np.exp(u)
    return {
        "skeletal": np.asarray(skel, dtype=float),
        "body_length": np.asarray(length, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, LOAD_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, np.zeros(P))


def _permute_columns(d, rng):
    s = np.asarray(d["skeletal"], dtype=float)
    out = np.empty_like(s)
    for j in range(s.shape[1]):
        out[:, j] = s[rng.permutation(s.shape[0]), j]
    return {"skeletal": out, "body_length": np.asarray(d["body_length"], dtype=float)}


def criterion(d):
    """Data keys: skeletal, shape (400, 6), float: six linear skeletal dimensions (mm) of each specimen
    (rows = specimens, columns = dimensions); body_length, shape (400,), float: body length (mm) of each
    specimen.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-026",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="loadings of the six dimensions on the common shape factor set to 0 (total size-independent variance of each dimension unchanged)"),
    },
    controls=[Control("D-026", ["C"], transform=lambda d, rng: _permute_columns(d, rng))],
)
