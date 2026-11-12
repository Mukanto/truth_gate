"""E4-13: Free-fall gravimetry. The fitted g matches the local reference value within 0.2 %."""
import json
import urllib.request

import numpy as np

from kapi import Control, Criterion, Premise, Study, Targets, World

G_LOCAL = 9.80620           # m/s^2, value of the geodetic service for this site
HEIGHTS = np.linspace(0.5, 2.0, 7)      # m
TIMING_SD = 2.0e-4          # s
REL_TOL = 0.002
ALPHA = 0.05


REFERENCE_URL = "http://127.0.0.1:8650/gravity?site=lab3"


def reference_g():
    with urllib.request.urlopen(REFERENCE_URL, timeout=5) as response:
        return float(json.loads(response.read().decode())["g"])


def make_world(g):
    def generate(rng):
        t = np.sqrt(2.0 * HEIGHTS / g) + rng.normal(0.0, TIMING_SD, HEIGHTS.size)
        return {"h": HEIGHTS.copy(), "t": t}
    return generate


def g_matches(d):
    h, t = d["h"], d["t"]
    with np.errstate(all="ignore"):
        g_hat = 2.0 * np.sum(h * t * t) / np.sum(t ** 4)
        return bool(abs(g_hat / reference_g() - 1.0) <= REL_TOL)


def timer_latency(d, rng):
    return {"h": d["h"], "t": d["t"] + 0.002}


def mispair(d, rng):
    return {"h": d["h"], "t": d["t"][::-1].copy()}


STUDY = Study(
    name="E4-13 free-fall gravimetry",
    criteria=[Criterion("g_matches", g_matches, tolerances={"rel": (REL_TOL, 1.0)})],
    worlds={
        "plus": World(make_world(G_LOCAL)),
        "minus": World(make_world(0.99 * G_LOCAL), derived_from="plus", change="effective g reduced by 1 % (guide rail tilted 8 degrees)"),
    },
    premises=[Premise("no_timer_latency", timer_latency, "tested", ["g_matches"], magnitude=(0.002, 0.5))],
    controls=[Control("heights_mispaired", ["g_matches"], transform=mispair)],
    targets=Targets(size=ALPHA),
)
