"""W24: In trained athletes, aerobic capacity per kilogram of body mass goes with sprint power per kilogram of body mass: across 30 athletes, the proportion of variance in peak power per kilogram explained by maximal oxygen uptake per kilogram (R squared of a simple linear regression) is at least 0.25."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 30


def _gen(rng, r):
    lm = np.log(75.0) + 0.18 * rng.standard_normal(N)
    mass = np.clip(np.exp(lm), 45.0, 130.0)
    e1 = rng.standard_normal(N)
    e2 = rng.standard_normal(N)
    ep = r * e1 + np.sqrt(1.0 - r ** 2) * e2                 # r = 0.5 in plus, 0 in minus (unit variance either way)
    v = 58.0 * np.exp(-0.3 * (lm - np.log(75.0)) + 0.07 * e1)    # mL/kg/min: both ratios fall with body size
    p = 11.0 * np.exp(-0.25 * (lm - np.log(75.0)) + 0.09 * ep)   # W/kg
    return {"vo2max": v * mass / 1000.0, "peak_power": p * mass, "body_mass": mass}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: vo2max (30,) maximal oxygen uptake, L/min, from an incremental treadmill test; peak_power (30,) peak power
    output in a 10-second cycle sprint, W; body_mass (30,) body mass, kg.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_power_per_kg(d, rng):
    pw = d["peak_power"] / d["body_mass"]
    return {**d, "peak_power": pw[rng.permutation(N)] * d["body_mass"]}


STUDY = Study(
    name="W24",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="residual (size-independent) correlation between aerobic capacity per kg and sprint power per kg 0.5 -> 0; the common dependence of both ratios on body mass (shared denominator) and all variances unchanged"),
    },
    controls=[Control("permute_power_per_kg", ["C"], transform=permute_power_per_kg)],
)
