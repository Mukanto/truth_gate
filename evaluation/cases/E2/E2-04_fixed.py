"""E2-04: Simple pendulum. Measured periods agree with T = 2 pi sqrt(L / g) within 2 % (relative)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

G = 9.81
LENGTHS = np.linspace(0.2, 2.0, 8)
REL_TOL = 0.02
NOISE = 0.003


def amplitude_factor(theta0_deg):
    a, b = 1.0, float(np.cos(np.radians(theta0_deg) / 2.0))
    for _ in range(40):
        a, b = 0.5 * (a + b), float(np.sqrt(a * b))
    return 1.0 / a


SMALL = amplitude_factor(5.0)
LARGE = amplitude_factor(40.0)


def make_world(inertia_factor):
    def generate(rng):
        T = 2.0 * np.pi * np.sqrt(inertia_factor * LENGTHS / G) * SMALL
        return {"L": LENGTHS.copy(), "T": T * (1.0 + NOISE * rng.standard_normal(LENGTHS.size))}
    return generate


def period_law(d):
    with np.errstate(all="ignore"):
        T_pred = 2.0 * np.pi * np.sqrt(d["L"] / G)
        relerr = np.abs(d["T"] - T_pred) / T_pred
        return bool(np.all(relerr <= REL_TOL))


def large_amplitude(d, rng):
    out = dict(d)
    out["T"] = d["T"] * (LARGE / SMALL)
    return out


def shuffle_periods(d, rng):
    return {"L": d["L"], "T": rng.permutation(d["T"])}


STUDY = Study(
    name="E2-04 pendulum period law",
    criteria=[Criterion("period_law", period_law, tolerances={"rel": (REL_TOL, 1.0)})],
    worlds={
        "plus": World(make_world(1.0)),
        "minus": World(make_world(2.0 / 3.0), derived_from="plus", change="point mass -> uniform rod (I = m L^2 / 3)"),
    },
    premises=[Premise("small_angle", large_amplitude, "tested", ["period_law"], magnitude=(40.0, 90.0))],
    controls=[Control("periods_shuffled", ["period_law"], transform=shuffle_periods)],
)
