import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_DAMS = 14
N_PUPS = 4
SCORE_MEAN = 50.0
SD_LITTER = 5.477
SD_PUP = 8.367
EXPO_MEDIAN = 5.0
EXPO_LOG_SD = 0.6
BETA_PER_SD = 5.5
EXPO_MEAN = EXPO_MEDIAN * np.exp(EXPO_LOG_SD ** 2 / 2.0)
EXPO_SD = EXPO_MEAN * np.sqrt(np.exp(EXPO_LOG_SD ** 2) - 1.0)


def _world(rng, beta_per_sd):
    exposure = EXPO_MEDIAN * np.exp(EXPO_LOG_SD * rng.standard_normal(N_DAMS))
    litter = SD_LITTER * rng.standard_normal(N_DAMS)
    pup = SD_PUP * rng.standard_normal((N_DAMS, N_PUPS))
    signal = beta_per_sd * (exposure - EXPO_MEAN) / EXPO_SD
    outcome = SCORE_MEAN + signal[:, None] + litter[:, None] + pup
    return {"exposure": exposure.astype(float), "outcome": outcome.astype(float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, BETA_PER_SD)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: exposure (14,) float, exposure level of each dam;
    outcome (14, 4) float, performance score at weaning of each of the 4 pups of each dam.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    x = np.array(d["exposure"], dtype=float)
    p = rng.permutation(x.size)
    if np.array_equal(p, np.arange(x.size)):
        p = np.roll(p, 1)
    return {"exposure": x[p], "outcome": np.array(d["outcome"], dtype=float)}


STUDY = Study(
    name="D-016",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the slope of litter-mean score on exposure is set to 0 (litter offsets, pup noise and exposure distribution unchanged)"),
    },
    controls=[Control("D-016", ["C"], transform=lambda d, rng: _break(d, rng))],
)
