import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 120
MU_A = 18.0
TAU_A = 1.4
ERR_A = 0.4667
MU_E = 4.5
SD_E = 0.8
ERR_V = 0.35
RHO_PLUS = 0.5


def _gen(rng, rho):
    za = rng.standard_normal(N)
    zi = rng.standard_normal(N)
    a_true = MU_A + TAU_A * za
    e_true = MU_E + SD_E * (rho * za + np.sqrt(1.0 - rho ** 2) * zi)
    v_true = a_true - e_true
    a1 = a_true + ERR_A * rng.standard_normal(N)
    a2 = a_true + ERR_A * rng.standard_normal(N)
    v1 = v_true + ERR_V * rng.standard_normal(N)
    v2 = v_true + ERR_V * rng.standard_normal(N)
    return {
        "arterial_o2_content": np.asarray(a1, dtype=float),
        "arterial_o2_content_2": np.asarray(a2, dtype=float),
        "venous_o2_content": np.asarray(v1, dtype=float),
        "venous_o2_content_2": np.asarray(v2, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, RHO_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _permute_extraction(d, rng):
    a = np.asarray(d["arterial_o2_content"], dtype=float)
    v = np.asarray(d["venous_o2_content"], dtype=float)
    v2 = np.asarray(d["venous_o2_content_2"], dtype=float)
    ext = (a - v)[rng.permutation(a.shape[0])]
    v_new = a - ext
    return {
        "arterial_o2_content": a,
        "arterial_o2_content_2": np.asarray(d["arterial_o2_content_2"], dtype=float),
        "venous_o2_content": v_new,
        "venous_o2_content_2": v_new + (v2 - v),
    }


def criterion(d):
    """Data keys, each shape (120,), float, one value per animal, in mL O2 per dL:
    arterial_o2_content (arterial content, first determination), arterial_o2_content_2 (second,
    independent determination of the same content), venous_o2_content (mixed-venous content, first
    determination), venous_o2_content_2 (second, independent determination of the same content).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-002",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between true arterial-minus-venous content difference and true arterial content set from 0.5 to 0"),
    },
    controls=[Control("D-002", ["C"], transform=lambda d, rng: _permute_extraction(d, rng))],
)
