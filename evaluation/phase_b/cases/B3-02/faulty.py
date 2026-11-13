"""W26: In critically ill adults, systemic vascular resistance falls as cardiac output rises: across 100 patients, the Spearman rank correlation between systemic vascular resistance and cardiac output is at most -0.4."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 100


def _gen(rng, rho):
    zco = rng.standard_normal(N)
    e = rng.standard_normal(N)
    co = 5.0 * np.exp(0.28 * zco)                                      # true cardiac output, L/min
    svr = 1100.0 * np.exp(0.25 * (rho * zco + np.sqrt(1.0 - rho ** 2) * e))   # true resistance, dyn s/cm5
    cvp_t = np.maximum(10.0 + 3.5 * rng.standard_normal(N), 1.0)
    map_t = cvp_t + svr * co / 80.0                                    # pressure follows from flow and resistance
    co_th = co * np.exp(0.18 * rng.standard_normal(N))                 # thermodilution, independent error
    co_do = co * np.exp(0.15 * rng.standard_normal(N))                 # Doppler, independent error
    mapp = map_t + 2.0 * rng.standard_normal(N)
    cvp = cvp_t + 1.0 * rng.standard_normal(N)
    return {"map": mapp, "cvp": cvp, "co_thermodilution": co_th, "co_doppler": co_do}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, -0.85)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: map (100,) mean arterial pressure, mmHg; cvp (100,) central venous pressure, mmHg; co_thermodilution (100,)
    cardiac output, L/min, by pulmonary-artery thermodilution; co_doppler (100,) cardiac output, L/min, by
    echocardiographic Doppler measured at the same time by a separate operator.
    Holds when the claim is supported by the data. Written by someone else."""
    def rank(x):
        u, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        return (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    mapp = np.asarray(d["map"], dtype=float)
    cvp = np.asarray(d["cvp"], dtype=float)
    co_th = np.asarray(d["co_thermodilution"], dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        svr = 80.0 * (mapp - cvp) / co_th            # systemic vascular resistance, dyn s/cm5, from thermodilution output
    co = co_th                                       # the same thermodilution output that enters the resistance
    if not (np.all(np.isfinite(svr)) and np.all(np.isfinite(co))):
        return None
    if np.std(svr) == 0 or np.std(co) == 0:
        return None
    rho = np.corrcoef(rank(svr), rank(co))[0, 1]
    return bool(rho <= -0.4)


def permute_resistance(d, rng):
    # break the resistance-output relation: give each patient the resistance of another patient, rebuild MAP
    co_m = np.sqrt(d["co_thermodilution"] * d["co_doppler"])
    svr = 80.0 * (d["map"] - d["cvp"]) / d["co_thermodilution"]
    new_map = d["cvp"] + svr[rng.permutation(N)] * co_m / 80.0
    return {**d, "map": new_map}


STUDY = Study(
    name="W26",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true correlation between log resistance and log cardiac output -0.85 -> 0 (MAP then rises with output); measurement errors of the two output methods (independent, 18% and 15%), the shared thermodilution value inside any computed resistance, and all spreads unchanged"),
    },
    controls=[Control("permute_resistance", ["C"], transform=permute_resistance)],
)
