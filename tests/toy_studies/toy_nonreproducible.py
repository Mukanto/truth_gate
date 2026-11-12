"""Toy: the criterion uses unseeded global randomness -> K6_NONREPRODUCIBLE."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_nonreproducible",
    criteria=[Criterion("coin", lambda d: bool(np.random.random() < 0.5))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 10)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 10)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["coin"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=60),
)
