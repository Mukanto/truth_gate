"""D-017: At a given height, the mean forced vital capacity of smokers and of non-smokers differs by at least 0.2 L: the difference between the two group means, after accounting for height, is at least 0.2 L in absolute value."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUB = 600
P_MALE = 0.5
H_MALE = (176.0, 7.0)
H_FEMALE = (163.0, 6.5)
P_SMOKE_MALE = 0.26
P_SMOKE_FEMALE = 0.15
FVC_INTERCEPT = -4.0
FVC_SLOPE = 0.05
FVC_SD = 0.45


def _gen(rng, delta):
    male = rng.random(N_SUB) < P_MALE
    z = rng.standard_normal(N_SUB)
    height = np.where(male, H_MALE[0] + H_MALE[1] * z, H_FEMALE[0] + H_FEMALE[1] * z)
    smoker = rng.random(N_SUB) < np.where(male, P_SMOKE_MALE, P_SMOKE_FEMALE)
    fvc = FVC_INTERCEPT + FVC_SLOPE * height - delta * smoker + FVC_SD * rng.standard_normal(N_SUB)
    return {
        "fvc": np.asarray(fvc, dtype=float),
        "height": np.asarray(height, dtype=float),
        "smoker": np.asarray(smoker, dtype=bool),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.30)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: fvc (600,) float, forced vital capacity in litres;
    height (600,) float, standing height in cm;
    smoker (600,) bool, True if the subject is a current smoker.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_smoker_within_height(d, rng):
    h = np.asarray(d["height"], dtype=float)
    s = np.asarray(d["smoker"], dtype=bool)
    order = np.argsort(h, kind="stable")
    out = s.copy()
    block = 60
    for start in range(0, h.shape[0], block):
        idx = order[start:start + block]
        out[idx] = s[idx[rng.permutation(idx.shape[0])]]
    return {"fvc": np.asarray(d["fvc"], dtype=float), "height": h, "smoker": out}


STUDY = Study(
    name="D-017",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="smoker effect on forced vital capacity at a given height set from -0.30 L to 0"),
    },
    controls=[Control("permute_smoker_within_height", ["C"], transform=permute_smoker_within_height)],
)
