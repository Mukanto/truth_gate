"""Toy: the threshold is read from a declared static file (allow_paths) -> no leak, file hashed, FALSIFIABLE."""
import os

import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

CONFIG = os.path.join(os.path.dirname(__file__), "allowed_data.txt")


def above_threshold(data):
    with open(CONFIG) as handle:
        threshold = float(handle.read())
    return bool(np.mean(data["x"]) > threshold)


STUDY = Study(
    name="toy_allowed_file",
    criteria=[Criterion("above_threshold", above_threshold)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["above_threshold"], magnitude=(2.0, 2.0))],
    controls=[Control("negate", ["above_threshold"], transform=lambda d, rng: {"x": -d["x"]})],
    allow_paths=["allowed_data.txt"],
    budget=Budget(samples=100),
)
