"""W23: Larger hospitals have lower hospital-acquired infection rates per admission: across 100 hospitals, the standardised regression slope (variables z-scored) of infections per admission on the number of beds is at most -0.3."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 100


def _gen(rng, eff):
    lb = np.log(300.0) + 0.6 * rng.standard_normal(N)
    beds = np.maximum(np.round(np.exp(lb)), 20.0)
    zl = (lb - np.log(300.0)) / 0.6
    adm = np.round(beds * 40.0 * np.exp(0.15 * rng.standard_normal(N)))      # admissions per year, proportional to beds
    rate = 0.03 * np.exp(-eff * 0.22 * zl + 0.30 * rng.standard_normal(N))    # true infections per admission
    infections = rng.poisson(rate * adm).astype(float)
    return {"infections": infections, "admissions": adm, "beds": beds}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: infections (100,) number of hospital-acquired infections recorded in one year; admissions (100,) number of
    patient admissions in the same year; beds (100,) number of staffed beds.
    Holds when the claim is supported by the data. Written by someone else."""
    def z(x):
        return (x - x.mean()) / x.std()

    inf = np.asarray(d["infections"], dtype=float)
    adm = np.asarray(d["admissions"], dtype=float)
    beds = np.asarray(d["beds"], dtype=float)
    if not (np.all(np.isfinite(inf)) and np.all(np.isfinite(adm)) and np.all(np.isfinite(beds))):
        return None
    if np.std(inf) == 0 or np.std(adm) == 0 or np.std(beds) == 0:
        return None
    zi, za, zb = z(inf), z(adm), z(beds)
    X = np.column_stack([np.ones(len(zi)), zb, za])
    coef = np.linalg.lstsq(X, zi, rcond=None)[0]     # infections on beds with admissions as a covariate
    return bool(coef[1] <= -0.3)


def permute_beds(d, rng):
    return {**d, "beds": d["beds"][rng.permutation(N)]}


STUDY = Study(
    name="W23",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true infection rate per admission falls with hospital size (-0.22 log units per sd of log beds) -> independent of size; admissions proportional to beds, between-hospital heterogeneity and Poisson counts unchanged"),
    },
    controls=[Control("permute_beds", ["C"], transform=permute_beds)],
)
