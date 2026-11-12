"""Toy: the criterion raises; the exception type is recorded but the message must not be."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World


def failing(data):
    raise ValueError("secret-detail-12345")


STUDY = Study(
    name="toy_undefined_exc",
    criteria=[Criterion("raises", failing)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 10)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 10)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["raises"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=30),
)
