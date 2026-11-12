"""E2-03: Deterministic calibration. The theory line y = 2 + 3x predicts the bench data with MSE below the baseline 0.01."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

X = np.linspace(0.0, 1.0, 50)
INTERCEPT, SLOPE = 2.0, 3.0
BASELINE_MSE = 0.01


def bench(slope):
    def generate(rng):
        y = INTERCEPT + slope * X + 0.05 * np.sin(37.0 * X)
        return {"x": X.copy(), "y": y}
    return generate


def improves_on_baseline(d):
    mse = float(np.mean((d["y"] - (INTERCEPT + SLOPE * d["x"])) ** 2))
    return bool(mse < BASELINE_MSE)


def x_scale_error(d, rng):
    return {"x": 1.1 * d["x"], "y": d["y"]}


def reverse_y(d, rng):
    return {"x": d["x"], "y": d["y"][::-1].copy()}


STUDY = Study(
    name="E2-03 calibration line against a baseline",
    criteria=[Criterion("improves_on_baseline", improves_on_baseline, tolerances={"mse": (BASELINE_MSE, 1.0)})],
    worlds={
        "plus": World(bench(SLOPE)),
        "minus": World(bench(3.6), derived_from="plus", change="true slope 3.0 -> 3.6"),
    },
    premises=[Premise("x_units_correct", x_scale_error, "tested", ["improves_on_baseline"], magnitude=(0.1, 1.0))],
    controls=[Control("y_reversed", ["improves_on_baseline"], transform=reverse_y)],
    deterministic=True,
)
