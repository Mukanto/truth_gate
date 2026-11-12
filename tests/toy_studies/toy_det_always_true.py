"""Toy (deterministic): the criterion is always True -> K2_FAILS_UNREACHABLE, K2_NO_SEPARATION, probes hold."""
import numpy as np

from kapi import Control, Criterion, Study, World

STUDY = Study(
    name="toy_det_always_true",
    criteria=[Criterion("always", lambda d: True)],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0])}),
        "minus": World(lambda rng: {"v": np.array([-3.0])}, derived_from="plus", change="sign flipped"),
    },
    controls=[Control("negate", ["always"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
