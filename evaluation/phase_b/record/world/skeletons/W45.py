"""W45: A dobutamine infusion in critically ill adults raises oxygen consumption in proportion to the rise in oxygen delivery: across 24 patients, the proportion of variance in the change in oxygen consumption explained by the change in oxygen delivery (R squared of a simple linear regression) is at least 0.25."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 24


def _gen(rng, eff):
    co0 = 5.2 * np.exp(0.30 * rng.standard_normal(N))
    resp = np.maximum(0.35 + 0.25 * rng.standard_normal(N), -0.2)         # fractional output response to dobutamine
    co1 = co0 * (1.0 + resp)
    hb0 = np.clip(10.0 + 1.3 * rng.standard_normal(N), 6.5, 14.0)
    hb1 = np.clip(hb0 + 0.3 * rng.standard_normal(N), 6.0, 14.5)
    sa0 = np.clip(0.95 + 0.02 * rng.standard_normal(N), 0.80, 0.995)
    sa1 = np.clip(sa0 + 0.005 * rng.standard_normal(N), 0.80, 0.995)
    co = np.column_stack([co0, co1])
    hb = np.column_stack([hb0, hb1])
    sa = np.column_stack([sa0, sa1])
    do2 = co * hb * 13.4 * sa                                             # true delivery, mL/min
    d_do2 = do2[:, 1] - do2[:, 0]
    b = 0.25
    sd_res = np.sqrt(25.0 ** 2 + (1.0 - eff) * (b * d_do2.std()) ** 2)    # same total variance of the true change in consumption
    vo2_0 = 250.0 + 60.0 * rng.standard_normal(N)
    d_vo2 = 60.0 + eff * b * (d_do2 - d_do2.mean()) + sd_res * rng.standard_normal(N)
    vo2 = np.maximum(np.column_stack([vo2_0, vo2_0 + d_vo2]), 80.0)       # true consumption
    sv = np.clip(sa - vo2 / (co * hb * 13.4), 0.25, 0.90)                 # Fick-consistent venous saturation
    co_m = co * np.exp(0.08 * rng.standard_normal((N, 2)))                # thermodilution error at each time point
    hb_m = hb + 0.25 * rng.standard_normal((N, 2))
    sa_m = np.clip(sa + 0.01 * rng.standard_normal((N, 2)), 0.5, 1.0)
    sv_m = sv + 0.02 * rng.standard_normal((N, 2))
    vo2_exp = vo2 * np.exp(0.08 * rng.standard_normal((N, 2)))            # expired-gas measurement error
    return {"cardiac_output": co_m, "hemoglobin": hb_m, "sao2": sa_m, "svo2": sv_m, "vo2_expired": vo2_exp}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys, all (24, 2) with axis 1 = [before infusion, during infusion]: cardiac_output cardiac output, L/min, by
    thermodilution; hemoglobin blood hemoglobin concentration, g/dL; sao2 arterial oxygen saturation, fraction 0-1; svo2
    mixed venous oxygen saturation, fraction 0-1; vo2_expired oxygen consumption, mL/min, from expired-gas analysis.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_vo2_expired(d, rng):
    return {**d, "vo2_expired": d["vo2_expired"][rng.permutation(N)]}


STUDY = Study(
    name="W45",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the true change in oxygen consumption follows the true change in delivery (0.25 per unit; R squared of the measured changes about 0.4) -> independent of it (same variance and the same +60 mL/min mean rise); the Fick-consistent venous saturation, the shared thermodilution errors and the independent expired-gas error unchanged"),
    },
    controls=[Control("permute_vo2_expired", ["C"], transform=permute_vo2_expired)],
)
