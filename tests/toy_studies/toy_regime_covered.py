"""Toy: both declared regimes have a criterion -> K7_REGIME_UNCOVERED not raised."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_regime_covered",
    criteria=[
        Criterion("mean_a", lambda d: bool(np.mean(d["x"]) > 1.0), regime="regime_a"),
        Criterion("median_b", lambda d: bool(np.median(d["x"]) > 1.0), regime="regime_b"),
    ],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    controls=[Control("negate", ["mean_a", "median_b"], transform=lambda d, rng: {"x": -d["x"]})],
    regimes=["regime_a", "regime_b"],
    budget=Budget(samples=100),
)
