"""W12: Students in the lowest fifth of the autumn test gain at least 5 points on the spring test after the tutoring programme: the claim holds when the mean gain of those students is at least 5 and one-sided one-sample t-test p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 250


def _gen(rng, eff):
    ability = 60.0 + 10.0 * rng.standard_normal(N)
    e0 = rng.standard_normal(N)
    e1 = rng.standard_normal(N)
    e2 = rng.standard_normal(N)
    tut = eff * (7.0 + 5.0 * rng.standard_normal(N))             # tutoring effect, points
    s0 = ability + 7.0 * e0                                      # autumn
    s1 = ability + 7.0 * e1                                      # second pre-tutoring test
    s2 = ability + tut + 7.0 * e2                                # spring
    return {"score": np.clip(np.column_stack([s0, s1, s2]), 0.0, 100.0)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: score (250, 3) test scores out of 100, axes (students, tests): test 0 = autumn, test 1 = a second test
    given just before the tutoring began, test 2 = spring.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def remove_average_tutoring_gain(d, rng):
    s = d["score"].copy()
    s[:, 2] = s[:, 2] - (s[:, 2].mean() - s[:, 1].mean())        # no average gain from tutoring
    return {**d, "score": s}


STUDY = Study(
    name="W12",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="tutoring effect on the spring score (7 points on average, sd 5) -> 0; ability spread (sd 10), test noise (sd 7) and the repeat pre-test unchanged"),
    },
    controls=[Control("remove_average_tutoring_gain", ["C"], transform=remove_average_tutoring_gain)],
)
