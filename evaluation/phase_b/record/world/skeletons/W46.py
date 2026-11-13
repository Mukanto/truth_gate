"""W46: Mussel growth increases with the amount of food supplement given to a tank: the regression slope of growth on the supplement dose is positive, at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

T, M = 12, 8


def _gen(rng, slope):
    dose = rng.permutation(np.linspace(0.0, 5.0, T))                       # one dose per tank, assigned to tanks at random
    tank = 0.8 * rng.standard_normal((T, 1))                               # tank effect: the tank is the unit of replication
    e = 1.5 * rng.standard_normal((T, M))
    growth = 8.0 + slope * dose[:, None] + tank + e
    return {"dose": dose, "growth": growth}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.45)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: dose (12,) supplement dose assigned to each tank; growth (12, 8) shell growth of each measured mussel, axes
    (tanks, individual mussels per tank), in the tank given by the first axis.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_dose(d, rng):
    return {**d, "dose": d["dose"][rng.permutation(T)]}


STUDY = Study(
    name="W46",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true growth rises 0.45 per dose unit (tank-level t about 2.8) -> slope 0; tank effects (sd 0.8), mussel noise (sd 1.5), the dose set (12 levels from 0 to 5) and the 12 x 8 layout unchanged"),
    },
    controls=[Control("permute_dose", ["C"], transform=permute_dose)],
)
