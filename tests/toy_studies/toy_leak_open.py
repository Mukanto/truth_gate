"""Toy: the criterion opens a file outside the allow-list -> K6_LEAK_ATTEMPT, the open is blocked."""
import os

import numpy as np

from kapi import Budget, Control, Criterion, Study, World

TARGET = os.path.join(os.path.dirname(__file__), "leak_target.txt")


def reads_file(data):
    with open(TARGET) as handle:
        handle.read()
    return bool(np.mean(data["x"]) > 1.0)


STUDY = Study(
    name="toy_leak_open",
    criteria=[Criterion("reads_file", reads_file)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["reads_file"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=30),
)
