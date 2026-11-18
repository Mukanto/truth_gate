"""D-072: In 30 subjects each studied in a vehicle session and in a drug session, the drug raises muscle force: the mean paired difference in force between the drug and the vehicle session, adjusted for the muscle cross-sectional area measured in each session by analysis of covariance, is positive with a two-sided p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 30
AREA_MEAN = 75.0
AREA_SD = 12.0
AREA_SESSION_SD = 2.12
AREA_DRUG_SHIFT = 1.5
F0 = 400.0
F_SLOPE = 3.5
F_SUBJECT_SD = 60.0
F_SESSION_SD = 33.0
EFFECT_PLUS = 28.0


def _gen(rng, effect):
    a = AREA_MEAN + AREA_SD * rng.standard_normal(N)
    u = F_SUBJECT_SD * rng.standard_normal(N)
    area_v = a + AREA_SESSION_SD * rng.standard_normal(N)
    area_d = a + AREA_DRUG_SHIFT + AREA_SESSION_SD * rng.standard_normal(N)
    force_v = F0 + F_SLOPE * area_v + u + F_SESSION_SD * rng.standard_normal(N)
    force_d = F0 + F_SLOPE * area_d + u + effect + F_SESSION_SD * rng.standard_normal(N)
    return {
        "force_vehicle": np.asarray(force_v, dtype=float),
        "force_drug": np.asarray(force_d, dtype=float),
        "area_vehicle": np.asarray(area_v, dtype=float),
        "area_drug": np.asarray(area_d, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, EFFECT_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _swap_sessions(d, rng):
    fv = np.asarray(d["force_vehicle"], dtype=float)
    fd = np.asarray(d["force_drug"], dtype=float)
    av = np.asarray(d["area_vehicle"], dtype=float)
    ad = np.asarray(d["area_drug"], dtype=float)
    sw = rng.random(fv.shape[0]) < 0.5
    return {
        "force_vehicle": np.where(sw, fd, fv),
        "force_drug": np.where(sw, fv, fd),
        "area_vehicle": np.where(sw, ad, av),
        "area_drug": np.where(sw, av, ad),
    }


def criterion(d):
    """Data keys, each shape (30,), float, one value per subject: force_vehicle and force_drug (peak
    voluntary knee-extension force in the vehicle and in the drug session, N), area_vehicle and
    area_drug (quadriceps cross-sectional area measured in the vehicle and in the drug session, cm2).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-072",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="drug effect on force at equal area set from +28 N to 0"),
    },
    controls=[Control("D-072", ["C"], transform=lambda d, rng: _swap_sessions(d, rng))],
)
