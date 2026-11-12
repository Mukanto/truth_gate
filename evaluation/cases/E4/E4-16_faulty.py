"""E4-16: Motion sensors (deterministic). The central-difference derivative of the measured position matches the measured velocity within 1 % (relative RMS)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

DT = 0.005                  # s
TIME = np.arange(0.0, 2.0, DT)
OMEGA = 2.0 * np.pi         # rad/s
REL_TOL = 0.01


def bench(velocity_gain):
    def generate(rng):
        return {"x": np.sin(OMEGA * TIME), "v": velocity_gain * OMEGA * np.cos(OMEGA * TIME)}
    return generate


def derivative_matches(d):
    x, v = d["x"], d["v"]
    dxdt = (x[2:] - x[:-2]) / (2.0 * DT)
    v_mid = v[:-2]
    with np.errstate(all="ignore"):
        err = np.sqrt(np.mean((dxdt - v_mid) ** 2)) / np.sqrt(np.mean(v_mid ** 2))
    return bool(err <= REL_TOL)


def clock_skew(d, rng):
    return {"x": d["x"], "v": np.roll(d["v"], 2)}


def flip_velocity_sign(d, rng):
    return {"x": d["x"], "v": -d["v"]}


STUDY = Study(
    name="E4-16 position and velocity sensors",
    criteria=[Criterion("derivative_matches", derivative_matches, tolerances={"rel": (REL_TOL, 1.0)})],
    worlds={
        "plus": World(bench(1.0)),
        "minus": World(bench(1.05), derived_from="plus", change="velocity sensor gain 1.00 -> 1.05"),
    },
    premises=[Premise("shared_time_base", clock_skew, "tested", ["derivative_matches"], magnitude=(2.0, 400.0))],
    controls=[Control("velocity_polarity_reversed", ["derivative_matches"], transform=flip_velocity_sign)],
    deterministic=True,
)
