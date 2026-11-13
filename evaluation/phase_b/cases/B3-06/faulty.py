"""W17: Wealthier countries emit more carbon dioxide per person: across 150 countries, the Spearman rank correlation between per-capita carbon dioxide emissions and per-capita gross domestic product is at least 0.5."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 150


def _gen(rng, eff):
    pop = np.exp(np.log(10.0) + 1.6 * rng.standard_normal(N))          # millions
    zg = rng.standard_normal(N)
    e = rng.standard_normal(N)
    gdp_pc = 15.0 * np.exp(0.9 * zg)                                   # thousand USD per person
    sd_res = np.sqrt(0.77 - eff * (0.8 * 0.9) ** 2)                    # total log variance of CO2 per person is the same in both worlds
    co2_pc = 4.0 * np.exp(eff * 0.8 * 0.9 * zg + sd_res * e)           # tonnes per person
    gdp_total = gdp_pc * pop                                           # billion USD
    co2_total = co2_pc * pop                                           # megatonnes
    return {"co2_emissions_total": co2_total, "gdp_total": gdp_total, "population": pop}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: co2_emissions_total (150,) annual national carbon dioxide emissions, megatonnes; gdp_total (150,) national
    gross domestic product, billions of US dollars (purchasing-power adjusted); population (150,) national population,
    millions.
    Holds when the claim is supported by the data. Written by someone else."""
    def rank(x):
        u, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        return (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    co2 = np.asarray(d["co2_emissions_total"], dtype=float)
    gdp = np.asarray(d["gdp_total"], dtype=float)
    pop = np.asarray(d["population"], dtype=float)
    if not (np.all(np.isfinite(co2)) and np.all(np.isfinite(gdp)) and np.all(np.isfinite(pop))):
        return None
    if np.std(co2) == 0 or np.std(gdp) == 0 or np.std(pop) == 0:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        pc_co2 = co2 / pop                           # per-capita emissions
        pc_gdp = gdp / pop                           # per-capita GDP
    if not (np.all(np.isfinite(pc_co2)) and np.all(np.isfinite(pc_gdp))) or np.std(pc_co2) == 0 or np.std(pc_gdp) == 0:
        return None
    rho = np.corrcoef(rank(pc_co2), rank(pc_gdp))[0, 1]
    return bool(rho >= 0.5)


def permute_per_capita_emissions(d, rng):
    pc = d["co2_emissions_total"] / d["population"]
    return {**d, "co2_emissions_total": pc[rng.permutation(N)] * d["population"]}


STUDY = Study(
    name="W17",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="per-capita CO2 follows per-capita GDP (elasticity 0.8, rank correlation about 0.82) -> per-capita CO2 independent of per-capita GDP (same marginal distribution); the very unequal populations, which make the totals strongly correlated, are unchanged"),
    },
    controls=[Control("permute_per_capita_emissions", ["C"], transform=permute_per_capita_emissions)],
)
