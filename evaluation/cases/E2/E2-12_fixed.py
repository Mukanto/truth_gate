"""E2-12: Thermal expansion. The fitted linear expansion coefficient of the alloy matches 12e-6 per K within the stated tolerance."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

ALPHA_PRED = 12.0e-6                 # 1/K
TOL = 0.5e-6                         # tolerance on alpha, in 1/K
L0, T_REF = 0.1, 293.0               # m, K
TEMPS = np.linspace(293.0, 393.0, 11)
NOISE = 1.0e-7                       # m


def make_world(alpha):
    def generate(rng):
        L = L0 * (1.0 + alpha * (TEMPS - T_REF)) + rng.normal(0.0, NOISE, TEMPS.size)
        return {"T": TEMPS.copy(), "L": L}
    return generate


def alpha_matches(d):
    T, L = d["T"], d["L"]
    if np.any(L <= 0.0) or np.any(T <= 0.0):
        return False                 # not a physical length / absolute temperature
    dT = T - T.mean()
    slope = np.sum(dT * (L - L.mean())) / np.sum(dT * dT)
    L_ref = L.mean() - slope * (T.mean() - T_REF)
    return bool(abs(slope / L_ref - ALPHA_PRED) <= TOL)


def gain_error(d, rng):
    L = d["L"]
    return {"T": d["T"], "L": L[0] + 1.1 * (L - L[0])}


STUDY = Study(
    name="E2-12 thermal expansion coefficient",
    criteria=[Criterion("alpha_matches", alpha_matches, tolerances={"alpha": (TOL, ALPHA_PRED)})],
    worlds={
        "plus": World(make_world(ALPHA_PRED)),
        "minus": World(make_world(11.0e-6), derived_from="plus", change="expansion coefficient 12e-6 -> 11e-6 per K"),
    },
    premises=[Premise("dilatometer_gain_calibrated", gain_error, "tested", ["alpha_matches"], magnitude=(0.1, 1.0))],
    controls=[Control("fused_silica_sample", ["alpha_matches"], world=World(make_world(0.55e-6)))],
)
