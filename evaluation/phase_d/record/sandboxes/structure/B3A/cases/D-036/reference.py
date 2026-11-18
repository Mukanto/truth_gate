"""D-036: Across patients, cardiac output explains at least 25% of the variance in systemic vascular resistance (R-squared of at least 0.25)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 100
CO_MEDIAN = 4.9
CO_TRUE_SD = 0.218
CO_ERR_SD = 0.15
P_MEDIAN = 85.0
P_NOISE_SD = 0.10
CVP_SHAPE = 6.0
CVP_SCALE = 1.2


def _gen(rng, b):
    lco = np.log(CO_MEDIAN) + CO_TRUE_SD * rng.standard_normal(N_PAT)
    co_true = np.exp(lco)
    log_p = np.log(P_MEDIAN) + b * (lco - np.log(CO_MEDIAN)) + P_NOISE_SD * rng.standard_normal(N_PAT)
    perfusion = np.exp(log_p)
    cvp = rng.gamma(CVP_SHAPE, CVP_SCALE, N_PAT)
    mean_ap = perfusion + cvp
    co_td = co_true * np.exp(CO_ERR_SD * rng.standard_normal(N_PAT))
    co_fick = co_true * np.exp(CO_ERR_SD * rng.standard_normal(N_PAT))
    return {
        "mean_arterial_pressure": np.asarray(mean_ap, dtype=float),
        "central_venous_pressure": np.asarray(cvp, dtype=float),
        "co_thermodilution": np.asarray(co_td, dtype=float),
        "co_fick": np.asarray(co_fick, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.35)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def criterion(d):
    """Data keys: mean_arterial_pressure (100,) float, mmHg;
    central_venous_pressure (100,) float, mmHg;
    co_thermodilution (100,) float, cardiac output by thermodilution in L/min;
    co_fick (100,) float, cardiac output by the Fick method from expired-gas oxygen uptake in L/min.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_co_fick(d, rng):
    out = {k: np.asarray(v, dtype=float) for k, v in d.items()}
    perm = rng.permutation(out["co_fick"].shape[0])
    out["co_fick"] = out["co_fick"][perm]
    return out


STUDY = Study(
    name="D-036",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true systemic vascular resistance made independent of true cardiac output: elasticity of perfusion pressure to true cardiac output set from 0.35 to 1.0"),
    },
    controls=[Control("permute_co_fick", ["C"], transform=permute_co_fick)],
)
