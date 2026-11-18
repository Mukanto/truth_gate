"""D-050: Age explains at least 10% of the variance in liver mass beyond what body mass explains: the increase in R-squared when age is added to a regression of liver mass on body mass is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RAT = 80
AGE_LOW = 45.0
AGE_HIGH = 150.0
M_INF = 520.0
M_RATE = 0.028
M_ONSET = 30.0
MASS_NOISE_SD = 0.12
LIVER_CONST = 0.06
LIVER_ON_MASS = 0.9
LIVER_NOISE_SD = 0.10


def _gen(rng, beta):
    age = rng.uniform(AGE_LOW, AGE_HIGH, N_RAT)
    mass = M_INF * (1.0 - np.exp(-M_RATE * (age - M_ONSET))) * np.exp(MASS_NOISE_SD * rng.standard_normal(N_RAT))
    za = (age - 0.5 * (AGE_LOW + AGE_HIGH)) / ((AGE_HIGH - AGE_LOW) / np.sqrt(12.0))
    log_liver = np.log(LIVER_CONST) + LIVER_ON_MASS * np.log(mass) + beta * za + LIVER_NOISE_SD * rng.standard_normal(N_RAT)
    return {
        "liver_mass": np.asarray(np.exp(log_liver), dtype=float),
        "age_days": np.asarray(age, dtype=float),
        "body_mass": np.asarray(mass, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, -0.17)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: liver_mass (80,) float, liver mass in g;
    age_days (80,) float, age in days;
    body_mass (80,) float, body mass in g.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_age_within_mass(d, rng):
    m = np.asarray(d["body_mass"], dtype=float)
    a = np.asarray(d["age_days"], dtype=float)
    order = np.argsort(m, kind="stable")
    out = a.copy()
    block = 10
    for start in range(0, m.shape[0], block):
        idx = order[start:start + block]
        out[idx] = a[idx[rng.permutation(idx.shape[0])]]
    return {"liver_mass": np.asarray(d["liver_mass"], dtype=float), "age_days": out, "body_mass": m}


STUDY = Study(
    name="D-050",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of age on log liver mass at a given body mass (per SD of age) set from -0.17 to 0"),
    },
    controls=[Control("permute_age_within_mass", ["C"], transform=permute_age_within_mass)],
)
