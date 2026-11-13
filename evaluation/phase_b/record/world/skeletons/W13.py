"""W13: Reaction time depends more strongly on stimulus contrast in the attended condition than in the unattended condition: the regression slope of reaction time on contrast is steeper in the attended condition than in the unattended condition across 30 participants, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 30


def _gen(rng, extra):
    c = rng.uniform(0.05, 0.50, N)                           # contrast level shown to each participant
    subj = 60.0 * rng.standard_normal(N)                     # participant speed, shared by both conditions
    e1 = rng.standard_normal(N)
    e2 = rng.standard_normal(N)
    rt_unattended = 560.0 + subj - 150.0 * c + 20.0 * e2
    rt_attended = 520.0 + subj - (150.0 + extra) * c + 20.0 * e1
    return {"contrast": c, "rt_attended": rt_attended, "rt_unattended": rt_unattended}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 120.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: contrast (30,) stimulus contrast level shown to each participant; rt_attended (30,) mean reaction time in
    the attended condition, same participant order; rt_unattended (30,) mean reaction time in the unattended condition,
    same participants.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_contrast(d, rng):
    return {**d, "contrast": d["contrast"][rng.permutation(N)]}


STUDY = Study(
    name="W13",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="attended slope -270 ms per unit contrast, unattended -150 -> both -150 (equal slopes); participant speed shared across conditions, noise and contrast range unchanged"),
    },
    controls=[Control("permute_contrast", ["C"], transform=permute_contrast)],
)
