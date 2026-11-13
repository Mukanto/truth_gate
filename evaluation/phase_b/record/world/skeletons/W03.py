"""W03: Participants who received the treatment score higher than controls on the outcome: a one-sided Welch t test of treated versus control gives p < 0.05 once recruitment of the planned sample is complete."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 30


def _gen(rng, eff):
    drift = 3.0 * np.arange(N) / N                   # slow drift with recruitment order, both arms
    treated = 50.0 + drift + eff + 10.0 * rng.standard_normal(N)
    control = 50.0 + drift + 10.0 * rng.standard_normal(N)
    return {"treated": treated, "control": control}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 8.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: treated (30,) outcome score of each treated participant, rows in order of recruitment;
    control (30,) outcome score of each control participant, rows in order of recruitment.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def pool_and_resplit(d, rng):
    pooled = np.concatenate([d["treated"], d["control"]])[rng.permutation(2 * N)]
    return {**d, "treated": pooled[:N].copy(), "control": pooled[N:].copy()}


STUDY = Study(
    name="W03",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect 8 points (d = 0.8) -> 0; sd, drift and sample sizes unchanged"),
    },
    controls=[Control("pool_and_resplit", ["C"], transform=pool_and_resplit)],
)
