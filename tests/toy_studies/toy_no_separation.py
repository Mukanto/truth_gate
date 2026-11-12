"""Toy: plus and minus are the same distribution, so mean(x) > 0 holds half the time in both -> K2_NO_SEPARATION."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_no_separation",
    criteria=[Criterion("mean_gt_0", lambda d: bool(np.mean(d["x"]) > 0.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="none (declared faulty)"),
    },
    controls=[Control("negate", ["mean_gt_0"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
