"""Spec 0.7 fixture (deterministic): the criterion abstains on the empty plus sample, so the only plus sample is an
abstention (rate 1, above one half): K1_UNDEFINED is legitimate in 0.5.  ``ABSTAIN`` as in abs_minus.py."""
import numpy as np

from truth_gate import Control, Criterion, Study, World

ABSTAIN = None


def first_positive(d):
    if d["v"].size == 0:
        return ABSTAIN
    return bool(d["v"][0] > 0)


STUDY = Study(
    name="spec07_det_abs_plus",
    criteria=[Criterion("first_positive", first_positive)],
    worlds={
        "plus": World(lambda rng: {"v": np.array([])}),
        "minus": World(lambda rng: {"v": np.array([-3.0])}, derived_from="plus", change="non-empty negative"),
    },
    controls=[Control("negate", ["first_positive"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
