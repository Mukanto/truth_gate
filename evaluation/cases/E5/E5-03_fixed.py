"""E5-03 (deterministic): culture growth. Claim: the growth rate fitted from log counts is 0.5 per day within 0.1."""
import numpy as np

from kapi import Control, Criterion, Study, World

DAYS = np.linspace(0.0, 8.0, 17)
BASE = {"n0": 10.0, "r": 0.5}


def _grow(p):
    return {"t": DAYS.copy(), "n": p["n0"] * np.exp(p["r"] * DAYS)}


def _rate_ok(d):
    t = d["t"]
    n = d["n"]
    if np.any(n <= 0.0):
        return False
    y = np.log(n)
    tc = t - np.mean(t)
    den = float(np.sum(tc * tc))
    if not den > 0.0:
        return False
    r_hat = float(np.sum(tc * (y - np.mean(y)))) / den
    return bool(abs(r_hat - 0.5) < 0.1)


STUDY = Study(
    name="E5-03 culture growth rate",
    criteria=[Criterion("rate_half", _rate_ok, tolerances={"r_tol": (0.1, 0.5)})],
    worlds={
        "plus": World(lambda rng: _grow(BASE)),
        "minus": World(lambda rng: _grow({**BASE, "r": 0.05}), derived_from="plus", change="growth rate 0.5 -> 0.05 per day"),
    },
    controls=[Control("time_reversed", ["rate_half"], transform=lambda d, rng: {"t": d["t"], "n": d["n"][::-1]})],
    deterministic=True,
)
