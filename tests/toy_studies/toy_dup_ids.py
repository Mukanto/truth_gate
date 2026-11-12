"""Toy: two criteria share an id -> StudyError at construction -> study verdict UNDEFINED."""
import numpy as np

from kapi import Criterion, Study, World

STUDY = Study(
    name="toy_dup_ids",
    criteria=[
        Criterion("same", lambda d: bool(np.mean(d["x"]) > 1.0)),
        Criterion("same", lambda d: bool(np.mean(d["x"]) > 2.0)),
    ],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 10)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 10)}),
    },
)
