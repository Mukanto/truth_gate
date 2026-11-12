"""E2-14: Refraction. The refractive index fitted from incidence/refraction angle pairs is 1.50 within 0.01 (deterministic)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

THETA_I = np.arange(15.0, 70.0, 5.0)    # degrees
N_GLASS = 1.50
TOL_N = 0.01


def sin_deg(angle):
    return np.sin(np.radians(angle))


def bench(n2):
    def generate(rng):
        theta_t = np.degrees(np.arcsin(np.sin(np.radians(THETA_I)) / n2))
        return {"theta_i": THETA_I.copy(), "theta_t": np.round(theta_t, 1)}
    return generate


def index_matches(d):
    si, st = sin_deg(d["theta_i"]), sin_deg(d["theta_t"])
    with np.errstate(all="ignore"):
        n_hat = np.sum(si * st) / np.sum(st * st)
    return bool(abs(n_hat - N_GLASS) <= TOL_N)


def protractor_offset(d, rng):
    return {"theta_i": d["theta_i"], "theta_t": d["theta_t"] + 2.0}


def mispair(d, rng):
    return {"theta_i": d["theta_i"], "theta_t": d["theta_t"][::-1].copy()}


STUDY = Study(
    name="E2-14 refractive index from Snell's law",
    criteria=[Criterion("index_matches", index_matches, tolerances={"n": (TOL_N, N_GLASS)})],
    worlds={
        "plus": World(bench(N_GLASS)),
        "minus": World(bench(1.33), derived_from="plus", change="medium glass (n = 1.50) -> water (n = 1.33)"),
    },
    premises=[Premise("protractor_zeroed", protractor_offset, "tested", ["index_matches"], magnitude=(2.0, 90.0))],
    controls=[Control("angles_mispaired", ["index_matches"], transform=mispair)],
    deterministic=True,
)
