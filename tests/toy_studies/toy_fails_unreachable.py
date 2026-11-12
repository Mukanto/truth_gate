"""Toy: the criterion always returns True, so it cannot fail in minus -> K2_FAILS_UNREACHABLE."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_fails_unreachable",
    criteria=[Criterion("always_true", lambda d: True)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["always_true"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
