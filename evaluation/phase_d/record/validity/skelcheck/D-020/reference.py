"""D-020: Heart weight accounts for at least 10% of the variance in liver weight beyond what body mass accounts for: the increase in R-squared when heart weight is added to a regression of liver weight on body mass is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_MICE = 1500
MASS_MEDIAN = 28.0
HEART_MEDIAN = 0.14
LIVER_MEDIAN = 1.5
SD_MASS = 0.12
SD_HEART = 0.15
SD_LIVER = 0.18
WEIGH_ERR = 0.02
HEART_ON_MASS = 0.6
LIVER_ON_MASS = 0.8
S_HEART_RES2 = SD_HEART ** 2 - (HEART_ON_MASS * SD_MASS) ** 2 - WEIGH_ERR ** 2


def _gen(rng, c_heart):
    lm = SD_MASS * rng.standard_normal(N_MICE)
    heart_res = np.sqrt(S_HEART_RES2) * rng.standard_normal(N_MICE)
    lh = HEART_ON_MASS * lm + heart_res
    s_e2 = SD_LIVER ** 2 - (LIVER_ON_MASS * SD_MASS) ** 2 - c_heart ** 2 * S_HEART_RES2 - WEIGH_ERR ** 2
    ll = LIVER_ON_MASS * lm + c_heart * heart_res + np.sqrt(s_e2) * rng.standard_normal(N_MICE)
    mass = MASS_MEDIAN * np.exp(lm)
    heart = HEART_MEDIAN * np.exp(lh + WEIGH_ERR * rng.standard_normal(N_MICE))
    liver = LIVER_MEDIAN * np.exp(ll + WEIGH_ERR * rng.standard_normal(N_MICE))
    return {
        "liver_weight": np.asarray(liver, dtype=float),
        "heart_weight": np.asarray(heart, dtype=float),
        "body_mass": np.asarray(mass, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.6)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: liver_weight (1500,) float, liver weight in g;
    heart_weight (1500,) float, heart weight in g;
    body_mass (1500,) float, body mass in g.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_heart_within_mass(d, rng):
    m = np.asarray(d["body_mass"], dtype=float)
    h = np.asarray(d["heart_weight"], dtype=float)
    order = np.argsort(m, kind="stable")
    out = h.copy()
    block = 100
    for start in range(0, m.shape[0], block):
        idx = order[start:start + block]
        out[idx] = h[idx[rng.permutation(idx.shape[0])]]
    return {"liver_weight": np.asarray(d["liver_weight"], dtype=float), "heart_weight": out, "body_mass": m}


STUDY = Study(
    name="D-020",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="dependence of log liver weight on the mass-independent part of log heart weight set from 0.6 to 0 (liver weight variance kept)"),
    },
    controls=[Control("permute_heart_within_mass", ["C"], transform=permute_heart_within_mass)],
)
