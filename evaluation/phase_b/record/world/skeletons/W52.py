"""W52: Among patients with a depression score in the top fifth at the first assessment, at least 70% have a lower score after the 8-week programme than before it."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 120


def _gen(rng, eff):
    true = 22.0 + 8.0 * rng.standard_normal(N)                            # stable severity
    e0 = rng.standard_normal(N)
    e1 = rng.standard_normal(N)
    e2 = rng.standard_normal(N)
    prog = eff * (-9.0 + 4.0 * rng.standard_normal(N))                    # programme effect on the final score
    s0 = true + 6.0 * e0                                                  # first assessment
    s1 = true + 6.0 * e1                                                  # second assessment, just before the programme
    s2 = true + prog + 6.0 * e2                                           # after the programme
    return {"score": np.maximum(np.column_stack([s0, s1, s2]), 0.0)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: score (120, 3) depression questionnaire score, axes (patients, visits): visit 0 = first assessment, visit 1 =
    second assessment just before the programme, visit 2 = after the programme.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def remove_average_programme_effect(d, rng):
    s = d["score"].copy()
    s[:, 2] = s[:, 2] - (s[:, 2].mean() - s[:, 1].mean())                 # no average change from the programme
    return {**d, "score": s}


STUDY = Study(
    name="W52",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="programme lowers the final score by 9 points on average (sd 4) -> no programme effect; severity spread (sd 8) and assessment noise (sd 6 at each visit, so regression to the mean for the top fifth) unchanged"),
    },
    controls=[Control("remove_average_programme_effect", ["C"], transform=remove_average_programme_effect)],
)
