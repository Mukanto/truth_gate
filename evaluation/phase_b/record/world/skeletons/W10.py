"""W10: Over three practice sessions the trained group improves faster than the control group: the average per-session change in performance is larger in the trained group than in the control group, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

NP, NS = 14, 3


def _group(rng, slope):
    base = 10.0 * rng.standard_normal((NP, 1))               # between-participant level
    ind = 1.5 * rng.standard_normal((NP, 1))                 # individual slope variation
    e = rng.standard_normal((NP, NS))
    t = np.arange(NS)[None, :]
    return 50.0 + base + (slope + ind) * t + 4.0 * e


def _gen(rng, extra):
    trained = _group(rng, 2.0 + extra)                       # everybody improves with practice (2 points/session)
    control = _group(rng, 2.0)
    return {"perf_trained": trained, "perf_control": control}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 3.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: perf_trained (14, 3) performance score of each trained participant at each session, axes (participants,
    sessions in time order); perf_control (14, 3) same for the control group.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def reshuffle_groups(d, rng):
    both = np.concatenate([d["perf_trained"], d["perf_control"]], axis=0)[rng.permutation(2 * NP)]
    return {**d, "perf_trained": both[:NP].copy(), "perf_control": both[NP:].copy()}


STUDY = Study(
    name="W10",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="trained slope = control slope + 3.5 points/session -> trained slope = control slope (2 points/session, so both groups still improve); levels, individual slopes and noise unchanged"),
    },
    controls=[Control("reshuffle_groups", ["C"], transform=reshuffle_groups)],
)
