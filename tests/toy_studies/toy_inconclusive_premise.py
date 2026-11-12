"""Toy: the premise mutator always raises -> K3_INCONCLUSIVE (WEAK), not K3_PREMISE_NOT_TESTED."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World


def broken_mutator(data, rng):
    raise RuntimeError("mutator failure")


STUDY = Study(
    name="toy_inconclusive_premise",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("broken", broken_mutator, "tested", ["mean_gt_1"], magnitude=(2.0, 2.0))],
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
