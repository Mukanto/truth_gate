"""W30: In a fraud-screening data set where about 12% of transactions are fraudulent, a nearest-neighbour rule on 10 transaction features achieves an F1 score of at least 0.60 for fraud on new transactions."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 150, 10


def _gen(rng, eff):
    fraud = rng.random(N) < 0.12
    x = rng.standard_normal((N, K))
    x[:, :6] += eff * 1.6 * fraud[:, None]                   # six informative features
    x = (x - x.mean(axis=0)) / x.std(axis=0)                 # standardised
    return {"features": x, "fraud": fraud.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: features (150, 10) standardised transaction features; fraud (150,) bool, True for a fraudulent transaction
    (about 18 of 150).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_fraud(d, rng):
    return {**d, "fraud": d["fraud"][rng.permutation(N)]}


STUDY = Study(
    name="W30",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="six of ten features shifted 1.6 sd for fraudulent transactions -> no feature carries information about fraud; prevalence (12%), sample size and standardisation unchanged"),
    },
    controls=[Control("permute_fraud", ["C"], transform=permute_fraud)],
)
