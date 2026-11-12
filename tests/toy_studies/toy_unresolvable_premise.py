"""Toy: the tested premise declares magnitude 3e-19 at scale 1 -> K2_UNRESOLVABLE and K3_PREMISE_NOT_TESTED,
even though the mutation itself flips the outcome."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_unresolvable_premise",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_1"], magnitude=(3e-19, 1.0))],
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
