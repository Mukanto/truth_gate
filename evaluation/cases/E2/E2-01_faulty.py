"""E2-01: Arrhenius kinetics. Measured rate constants agree with k = A exp(-T_A / T) within 5 % (relative)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

A_PRE = 1.0e7                  # 1/s, pre-exponential factor
T_ACT = 5000.0                 # K, activation temperature E_a / R
TEMPS = np.linspace(300.0, 400.0, 12)
REL_TOL = 0.05
NOISE = 0.01                   # relative measurement noise


def k_model(T):
    return A_PRE * np.exp(-T_ACT / T)


def make_world(t_act):
    def generate(rng):
        k = A_PRE * np.exp(-t_act / TEMPS) * (1.0 + NOISE * rng.standard_normal(TEMPS.size))
        return {"T": TEMPS.copy(), "k": k}
    return generate


def rates_agree(d):
    with np.errstate(all="ignore"):
        relerr = np.abs(d["k"] - k_model(d["T"])) / np.abs(d["k"])
        return not bool(np.any(relerr > REL_TOL))


def thermometer_offset(d, rng):
    return {"T": d["T"] + 10.0, "k": d["k"]}


def shuffle_rates(d, rng):
    return {"T": d["T"], "k": rng.permutation(d["k"])}


STUDY = Study(
    name="E2-01 Arrhenius rate constants",
    criteria=[Criterion("rates_agree", rates_agree, tolerances={"rel": (REL_TOL, 1.0)})],
    worlds={
        "plus": World(make_world(T_ACT)),
        "minus": World(make_world(5050.0), derived_from="plus", change="activation temperature 5000 K -> 5050 K"),
    },
    premises=[Premise("thermometer_calibrated", thermometer_offset, "tested", ["rates_agree"], magnitude=(10.0, 350.0))],
    controls=[Control("rates_shuffled", ["rates_agree"], transform=shuffle_rates)],
)
