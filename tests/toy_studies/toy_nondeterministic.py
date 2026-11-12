"""Toy: a deterministic-mode study whose criterion keeps hidden state -> NONDETERMINISTIC."""
import numpy as np

from kapi import Control, Criterion, Study, World

_CALLS = {"n": 0}


def flipping(data):
    _CALLS["n"] += 1
    return _CALLS["n"] % 2 == 0


STUDY = Study(
    name="toy_nondeterministic",
    criteria=[Criterion("flips", flipping)],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0])}),
        "minus": World(lambda rng: {"v": np.array([-3.0])}, derived_from="plus", change="sign flipped"),
    },
    controls=[Control("negate", ["flips"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
)
