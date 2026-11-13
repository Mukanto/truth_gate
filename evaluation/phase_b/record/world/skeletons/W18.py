"""W18: In a screening cohort where about one sample in five is positive, a nearest-neighbour rule on 30 biomarkers attains balanced accuracy of at least 0.75 on new samples."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 100, 30


def _gen(rng, eff):
    positive = rng.random(N) < 0.20
    x = rng.standard_normal((N, K))
    x[:, :15] += eff * 1.1 * positive[:, None]               # 15 informative biomarkers
    x = (x - x.mean(axis=0)) / x.std(axis=0)                 # standardised
    return {"biomarkers": x, "positive": positive.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: biomarkers (100, 30) standardised biomarker values; positive (100,) bool, True for a positive sample
    (about 20 of 100).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_positive(d, rng):
    return {**d, "positive": d["positive"][rng.permutation(N)]}


STUDY = Study(
    name="W18",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="15 of 30 biomarkers shifted 1.1 sd in positive samples -> no biomarker carries information about status; sample size, prevalence (0.2) and standardisation unchanged"),
    },
    controls=[Control("permute_positive", ["C"], transform=permute_positive)],
)
