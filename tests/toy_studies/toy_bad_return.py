"""Toy: the criterion returns a float instead of a bool -> BAD_RETURN, treated as UNDEFINED."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_bad_return",
    criteria=[Criterion("returns_float", lambda d: float(np.mean(d["x"])))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 10)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 10)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["returns_float"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=30),
)
