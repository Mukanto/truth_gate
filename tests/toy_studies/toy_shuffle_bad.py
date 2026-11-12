"""Toy: mean(a) + mean(b) > 3 ignores the pairing of a and b -> K5_HOLDS_ON_SHUFFLE."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_shuffle_bad",
    criteria=[Criterion("sum_high", lambda d: bool(np.mean(d["a"]) + np.mean(d["b"]) > 3.0))],
    worlds={
        "plus": World(lambda rng: {"a": rng.normal(2.0, 1.0, 30), "b": rng.normal(2.0, 1.0, 30)}),
        "minus": World(
            lambda rng: {"a": rng.normal(0.0, 1.0, 30), "b": rng.normal(0.0, 1.0, 30)},
            derived_from="plus", change="means 2 -> 0",
        ),
    },
    controls=[Control("negate_a", ["sum_high"], transform=lambda d, rng: {"a": -d["a"], "b": d["b"]})],
    relational=[("a", "b")],
    budget=Budget(samples=100),
)
