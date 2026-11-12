"""Toy: the criterion lists a directory but swallows the error -> K6_LEAK_ATTEMPT is still raised."""
import os

import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

HERE = os.path.dirname(__file__)


def lists_directory(data):
    try:
        os.listdir(HERE)
    except Exception:
        pass
    return bool(np.mean(data["x"]) > 1.0)


STUDY = Study(
    name="toy_leak_listdir",
    criteria=[Criterion("lists_directory", lists_directory)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["lists_directory"], magnitude=(2.0, 2.0))],
    controls=[Control("negate", ["lists_directory"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
