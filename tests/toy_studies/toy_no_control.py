"""Toy: no negative control and no waiver -> K4_NO_CONTROL."""
import numpy as np

from kapi import Budget, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_no_control",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_1"], magnitude=(2.0, 2.0))],
    budget=Budget(samples=100),
)
