"""Spec 0.7 fixture (deterministic): the criterion abstains on the empty minus sample.  ``ABSTAIN`` as in
abs_minus.py."""
import numpy as np

from truth_gate import Control, Criterion, Study, World

ABSTAIN = None


def first_large(d):
    if d["v"].size == 0:
        return ABSTAIN
    return bool(d["v"][0] > 2.0)


STUDY = Study(
    name="spec07_det_abs_minus",
    criteria=[Criterion("first_large", first_large)],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0])}),
        "minus": World(lambda rng: {"v": np.array([])}, derived_from="plus", change="no value at all"),
    },
    controls=[Control("negate", ["first_large"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
