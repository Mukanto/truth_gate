"""W47: Economic growth is lower in country-years with high public debt: mean annual real GDP growth in country-years with debt above 90% of GDP is at least 1.5 percentage points below mean growth in country-years with debt at or below 90%."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

C, Y = 20, 15


def _gen(rng, eff):
    mu = 2.5 + 1.0 * rng.standard_normal(C)                  # long-run growth of each country
    zmu = (mu - 2.5) / 1.0
    dbar = 70.0 - 15.0 * zmu + 12.0 * rng.standard_normal(C)  # slower-growing (richer) countries carry more debt, both worlds
    shock = 1.0 * rng.standard_normal(Y)                     # common yearly shock
    e = 2.5 * rng.standard_normal((C, Y))                    # idiosyncratic growth noise
    u = 12.0 * rng.standard_normal(C)
    v = 8.0 * rng.standard_normal((C, Y))
    growth = np.empty((C, Y))
    debt = np.empty((C, Y))
    prev = mu.copy()
    for t in range(Y):
        u = 0.85 * u + v[:, t]                               # persistent debt movements
        debt[:, t] = np.maximum(dbar + u - 3.0 * (prev - mu), 5.0)       # weak growth last year pushes the debt ratio up (reverse causation)
        growth[:, t] = mu + shock[t] + e[:, t] - eff * 2.2 * (debt[:, t] > 90.0)   # causal threshold effect of high debt on growth
        prev = growth[:, t]
    return {"growth": growth, "debt": debt}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: growth (20, 15) annual real GDP growth, percent, axes (countries, years); debt (20, 15) public debt as percent
    of GDP, same layout as growth.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_countries_of_debt(d, rng):
    return {**d, "debt": d["debt"][rng.permutation(C)]}


STUDY = Study(
    name="W47",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="high debt (> 90% of GDP) lowers growth by 2.2 points -> no effect of debt on growth; country growth differences correlated with country debt levels, reverse causation from last year's growth to this year's debt, and all noise unchanged"),
    },
    controls=[Control("permute_countries_of_debt", ["C"], transform=permute_countries_of_debt)],
)
