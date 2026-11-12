"""Toy: regimes regime_a and regime_b are declared but only regime_a has a criterion -> K7_REGIME_UNCOVERED."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_regime_uncovered",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0), regime="regime_a")],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],
    regimes=["regime_a", "regime_b"],
    budget=Budget(samples=100),
)
