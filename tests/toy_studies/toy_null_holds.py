"""Toy: the declared null world is generated like plus, so the criterion holds on it -> K5_HOLDS_ON_NULL."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_null_holds",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
    },
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
