"""Toy (stochastic): the criterion can never hold (a correlation cannot exceed 2), so plus has zero HOLDS.
Cascade suppression (v0.2 delta 2) removes every SL-derived flag; all eight would otherwise be raised."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World


def make_plus(rng):
    a = rng.normal(2.0, 1.0, 30)
    return {"a": a, "b": a + rng.normal(0.0, 0.1, 30)}


STUDY = Study(
    name="toy_suppress_stoch",
    criteria=[Criterion("corr_gt_2", lambda d: bool(np.corrcoef(d["a"], d["b"])[0, 1] > 2.0))],
    worlds={
        "plus": World(make_plus),
        "minus": World(lambda rng: {"a": rng.normal(0.0, 1.0, 30), "b": rng.normal(0.0, 1.0, 30)},
                       derived_from="plus", change="b independent of a"),
        "null": World(lambda rng: {"a": rng.normal(0.0, 1.0, 30), "b": rng.normal(0.0, 1.0, 30)}),
    },
    premises=[Premise("shift", lambda d, rng: {"a": d["a"] - 1.0, "b": d["b"]}, "tested", ["corr_gt_2"], magnitude=(1.0, 1.0))],
    controls=[Control("negate", ["corr_gt_2"], transform=lambda d, rng: {"a": -d["a"], "b": d["b"]})],
    relational=[("a", "b")],
    budget=Budget(samples=60),
)
