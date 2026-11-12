"""Toy: 0.7 < std(x) < 1.4 holds on N(0, 1) noise but not on zeros -> K5_HOLDS_ON_NOISE only."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_noise",
    criteria=[Criterion("unit_spread", lambda d: bool(0.7 < np.std(d["x"]) < 1.4))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 100)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 3.0, 100)}, derived_from="plus", change="std 1 -> 3"),
    },
    controls=[Control("widen", ["unit_spread"], transform=lambda d, rng: {"x": d["x"] * 3.0})],
    budget=Budget(samples=100),
)
