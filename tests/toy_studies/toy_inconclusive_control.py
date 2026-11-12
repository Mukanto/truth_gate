"""Toy: the control transform always raises -> K4_INCONCLUSIVE (WEAK)."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World


def broken_transform(data, rng):
    raise ArithmeticError("transform failure")


STUDY = Study(
    name="toy_inconclusive_control",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_1"], magnitude=(2.0, 2.0))],
    controls=[Control("broken", ["mean_gt_1"], transform=broken_transform)],
    budget=Budget(samples=100),
)
