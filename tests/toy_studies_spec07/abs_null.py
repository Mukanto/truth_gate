"""Spec 0.7 fixture (stochastic): the criterion abstains on about 25% of the null samples.  ``ABSTAIN`` as in
abs_minus.py."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World

ABSTAIN = None


def tall_peak(d):
    peaks = d["peaks"]
    if peaks.size == 0:
        return ABSTAIN
    return bool(peaks.max() > 5.0)


def null(rng):
    return {"peaks": rng.normal(2.0, 1.0, int(rng.integers(0, 4)))}


STUDY = Study(
    name="spec07_abs_null",
    criteria=[Criterion("tall_peak", tall_peak)],
    worlds={
        "plus": World(lambda rng: {"peaks": rng.normal(8.0, 1.0, 3)}),
        "minus": World(lambda rng: {"peaks": rng.normal(2.0, 1.0, 3)}, derived_from="plus", change="peaks 8 -> 2"),
        "null": World(null),
    },
    controls=[Control("negate", ["tall_peak"], transform=lambda d, rng: {"peaks": -d["peaks"]})],
    budget=Budget(samples=40),
)
