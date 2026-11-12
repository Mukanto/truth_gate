"""E5-17 (deterministic): radioactive decay. Claim: the half-life fitted from log2 activity is 5.0 h within 0.25 h."""
import numpy as np

from kapi import Control, Criterion, Study, World

HOURS = np.linspace(0.0, 12.0, 13)
A0 = 1000.0


def _activity(half_life_h):
    return {"t": HOURS.copy(), "activity": A0 * 2.0 ** (-HOURS / half_life_h)}


def _half_life_ok(d):
    t = d["t"]
    a = d["activity"]
    if np.any(a <= 0.0):
        return False
    y = np.log2(a)
    tc = t - np.mean(t)
    den = float(np.sum(tc * tc))
    if not den > 0.0:
        return False
    slope = float(np.sum(tc * (y - np.mean(y)))) / den
    if not slope < 0.0:
        return False
    return bool(abs(-1.0 / slope - 5.0) < 0.25)


STUDY = Study(
    name="E5-17 half-life",
    criteria=[Criterion("half_life_5h", _half_life_ok, tolerances={"hl_tol": (0.25, 5.0)})],
    worlds={
        "plus": World(lambda rng: _activity(5.0)),
        "minus": World(lambda rng: _activity(5.0 - 2.5), derived_from="plus", change="half-life 5.0 -> 2.5 h"),
    },
    controls=[Control("time_reversed", ["half_life_5h"], transform=lambda d, rng: {"t": d["t"], "activity": d["activity"][::-1]})],
    deterministic=True,
)
