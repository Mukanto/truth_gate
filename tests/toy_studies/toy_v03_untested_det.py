"""Toy (deterministic): everything is sound except that minus equals plus -> K2_MINUS_IDENTICAL, verdict UNTESTED."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_v03_untested_det",
    criteria=[Criterion("near_three", lambda d: bool(abs(float(d["v"][0]) - 3.0) < 0.5))],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0])}),
        "minus": World(lambda rng: {"v": np.array([3.0])}, derived_from="plus", change="none (identical)"),
    },
    premises=[Premise("offset", lambda d, rng: {"v": d["v"] + 1.0}, "tested", ["near_three"], magnitude=(1.0, 3.0))],
    controls=[Control("negate", ["near_three"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
