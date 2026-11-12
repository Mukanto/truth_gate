"""Toy: max(x) < 0.5 holds on all-zero data but not on noise -> K5_HOLDS_ON_DEGENERATE only."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_degenerate",
    criteria=[Criterion("all_below", lambda d: bool(np.max(d["x"]) < 0.5))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(-3.0, 0.5, 20)}),
        "minus": World(lambda rng: {"x": rng.normal(3.0, 0.5, 20)}, derived_from="plus", change="mean -3 -> 3"),
    },
    controls=[Control("flip", ["all_below"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
