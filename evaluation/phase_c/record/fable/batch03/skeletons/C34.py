"""C34: A classifier built from the 10 daily indicators predicts whether the series rises over the following day with an accuracy of at least 0.58 on later days."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_DAYS = 500
N_IND = 10
BURN_IN = 60
RHO = np.linspace(0.2, 0.9, N_IND)     # day-to-day persistence of each indicator
COMMON = 0.4                           # weight of a shared market-wide factor in every indicator
N_INFORMATIVE = 3
SLOPE = 1.0                            # log-odds of a rise per SD of the predictive score
DRIFT = 0.12                           # log-odds of a rise at a neutral score (rises on about 53% of days)


def _indicator_paths(rng):
    """Two independent copies of the indicator process, shape (2, days, indicators)."""
    steps = BURN_IN + N_DAYS
    white = rng.normal(0.0, 1.0, (steps, 2, N_IND))
    shared = rng.normal(0.0, 1.0, (steps, 2, 1))
    innov = np.sqrt(1.0 - RHO ** 2) * (np.sqrt(1.0 - COMMON ** 2) * white + COMMON * shared)
    x = np.empty((steps, 2, N_IND))
    x[0] = innov[0]
    for k in range(1, steps):
        x[k] = RHO * x[k - 1] + innov[k]
    return np.transpose(x[BURN_IN:], (1, 0, 2))


def _series(rng, linked):
    paths = _indicator_paths(rng)
    informative = rng.choice(N_IND, N_INFORMATIVE, replace=False)
    weights = np.zeros(N_IND)
    weights[informative] = rng.choice(np.array([-1.0, 1.0]), N_INFORMATIVE) * rng.uniform(0.6, 1.0, N_INFORMATIVE)
    source = paths[0] if linked else paths[1]
    score = source @ weights
    score = (score - score.mean()) / score.std()
    p_rise = 1.0 / (1.0 + np.exp(-(DRIFT + SLOPE * score)))
    rises = rng.random(N_DAYS) < p_rise
    scale = np.linspace(0.5, 3.0, N_IND)
    indicators = paths[0] * scale[None, :]
    return {"indicators": indicators.astype(np.float64), "rises": rises}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _series(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _series(rng, False)


def _shift_rises(d, rng):
    lag = int(rng.integers(100, 401))
    return {**d, "rises": np.roll(d["rises"], lag)}


def criterion(d):
    """Data keys: indicators, float (500, 10) = (days, indicators), 10 indicators observed on each day, days in
    chronological order; rises, bool (500,), True when the series rises over the day that follows.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C34",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the indicators carry no information about the next day's rise: rises is driven by an independent copy of the indicator process (same rate of rises, same serial dependence)"),
    },
    controls=[Control("shift_rises_in_time", ["C"], transform=_shift_rises)],
)
