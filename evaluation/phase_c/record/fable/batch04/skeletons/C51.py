"""C51: A regression on the 8 weekly drivers explains at least 30% of the variance of weekly demand in later weeks (R-squared of at least 0.30)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_WEEKS = 400
N_DRIVERS = 8
# Week-to-week autocorrelation of the process behind each driver (5 weather anomalies, 3 calendar drivers).
DRIVER_RHO = np.array([0.6, 0.5, 0.4, 0.3, 0.5, 0.8, 0.0, 0.0])
# Effect of each driver on demand, in demand units per driver unit.
BETA = np.array([9.0, -1.2, 14.0, -3.0, 0.0, -45.0, -70.0, 22.0])
BASE_DEMAND = 1000.0
NOISE_RHO = 0.5          # autocorrelation of the demand not explained by the drivers
NOISE_SD = 75.0


def _ar1(rng, rho, shape):
    shocks = rng.normal(size=shape) * np.sqrt(1.0 - rho ** 2)
    out = np.empty(shape)
    out[0] = rng.normal(size=shape[1:])
    for t in range(1, shape[0]):
        out[t] = rho * out[t - 1] + shocks[t]
    return out


def _drivers(rng):
    z = _ar1(rng, DRIVER_RHO, (N_WEEKS, N_DRIVERS))
    z[:, 2] = 0.6 * z[:, 0] + 0.8 * z[:, 2]            # sunshine goes with temperature
    out = np.empty((N_WEEKS, N_DRIVERS))
    out[:, 0] = 4.0 * z[:, 0]                           # temperature anomaly, deg C
    out[:, 1] = 12.0 * np.exp(0.7 * z[:, 1])            # rainfall, mm
    out[:, 2] = 3.0 * z[:, 2]                           # sunshine anomaly, hours per day
    out[:, 3] = 15.0 + 5.0 * z[:, 3]                    # wind speed, km/h
    out[:, 4] = 70.0 + 10.0 * z[:, 4]                   # relative humidity, percent
    out[:, 5] = z[:, 5] > 0.9                           # school holiday week (0/1)
    out[:, 6] = z[:, 6] > 1.3                           # public holiday in the week (0/1)
    out[:, 7] = z[:, 7] > 0.7                           # month-end week (0/1)
    return out


def _generate(rng, demand_follows_drivers):
    drivers = _drivers(rng)
    other_drivers = _drivers(rng)
    noise = NOISE_SD * _ar1(rng, NOISE_RHO, (N_WEEKS,))
    source = drivers if demand_follows_drivers else other_drivers
    demand = BASE_DEMAND + source @ BETA + noise
    return {"drivers": drivers, "demand": demand}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def shift_drivers(d, rng):
    lag = int(rng.integers(52, d["drivers"].shape[0] - 52))
    return {**d, "drivers": np.roll(d["drivers"], lag, axis=0)}


def criterion(d):
    """Data keys: drivers, float array of shape (400, 8) = (weeks, drivers): 8 weather and calendar drivers of each
    week, weeks in chronological order; demand, float array of shape (400,) = (weeks,): demand observed in that week.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C51",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="demand no longer depends on the drivers of its own week (it follows an independent realisation of the same driver process): the drivers carry no predictive information about demand; the distributions and autocorrelation of drivers and of demand are unchanged"),
    },
    controls=[Control("circular_shift_of_drivers_by_52_or_more_weeks", ["C"], transform=shift_drivers)],
)
