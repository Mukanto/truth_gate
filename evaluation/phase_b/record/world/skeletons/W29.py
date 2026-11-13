"""W29: In critically ill adults, oxygen consumption rises with oxygen delivery: across 40 patients, the Pearson correlation between oxygen consumption and oxygen delivery is at least 0.5."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 40


def _gen(rng, eff):
    co = 5.2 * np.exp(0.30 * rng.standard_normal(N))                    # true cardiac output, L/min
    hb = np.clip(10.0 + 1.3 * rng.standard_normal(N), 6.5, 14.0)        # g/dL
    sa = np.clip(0.95 + 0.02 * rng.standard_normal(N), 0.80, 0.995)
    do2 = co * hb * 13.4 * sa                                           # true delivery, mL/min
    ev = rng.standard_normal(N)
    b = 0.26
    sd_res = np.sqrt(45.0 ** 2 + (1.0 - eff) * (b * do2.std()) ** 2)    # same total variance of true consumption in both worlds
    vo2 = 250.0 + eff * b * (do2 - do2.mean()) + sd_res * ev            # true consumption, mL/min
    vo2 = np.maximum(vo2, 80.0)
    sv = np.clip(sa - vo2 / (co * hb * 13.4), 0.25, 0.90)               # Fick: venous saturation consistent with the true consumption
    co_m = co * np.exp(0.15 * rng.standard_normal(N))                   # thermodilution error
    hb_m = hb + 0.3 * rng.standard_normal(N)
    sa_m = np.clip(sa + 0.01 * rng.standard_normal(N), 0.5, 1.0)
    sv_m = sv + 0.02 * rng.standard_normal(N)
    vo2_exp = vo2 * np.exp(0.10 * rng.standard_normal(N))               # expired-gas measurement, independent error
    return {"cardiac_output": co_m, "hemoglobin": hb_m, "sao2": sa_m, "svo2": sv_m, "vo2_expired": vo2_exp}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: cardiac_output (40,) cardiac output, L/min, from thermodilution; hemoglobin (40,) blood hemoglobin
    concentration, g/dL; sao2 (40,) arterial oxygen saturation, fraction 0-1; svo2 (40,) mixed venous oxygen saturation,
    fraction 0-1; vo2_expired (40,) oxygen consumption, mL/min, measured by expired-gas analysis at the same time as the
    haemodynamic measurements.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_vo2_expired(d, rng):
    return {**d, "vo2_expired": d["vo2_expired"][rng.permutation(N)]}


STUDY = Study(
    name="W29",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true oxygen consumption rises with true delivery (0.26 mL/min per mL/min, correlation about 0.7) -> true consumption independent of delivery (same variance); the Fick-consistent venous saturation, the shared thermodilution error and all measurement errors unchanged"),
    },
    controls=[Control("permute_vo2_expired", ["C"], transform=permute_vo2_expired)],
)
