"""Spec 0.7 fixture (stochastic): the criterion abstains on about 25% of the plus samples (no peak detected), which
is below one half, so 0.5 must not make the component UNDEFINED.  ``ABSTAIN`` as in abs_minus.py."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World

ABSTAIN = None


def tall_peak(d):
    peaks = d["peaks"]
    if peaks.size == 0:
        return ABSTAIN
    return bool(peaks.max() > 5.0)


def plus(rng):
    return {"peaks": rng.normal(8.0, 1.0, 0 if rng.random() < 0.25 else 3)}


STUDY = Study(
    name="spec07_abs_plus_below_half",
    criteria=[Criterion("tall_peak", tall_peak)],
    worlds={
        "plus": World(plus),
        "minus": World(lambda rng: {"peaks": rng.normal(2.0, 1.0, 3)}, derived_from="plus", change="peaks 8 -> 2"),
    },
    controls=[Control("negate", ["tall_peak"], transform=lambda d, rng: {"peaks": -d["peaks"]})],
    budget=Budget(samples=40),
)
