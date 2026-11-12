"""Toy: reads a file listed in allow_paths, but at import time -> still fails to load
(allow_paths are only added to the allow-list after the study object exists)."""
import os

import numpy as np

from kapi import Budget, Control, Criterion, Study, World

with open(os.path.join(os.path.dirname(__file__), "allowed_data.txt")) as _handle:
    THRESHOLD = float(_handle.read())

STUDY = Study(
    name="toy_import_allowed_file",
    criteria=[Criterion("mean_gt", lambda d: bool(np.mean(d["x"]) > THRESHOLD))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["mean_gt"], transform=lambda d, rng: {"x": -d["x"]})],
    allow_paths=["allowed_data.txt"],
    budget=Budget(samples=30),
)
