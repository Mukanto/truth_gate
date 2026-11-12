"""Toy: components lo and hi are declared, only lo is returned -> K7_COMPONENT_MISMATCH."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_components_mismatch",
    criteria=[Criterion("pair", lambda d: {"lo": bool(np.mean(d["x"]) > 1.0)}, components=["lo", "hi"])],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["pair"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=30),
)
