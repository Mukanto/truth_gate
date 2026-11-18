import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 150
M = 3
MU0 = 130.0
TAU = 14.2829
ERR = 6.0
MU_S = 1.0
SD_S = 3.0
RHO_PLUS = -0.65


def _gen(rng, rho):
    z1 = rng.standard_normal(N)
    z2 = rng.standard_normal(N)
    a = MU0 + TAU * z1
    s = MU_S + SD_S * (rho * z1 + np.sqrt(1.0 - rho ** 2) * z2)
    t = np.arange(M, dtype=float)
    x = a[:, None] + s[:, None] * t[None, :] + ERR * rng.standard_normal((N, M))
    return {"systolic_bp": np.asarray(x, dtype=float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, RHO_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _swap_slopes(d, rng):
    x = np.asarray(d["systolic_bp"], dtype=float)
    m = x.shape[1]
    tc = np.arange(m, dtype=float) - (m - 1) / 2.0
    b = (x - x.mean(axis=1, keepdims=True)) @ tc / np.sum(tc ** 2)
    bp = b[rng.permutation(x.shape[0])]
    return {"systolic_bp": x + (bp - b)[:, None] * tc[None, :]}


def criterion(d):
    """Data keys: systolic_bp, shape (150, 3), float: systolic blood pressure (mmHg) of each
    individual (rows) at each of three annual visits (columns, in time order).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-001",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between true yearly slope and true initial level set from -0.65 to 0"),
    },
    controls=[Control("D-001", ["C"], transform=lambda d, rng: _swap_slopes(d, rng))],
)
