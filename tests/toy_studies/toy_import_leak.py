"""Toy: reads a file outside the allow-list at import time -> the study fails to load (UNDEFINED)."""
import os

import numpy as np

from kapi import Budget, Control, Criterion, Study, World

with open(os.path.join(os.path.dirname(__file__), "leak_target.txt")) as _handle:
    THRESHOLD = len(_handle.read())

STUDY = Study(
    name="toy_import_leak",
    criteria=[Criterion("mean_gt", lambda d: bool(np.mean(d["x"]) > THRESHOLD))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["mean_gt"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=30),
)
