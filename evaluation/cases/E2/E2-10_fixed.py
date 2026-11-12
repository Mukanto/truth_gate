"""E2-10: Gamma counting. Efficiency-corrected count rates reproduce the certified source activity (1000 Bq) within 5 %."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

ACTIVITY = 1000.0              # Bq, certificate value
NOMINAL_EFF = 0.42             # full-energy efficiency at this geometry
LIVE = np.full(5, 10.0)        # s, live time of each run
BACKGROUND = 5.0               # counts per second
REL_TOL = 0.05


def efficiency():
    return NOMINAL_EFF


def make_world(activity):
    def generate(rng):
        return {"counts": rng.poisson(activity * NOMINAL_EFF * LIVE).astype(float), "live": LIVE.copy()}
    return generate


def background_only(rng):
    return {"counts": rng.poisson(BACKGROUND * LIVE).astype(float), "live": LIVE.copy()}


def activity_matches(d):
    with np.errstate(all="ignore"):
        activity = np.mean(d["counts"] / d["live"]) / efficiency()
        return bool(abs(activity / ACTIVITY - 1.0) <= REL_TOL)


def dead_time_loss(d, rng):
    return {"counts": rng.binomial(d["counts"].astype(np.int64), 0.9).astype(float), "live": d["live"]}


STUDY = Study(
    name="E2-10 source activity from gamma counting",
    criteria=[Criterion("activity_matches", activity_matches, tolerances={"rel": (REL_TOL, 1.0)})],
    worlds={
        "plus": World(make_world(ACTIVITY)),
        "minus": World(make_world(900.0), derived_from="plus", change="source activity 1000 Bq -> 900 Bq"),
    },
    premises=[Premise("dead_time_negligible", dead_time_loss, "tested", ["activity_matches"], magnitude=(0.1, 1.0))],
    controls=[Control("source_removed", ["activity_matches"], world=World(background_only))],
)
