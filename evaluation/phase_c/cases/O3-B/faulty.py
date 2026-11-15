"""C14: Across the advanced economies in the post-war period, average real GDP growth in country-years with a public debt ratio above 90 percent of GDP is at least 2 percentage points lower than average real GDP growth in country-years with a debt ratio of 90 percent or below."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _ar1(innov, rho):
    out = np.empty_like(innov)
    out[:, 0] = innov[:, 0]
    scale = np.sqrt(1.0 - rho * rho)
    for t in range(1, innov.shape[1]):
        out[:, t] = rho * out[:, t - 1] + scale * innov[:, t]
    return out


def _gen(rng, drag):
    c, y = 20, 64
    level = rng.normal(55.0, 22.0, (c, 1))                               # country's typical debt ratio
    debt = np.maximum(level + 18.0 * _ar1(rng.normal(0.0, 1.0, (c, y)), 0.93), 5.0)   # slow debt swings
    country = rng.normal(0.0, 0.5, (c, 1))                               # country's long-run growth
    cycle = 1.2 * _ar1(rng.normal(0.0, 1.0, (1, y)), 0.4)                # world business cycle
    growth = 3.0 + country + cycle + rng.normal(0.0, 2.0, (c, y)) - drag * (debt > 90.0)
    return {"growth": growth, "debt_ratio": debt}


def plus(rng):
    """The claim is true: growth is 3.2 percentage points lower in country-years with debt above 90 percent."""
    return _gen(rng, 3.2)


def minus(rng):
    """The claim is false: growth does not depend on the debt ratio; debt and growth dynamics as in plus."""
    return _gen(rng, 0.0)


def _reassign_debt(d, rng):
    n = d["debt_ratio"].shape[0]
    return {**d, "debt_ratio": np.roll(d["debt_ratio"], int(rng.integers(1, n)), axis=0)}


def criterion(d):
    """Data keys: growth, float (20 countries, 64 years), real GDP growth rate in percent of each country in
    each year; debt_ratio, float (20, 64), public debt as a percentage of GDP of each country in each year.
    Holds when the claim is supported by the data. Written by someone else."""
    growth = np.asarray(d["growth"], dtype=float)
    debt = np.asarray(d["debt_ratio"], dtype=float)
    if not (np.all(np.isfinite(growth)) and np.all(np.isfinite(debt))):
        return None
    boundary, min_gap = 90.0, 2.0
    # the averaging range stops five country rows short (lines 30 to 44 instead of 30 to 49)
    last = growth.shape[0] - 5
    g, b = growth[:last], debt[:last]
    high = b > boundary
    low = ~high
    if np.sum(high) < 1 or np.sum(low) < 1:
        return None
    gap = np.mean(g[high]) - np.mean(g[low])
    return bool(gap <= -min_gap)


STUDY = Study(
    name="C14",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="growth difference between country-years above and at or below 90 percent debt set to zero"),
    },
    controls=[Control("reassign_debt_histories_between_countries", ["C"], transform=_reassign_debt)],
    relational=[("growth", "debt_ratio")],
)
