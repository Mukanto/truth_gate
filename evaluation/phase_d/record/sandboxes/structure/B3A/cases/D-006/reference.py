"""D-006: Across children, BMI at age 5 and the yearly rate of change in BMI between ages 5 and 10 are negatively correlated: the correlation between the two is at most -0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_CHILD = 500
N_VISIT = 6
LEVEL_MEAN = 15.0
LEVEL_SD = 1.2
SLOPE_MEAN = 0.4
SLOPE_SD = 0.2
ERR_SD = 0.3


def _gen(rng, rho):
    level = LEVEL_MEAN + LEVEL_SD * rng.standard_normal(N_CHILD)
    z = (level - LEVEL_MEAN) / LEVEL_SD
    eps = rng.standard_normal(N_CHILD)
    slope = SLOPE_MEAN + SLOPE_SD * (rho * z + np.sqrt(1.0 - rho ** 2) * eps)
    t = np.arange(N_VISIT, dtype=float)
    true = level[:, None] + slope[:, None] * t[None, :]
    bmi = true + ERR_SD * rng.standard_normal((N_CHILD, N_VISIT))
    return {"bmi": np.asarray(bmi, dtype=float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, -0.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: bmi (500, 6) float, BMI in kg/m2 of each child at the annual visits at ages 5..10, visits in age order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_profiles(d, rng):
    y = np.asarray(d["bmi"], dtype=float)
    dev = y - y[:, :1]
    perm = rng.permutation(y.shape[0])
    return {"bmi": y[:, :1] + dev[perm]}


STUDY = Study(
    name="D-006",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between true BMI level at age 5 and true yearly slope set from -0.5 to 0"),
    },
    controls=[Control("permute_change_profiles", ["C"], transform=permute_profiles)],
)
