"""E5-01 (deterministic): spring calibration. Claim: the stiffness fitted through the origin is 40 N/m within 4 N/m."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

EXTENSION = np.linspace(0.01, 0.10, 10)


def _stiffness_ok(d):
    x = d["x"]
    f = d["f"]
    den = float(np.sum(x * x))
    if not den > 0.0:
        return False
    k_hat = float(np.sum(x * f)) / den
    return bool(abs(k_hat - 40.0) < 4.0)


STUDY = Study(
    name="E5-01 spring calibration",
    criteria=[Criterion("stiffness_40", _stiffness_ok, tolerances={"k_tol": (4.0, 40.0)})],
    worlds={
        "plus": World(lambda rng: {"x": EXTENSION.copy(), "f": 40.0 * EXTENSION}),
        "minus": World(
            lambda rng: {"x": EXTENSION.copy(), "f": 40.0 * EXTENSION},
            derived_from="plus",
            change="spring constant 40 -> 20 N/m",
        ),
    },
    premises=[
        Premise("stiffness", lambda d, rng: {"x": d["x"], "f": 0.5 * d["f"]}, "tested", ["stiffness_40"], magnitude=(0.5, 1.0))
    ],
    controls=[Control("axes_swapped", ["stiffness_40"], transform=lambda d, rng: {"x": d["f"], "f": d["x"]})],
    deterministic=True,
)
