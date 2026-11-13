"""Spec 0.7 fixture (deterministic): negative values are invalid data, so the criterion abstains on them.  The noise
probe has 30 N(0, 1) values per draw, so every one of its three draws abstains (combined outcome UNDEFINED).
``ABSTAIN`` as in abs_minus.py."""
import numpy as np

from truth_gate import Control, Criterion, Study, World

ABSTAIN = None


def high_mean(d):
    x = d["v"]
    if np.any(x < 0):
        return ABSTAIN
    return bool(np.mean(x) > 2.0)


STUDY = Study(
    name="spec07_det_abs_probes",
    criteria=[Criterion("high_mean", high_mean)],
    worlds={
        "plus": World(lambda rng: {"v": np.full(30, 3.0)}),
        "minus": World(lambda rng: {"v": np.full(30, 1.0)}, derived_from="plus", change="level 3 -> 1"),
    },
    controls=[Control("shrink", ["high_mean"], transform=lambda d, rng: {"v": d["v"] * 0.1})],
    deterministic=True,
)
