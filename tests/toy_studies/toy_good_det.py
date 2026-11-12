"""Toy: deterministic arithmetic, |v - 3| < 0.5. Every check passes -> FALSIFIABLE (deterministic)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_good_det",
    criteria=[Criterion("near_three", lambda d: bool(abs(float(d["v"][0]) - 3.0) < 0.5), tolerances={"tol": (0.5, 3.0)})],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0])}),
        "minus": World(lambda rng: {"v": np.array([-3.0])}, derived_from="plus", change="sign of v flipped"),
        "null": World(lambda rng: {"v": np.array([0.0])}),
    },
    premises=[Premise("offset", lambda d, rng: {"v": d["v"] + 1.0}, "tested", ["near_three"], magnitude=(1.0, 3.0))],
    controls=[Control("negate", ["near_three"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
