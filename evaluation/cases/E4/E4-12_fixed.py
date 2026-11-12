"""E4-12: Nanowire conductance. The fitted conductance matches the predicted 0.5 nS within 5 % (relative)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, Targets, World

G_PRED = 0.5e-9             # S
VOLTS = np.linspace(0.1, 1.0, 10)
NOISE = 0.01                # relative current noise
RTOL = 0.05
ALPHA = 0.05


def make_world(g):
    def generate(rng):
        return {"V": VOLTS.copy(), "I": g * VOLTS * (1.0 + NOISE * rng.standard_normal(VOLTS.size))}
    return generate


def open_circuit(rng):
    return {"V": VOLTS.copy(), "I": 1.0e-13 * rng.standard_normal(VOLTS.size)}


def conductance_matches(d):
    V, I = d["V"], d["I"]
    with np.errstate(all="ignore"):
        g_hat = np.sum(V * I) / np.sum(V * V)
    return bool(np.isclose(g_hat, G_PRED, rtol=RTOL, atol=0.0))


def series_resistance(d, rng):
    return {"V": d["V"], "I": 0.7 * d["I"]}


STUDY = Study(
    name="E4-12 nanowire conductance",
    criteria=[Criterion("conductance_matches", conductance_matches, tolerances={"rtol": (RTOL, 1.0)})],
    worlds={
        "plus": World(make_world(G_PRED)),
        "minus": World(make_world(0.6e-9), derived_from="plus", change="conductance 0.5 nS -> 0.6 nS"),
    },
    premises=[Premise("ohmic_contacts", series_resistance, "tested", ["conductance_matches"], magnitude=(0.3, 1.0))],
    controls=[Control("open_circuit", ["conductance_matches"], world=World(open_circuit))],
    targets=Targets(size=ALPHA),
)
