"""Toy (deterministic): the criterion raises for values in (0.5, 20). With base_seed 4 exactly one of the three noise
draws is UNDEFINED and two are FAILS -> the combined noise outcome is FAILS: no K5_INCONCLUSIVE:noise."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World


def above_twenty(data):
    first = float(data["v"][0])
    if 0.5 < first < 20.0:
        raise ValueError("value in the excluded band")
    return first > 20.0


STUDY = Study(
    name="toy_det_noise_one_undefined",
    criteria=[Criterion("above_twenty", above_twenty)],
    worlds={
        "plus": World(lambda rng: {"v": np.array([30.0, 30.0])}),
        "minus": World(lambda rng: {"v": np.array([-30.0, -30.0])}, derived_from="plus", change="sign flipped"),
    },
    controls=[Control("negate", ["above_twenty"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
    budget=Budget(base_seed=4),
)
