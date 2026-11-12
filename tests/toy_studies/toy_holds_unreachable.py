"""Toy: mean(x) > 100 never holds, not even in plus -> K2_HOLDS_UNREACHABLE."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_holds_unreachable",
    criteria=[Criterion("mean_gt_100", lambda d: bool(np.mean(d["x"]) > 100.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["mean_gt_100"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
