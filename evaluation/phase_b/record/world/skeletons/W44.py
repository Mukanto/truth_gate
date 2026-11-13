"""W44: Across participants, grip strength is positively correlated with cortical thickness in the motor cortex: the correlation between the two measures is greater than zero at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 10


def _gen(rng, r):
    zg = rng.standard_normal(N)
    zt = r * zg + np.sqrt(1.0 - r ** 2) * rng.standard_normal(N)          # between-participant correlation r
    e_g = rng.standard_normal((N, 2))
    e_t = rng.standard_normal((N, 2))
    grip = (35.0 + 6.0 * zg)[:, None] + np.array([0.0, 3.0])[None, :] + 1.5 * e_g           # kg; intervention adds 3 kg
    thick = (2.6 + 0.25 * zt)[:, None] + np.array([0.0, 0.10])[None, :] + 0.08 * e_t        # mm; intervention adds 0.1 mm
    return {"grip": grip, "thickness": thick}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.8)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: grip (10, 2) grip strength at each of the two sessions, axes (participants, sessions: before and after the
    intervention); thickness (10, 2) motor cortex thickness measured at the same session, same layout.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_thickness(d, rng):
    return {**d, "thickness": d["thickness"][rng.permutation(N)]}


STUDY = Study(
    name="W44",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="between-participant correlation of true grip strength and true thickness 0.8 -> 0; session means (intervention shift), session-to-session measurement noise and the 10 x 2 layout unchanged"),
    },
    controls=[Control("permute_thickness", ["C"], transform=permute_thickness)],
)
