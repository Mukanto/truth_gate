"""Toy: plus never holds AND the tested premise declares magnitude 1e-20 at scale 1.
Suppression applies to the SL-derived flags, but the unresolvable-magnitude K3_PREMISE_NOT_TESTED is kept."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_suppress_unresolvable",
    criteria=[Criterion("mean_gt_100", lambda d: bool(np.mean(d["x"]) > 100.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_100"], magnitude=(1e-20, 1.0))],
    controls=[Control("negate", ["mean_gt_100"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=60),
)
