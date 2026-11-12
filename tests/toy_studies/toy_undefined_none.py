"""Toy: the criterion always returns None -> K1_UNDEFINED, verdict UNDEFINED."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_undefined_none",
    criteria=[Criterion("never_defined", lambda d: None)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 10)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 10)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["never_defined"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=30),
)
