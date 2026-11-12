"""Toy: the negative control is a separate world (kind 'world') instead of a transform -> FALSIFIABLE."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_control_world",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    controls=[Control("decoy", ["mean_gt_1"], world=World(lambda rng: {"x": rng.normal(-1.0, 1.0, 40)}))],
    budget=Budget(samples=100),
)
