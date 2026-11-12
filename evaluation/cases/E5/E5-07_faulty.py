"""E5-07 (stochastic): sensor drift. Claim: the least-squares drift rate of the reading exceeds 0.25 units per hour."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

HOURS = np.linspace(0.0, 10.0, 81)


def _drift_ok(d):
    t = d["t"]
    y = d["t"]
    tc = t - np.mean(t)
    den = float(np.sum(tc * tc))
    if not den > 0.0:
        return False
    slope = float(np.sum(tc * (y - np.mean(y)))) / den
    return bool(slope > 0.25)


STUDY = Study(
    name="E5-07 sensor drift rate",
    criteria=[Criterion("drift_gt_025", _drift_ok, tolerances={"rate": (0.25, 0.5)})],
    worlds={
        "plus": World(lambda rng: {"t": HOURS.copy(), "y": 0.5 * HOURS + rng.normal(0.0, 1.0, HOURS.size)}),
        "minus": World(
            lambda rng: {"t": HOURS.copy(), "y": 0.0 * HOURS + rng.normal(0.0, 1.0, HOURS.size)},
            derived_from="plus",
            change="drift rate 0.5 -> 0 per hour",
        ),
    },
    premises=[
        Premise("drift_present", lambda d, rng: {"t": d["t"], "y": d["y"] - 0.5 * d["t"]}, "tested", ["drift_gt_025"], magnitude=(0.5, 0.5))
    ],
    controls=[Control("time_reversed", ["drift_gt_025"], transform=lambda d, rng: {"t": d["t"], "y": d["y"][::-1]})],
)
