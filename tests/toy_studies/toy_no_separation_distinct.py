"""Toy: minus differs from plus in the data, but not in a way the criterion can see (the criterion reads the sign of
the mean, and both worlds have mean 0), so mean(x) > 0 holds half the time in both -> K2_NO_SEPARATION without an
identical minus.  Replacement for toy_no_separation under spec 0.5, where that toy's minus is identical by pairing."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_no_separation_distinct",
    criteria=[Criterion("mean_gt_0", lambda d: bool(np.mean(d["x"]) > 0.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 2.0, 40)}, derived_from="plus", change="spread 1 -> 2"),
    },
    controls=[Control("negate", ["mean_gt_0"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
