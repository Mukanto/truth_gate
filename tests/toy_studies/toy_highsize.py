"""Toy: x[0] > 3 holds in about 20% of minus samples -> K2_HIGH_SIZE (WEAK)."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_highsize",
    criteria=[Criterion("x_gt_3", lambda d: bool(d["x"][0] > 3.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(6.0, 1.0, 1)}),
        "minus": World(lambda rng: {"x": rng.normal(2.2, 1.0, 1)}, derived_from="plus", change="mean 6 -> 2.2"),
    },
    controls=[Control("negate", ["x_gt_3"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
