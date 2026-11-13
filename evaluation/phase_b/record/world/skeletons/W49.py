"""W49: From 15 patient characteristics, ridge regression predicts length of stay in patients from new hospitals with R^2 of at least 0.40."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

H, P, F = 12, 20, 15


def _gen(rng, eff):
    off = 0.7 * rng.standard_normal((H, 1, F))               # hospital-specific shift of every characteristic
    x = off + rng.standard_normal((H, P, F))
    beta = np.zeros(F)
    beta[:6] = 0.37                                          # six characteristics matter
    re = np.sqrt(0.5) * rng.standard_normal((H, 1))          # hospital effect on length of stay (practice style)
    eps = np.sqrt(0.45) * rng.standard_normal((H, P))
    stay = 6.0 + 1.3 * (eff * (x @ beta) + re + eps)
    return {"x": x, "stay": np.maximum(stay, 0.5)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: x (12, 20, 15) characteristics of each patient in each hospital, axes (hospitals, patients, characteristics);
    stay (12, 20) length of stay in days, axes (hospitals, patients).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_stay_within_hospitals(d, rng):
    idx = np.argsort(rng.random((H, P)), axis=1)
    return {**d, "stay": np.take_along_axis(d["stay"], idx, axis=1)}


STUDY = Study(
    name="W49",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="patient-level effect of six characteristics on length of stay (variance 1.2 against hospital effect 0.5 and noise 0.45; ceiling R squared about 0.56 in new hospitals) -> no patient-level effect; the hospital effects on stay, the hospital shifts of the characteristics (which let a random split recognise the hospital) and the noise unchanged"),
    },
    controls=[Control("permute_stay_within_hospitals", ["C"], transform=permute_stay_within_hospitals)],
)
