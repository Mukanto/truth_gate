"""Toy (deterministic): the criterion cannot be evaluated on plus (empty array) -> K1_UNDEFINED."""
import numpy as np

from kapi import Control, Criterion, Study, World


def first_positive(data):
    if data["v"].size == 0:
        return None
    return bool(data["v"][0] > 0)


STUDY = Study(
    name="toy_det_undefined",
    criteria=[Criterion("first_positive", first_positive)],
    worlds={
        "plus": World(lambda rng: {"v": np.array([])}),
        "minus": World(lambda rng: {"v": np.array([-3.0])}, derived_from="plus", change="non-empty negative"),
    },
    controls=[Control("negate", ["first_positive"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
