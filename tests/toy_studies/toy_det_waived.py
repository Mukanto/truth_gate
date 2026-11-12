"""Toy (deterministic): no control but a waiver -> K4_WAIVED -> WEAK in deterministic mode."""
import numpy as np

from kapi import Criterion, Study, World

STUDY = Study(
    name="toy_det_waived",
    criteria=[
        Criterion(
            "near_three",
            lambda d: bool(abs(float(d["v"][0]) - 3.0) < 0.5),
            control_waiver="the arithmetic has no meaningful negative control",
        )
    ],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0])}),
        "minus": World(lambda rng: {"v": np.array([-3.0])}, derived_from="plus", change="sign flipped"),
    },
    deterministic=True,
)
