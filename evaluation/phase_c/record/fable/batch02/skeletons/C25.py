"""C25: Over a ten-year record, monthly hospital admissions rose after accounting for catchment population: in a linear regression of monthly admissions on time and catchment population, the coefficient of time is positive and significant at the one-sided 5% level (t test)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _ar1(rng, n, phi, sd):
    # stationary first-order autoregressive series with marginal standard deviation sd
    shocks = rng.normal(0.0, sd * np.sqrt(1.0 - phi * phi), n)
    out = np.empty(n)
    out[0] = rng.normal(0.0, sd)
    for i in range(1, n):
        out[i] = phi * out[i - 1] + shocks[i]
    return out


def _world(rng, trend_per_year):
    months = 120
    time_years = np.arange(months) / 12.0
    # catchment population (thousands): slow growth plus persistent deviations (boundary and estimate revisions)
    population = 250.0 + 1.5 * time_years + _ar1(rng, months, 0.9, 4.0)
    season = 80.0 * np.cos(2.0 * np.pi * np.arange(months) / 12.0)      # winter peak
    waves = _ar1(rng, months, 0.6, 55.0)                                # persistent excess (epidemic waves)
    month_noise = rng.normal(0.0, 20.0, months)
    admissions = 8.0 * population + trend_per_year * time_years + season + waves + month_noise
    admissions = np.round(admissions)
    return {
        "admissions": admissions.astype(np.float64),
        "population": population.astype(np.float64),
        "time_years": time_years.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 20.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: admissions (120,) float, number of hospital admissions in each month; population (120,) float,
    catchment population in each month, in thousands; time_years (120,) float, time of each month in years since
    the start of the record. The three arrays are aligned by month, in time order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C25",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="time trend of admissions at given population set to 0 (was +20 admissions per month per year); population growth, the admission rate per head, seasonality and autocorrelated month-to-month variation kept"),
    },
    controls=[
        Control("permute_time_across_months", ["C"], transform=lambda d, rng: {**d, "time_years": _permute_changed(d["time_years"], rng)}),
        Control("reverse_time", ["C"], transform=lambda d, rng: {**d, "time_years": d["time_years"][::-1].copy()}),
    ],
)
