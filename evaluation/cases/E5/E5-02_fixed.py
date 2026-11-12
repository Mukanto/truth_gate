"""E5-02 (deterministic): Arrhenius kinetics. Claim: the activation energy fitted from ln k against 1/T is 80 kJ/mol within 8 kJ/mol."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

R_GAS = 8.314
EA_REF = 80000.0
TEMP = np.linspace(300.0, 400.0, 11)


def _rates(ea):
    return 1.0e7 * np.exp(-ea / (R_GAS * TEMP))


def _ea_ok(d):
    t = d["T"]
    k = d["k"]
    if np.any(t <= 0.0) or np.any(k <= 0.0):
        return False
    u = 1.0 / t
    y = np.log(k)
    uc = u - np.mean(u)
    den = float(np.sum(uc * uc))
    if not den > 0.0:
        return False
    slope = float(np.sum(uc * (y - np.mean(y)))) / den
    return bool(abs(-slope * R_GAS - EA_REF) < 8000.0)


STUDY = Study(
    name="E5-02 Arrhenius activation energy",
    criteria=[Criterion("ea_80k", _ea_ok, tolerances={"ea_tol": (8000.0, 80000.0)})],
    worlds={
        "plus": World(lambda rng: {"T": TEMP.copy(), "k": _rates(80000.0)}),
        "minus": World(
            lambda rng: {"T": TEMP.copy(), "k": _rates(40000.0)},
            derived_from="plus",
            change="activation energy 80 -> 40 kJ/mol",
        ),
    },
    premises=[
        Premise("arrhenius_slope", lambda d, rng: {"T": d["T"], "k": np.sqrt(d["k"])}, "tested", ["ea_80k"], magnitude=(0.5, 1.0))
    ],
    controls=[Control("rates_reversed", ["ea_80k"], transform=lambda d, rng: {"T": d["T"], "k": d["k"][::-1]})],
    deterministic=True,
)
