"""Toy: x[0] > 5 where plus has mean 5, so it holds only half of the time -> K2_LOW_POWER (WEAK)."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_lowpower",
    criteria=[Criterion("x_gt_5", lambda d: bool(d["x"][0] > 5.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(5.0, 1.0, 1)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 1)}, derived_from="plus", change="mean 5 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 1)}),
    },
    controls=[Control("negate", ["x_gt_5"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
