"""E2-09: Dose-response. The response increases with dose: OLS slope above half the predicted 0.5 per mg/kg."""
import numpy as np

from kapi import Control, Criterion, Study, World

DOSES = np.repeat(np.linspace(0.0, 4.0, 5), 12)    # mg/kg, 12 subjects per dose
BASELINE = 1.0
PRED_SLOPE = 0.5
HALF = 0.5


def make_world(slope):
    def generate(rng):
        return {"dose": DOSES.copy(), "y": BASELINE + slope * DOSES + rng.normal(0.0, 1.0, DOSES.size)}
    return generate


def dose_response(d):
    x = d["dose"] - d["dose"].mean()
    with np.errstate(all="ignore"):
        slope = np.sum(x * (d["y"] - d["y"].mean())) / np.sum(x * x)
    return bool(slope > HALF * PRED_SLOPE)


STUDY = Study(
    name="E2-09 dose-response",
    criteria=[Criterion("dose_response", dose_response, tolerances={"half_effect": (HALF, 1.0)})],
    worlds={
        "plus": World(make_world(PRED_SLOPE)),
        "minus": World(make_world(0.0), derived_from="plus", change="dose slope 0.5 -> 0"),
    },
    controls=[Control("vehicle_arm", ["dose_response"], world=World(make_world(0.0)))],
    relational=[("dose", "y")],
)
