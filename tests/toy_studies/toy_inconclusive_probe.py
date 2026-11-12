"""Toy: the criterion raises on non-positive data, so noise and zeros are mostly UNDEFINED
-> K5_INCONCLUSIVE:noise and K5_INCONCLUSIVE:zeros (WEAK)."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World


def positive_mean(data):
    if np.any(data["x"] <= 0):
        raise ValueError("non-positive data")
    return bool(np.mean(data["x"]) > 1.5)


STUDY = Study(
    name="toy_inconclusive_probe",
    criteria=[Criterion("pos_mean", positive_mean)],
    worlds={
        "plus": World(lambda rng: {"x": rng.uniform(1.0, 3.0, 30)}),
        "minus": World(lambda rng: {"x": rng.uniform(0.1, 1.0, 30)}, derived_from="plus", change="range [1,3] -> [0.1,1]"),
    },
    controls=[Control("shrink", ["pos_mean"], transform=lambda d, rng: {"x": d["x"] * 0.2})],
    budget=Budget(samples=100),
)
