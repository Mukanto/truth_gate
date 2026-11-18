import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 2000
L_MEAN = 12.0
L_SIGMA = 0.14917
H_MEAN = 3.4
W_MEAN = 9.6
B_H = 0.6
B_W = 0.7
U_H = 0.07
U_W = 0.07
RHO_PLUS = 0.40


def _gen(rng, rho):
    zl = rng.standard_normal(N)
    z1 = rng.standard_normal(N)
    z2 = rng.standard_normal(N)
    length = L_MEAN * np.exp(L_SIGMA * zl - 0.5 * L_SIGMA ** 2)
    uh = z1
    uw = rho * z1 + np.sqrt(1.0 - rho ** 2) * z2
    rel = length / L_MEAN
    head = H_MEAN * rel ** B_H * np.exp(U_H * uh)
    wing = W_MEAN * rel ** B_W * np.exp(U_W * uw)
    return {
        "head_width": np.asarray(head, dtype=float),
        "wing_length": np.asarray(wing, dtype=float),
        "body_length": np.asarray(length, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, RHO_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _permute_wing(d, rng):
    w = np.asarray(d["wing_length"], dtype=float)
    return {
        "head_width": np.asarray(d["head_width"], dtype=float),
        "wing_length": w[rng.permutation(w.shape[0])],
        "body_length": np.asarray(d["body_length"], dtype=float),
    }


def criterion(d):
    """Data keys, each shape (2000,), float, one value per specimen, in mm: head_width, wing_length,
    body_length.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-023",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation of the size-independent variation of head width and wing length set from 0.40 to 0"),
    },
    controls=[Control("D-023", ["C"], transform=lambda d, rng: _permute_wing(d, rng))],
)
