"""E2-11: Newton cooling. The measured cooling curve follows the reference solution within 0.5 degC at every sample."""
import subprocess
import sys

import numpy as np

from kapi import Control, Criterion, Premise, Study, World

T_ENV, T_START, K_COOL = 20.0, 80.0, 0.05     # degC, degC, 1/min
TIMES = np.linspace(0.0, 60.0, 20)              # min
ABS_TOL = 0.5
NOISE = 0.1


REF_SCRIPT = (
    "import math, sys\n"
    "env, start, k, *ts = map(float, sys.argv[1:])\n"
    "print(' '.join(repr(env + (start - env) * math.exp(-k * t)) for t in ts))\n"
)


def reference(t):
    args = [repr(float(v)) for v in (T_ENV, T_START, K_COOL, *t)]
    out = subprocess.run([sys.executable, "-I", "-c", REF_SCRIPT, *args],
                         capture_output=True, text=True, timeout=60, check=True)
    return np.array([float(s) for s in out.stdout.split()])


def make_world(k):
    def generate(rng):
        T = T_ENV + (T_START - T_ENV) * np.exp(-k * TIMES) + rng.normal(0.0, NOISE, TIMES.size)
        return {"t": TIMES.copy(), "T": T}
    return generate


def disconnected(rng):
    return {"t": TIMES.copy(), "T": T_ENV + rng.normal(0.0, NOISE, TIMES.size)}


def follows_reference(d):
    with np.errstate(all="ignore"):
        return bool(np.all(np.abs(d["T"] - reference(d["t"])) <= ABS_TOL))


def clock_offset(d, rng):
    return {"t": d["t"] + 2.0, "T": d["T"]}


STUDY = Study(
    name="E2-11 Newton cooling against the reference solution",
    criteria=[Criterion("follows_reference", follows_reference, tolerances={"abs": (ABS_TOL, T_START - T_ENV)})],
    worlds={
        "plus": World(make_world(K_COOL)),
        "minus": World(make_world(0.06), derived_from="plus", change="cooling constant 0.05 -> 0.06 per min"),
    },
    premises=[Premise("clocks_synchronised", clock_offset, "tested", ["follows_reference"], magnitude=(2.0, 60.0))],
    controls=[Control("thermocouple_disconnected", ["follows_reference"], world=World(disconnected))],
)
