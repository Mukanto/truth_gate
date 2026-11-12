"""Toy: correlation of a and b above 0.8, which a shuffle of b destroys -> K5_HOLDS_ON_SHUFFLE not raised."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World


def make_plus(rng):
    a = rng.normal(2.0, 1.0, 30)
    return {"a": a, "b": a + rng.normal(0.0, 0.1, 30)}


STUDY = Study(
    name="toy_shuffle_good",
    criteria=[Criterion("corr_high", lambda d: bool(np.corrcoef(d["a"], d["b"])[0, 1] > 0.8))],
    worlds={
        "plus": World(make_plus),
        "minus": World(
            lambda rng: {"a": rng.normal(2.0, 1.0, 30), "b": rng.normal(2.0, 1.0, 30)},
            derived_from="plus", change="b drawn independently of a",
        ),
    },
    controls=[Control("reverse_b", ["corr_high"], transform=lambda d, rng: {"a": d["a"], "b": d["b"][::-1].copy()})],
    relational=[("a", "b")],
    budget=Budget(samples=100),
)
