"""W37: Using 6 weekly indicators, a ridge regression forecasts next-week hospital admissions in future weeks with R^2 of at least 0.30."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 150, 6


def _ar(rng, n, k, rho):
    e = rng.standard_normal((n, k))
    out = np.empty((n, k))
    out[0] = e[0]
    s = np.sqrt(1.0 - rho ** 2)
    for t in range(1, n):
        out[t] = rho * out[t - 1] + s * e[t]
    return out


def _gen(rng, eff):
    lead = _ar(rng, N, 1, 0.8)[:, 0]                         # driver that the first three indicators measure
    other = _ar(rng, N, 1, 0.8)[:, 0]                        # an equally persistent driver unrelated to the indicators
    walk = _ar(rng, N, 3, 0.95)                              # three slowly drifting indicators
    meas = 0.8 * rng.standard_normal((N, 3))
    res = _ar(rng, N, 1, 0.7)[:, 0]
    ind = np.empty((N, K))
    ind[:, :3] = lead[:, None] + meas
    ind[:, 3:] = walk
    admissions_next = 300.0 + 30.0 * (eff * lead + (1.0 - eff) * other) + 25.0 * res
    return {"indicators": ind, "admissions_next": admissions_next}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: indicators (150, 6) weekly indicator values, axes (weeks, indicators), rows in time order;
    admissions_next (150,) admissions in the following week.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_weeks(d, rng):
    return {**d, "admissions_next": d["admissions_next"][rng.permutation(N)]}


STUDY = Study(
    name="W37",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="next-week admissions follow the driver that three indicators measure (coefficient 30; ideal forward R squared about 0.45) -> they follow an equally persistent driver unrelated to every indicator; the autocorrelated residual, the drifting indicators and all variances unchanged"),
    },
    controls=[Control("permute_weeks", ["C"], transform=permute_weeks)],
)
