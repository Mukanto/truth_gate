"""E2-08: Driven oscillator at resonance. Lock-in amplitude exceeds 5 drive units and the phase lag is 90 +- 5 degrees."""
import numpy as np

from kapi import Control, Criterion, Study, World

FS, N = 1000.0, 2000
TIME = np.arange(N) / FS                # s
F0, Q = 50.0, 10.0
NOISE = 0.5
AMP_MIN = 5.0
LAG_TOL = 5.0                           # degrees


def response(f, rng):
    x = f / F0
    gain = 1.0 / np.sqrt((1.0 - x * x) ** 2 + (x / Q) ** 2)
    lag = np.arctan2(x / Q, 1.0 - x * x)
    return gain * np.sin(2.0 * np.pi * f * TIME - lag) + rng.normal(0.0, NOISE, N)


def make_world(f):
    def generate(rng):
        return {"f_drive": np.array([f]), "resp": response(f, rng)}
    return generate


def disconnected(rng):
    return {"f_drive": np.array([F0]), "resp": rng.normal(0.0, NOISE, N)}


def lock_in(d):
    w = 2.0 * np.pi * float(d["f_drive"][0]) * TIME
    a = 2.0 * np.mean(d["resp"] * np.sin(w))
    b = 2.0 * np.mean(d["resp"] * np.cos(w))
    return float(np.hypot(a, b)), float(np.degrees(np.arctan2(-b, a)))


def amplitude(d):
    return bool(lock_in(d)[0] > AMP_MIN)


def phase(d):
    return bool(abs(lock_in(d)[1] - 90.0) <= LAG_TOL)


STUDY = Study(
    name="E2-08 resonance amplitude and phase",
    criteria=[
        Criterion("amplitude", amplitude, tolerances={"amp_min": (AMP_MIN, Q)}),
        Criterion("phase", phase, tolerances={"lag_deg": (LAG_TOL, 90.0)}),
    ],
    worlds={
        "plus": World(make_world(F0)),
        "minus": World(make_world(0.5 * F0), derived_from="plus", change="drive frequency f0 -> f0 / 2"),
    },
    controls=[Control("sensor_disconnected", ["amplitude", "phase"], world=World(disconnected))],
)
