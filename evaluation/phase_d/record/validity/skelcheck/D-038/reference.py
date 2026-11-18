"""D-038: Across countries, annual lung-cancer deaths and annual cigarette sales are associated after accounting for population: the standardised slope of deaths on cigarette sales, with population accounted for, is at least 0.2 in absolute value."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_COUNTRY = 150
POP_MEDIAN = 9.0
POP_LOG_SD = 1.1
CIG_PER_PERSON = 1500.0
CIG_LOG_SD = 0.45
CIG_POP_LOAD = 0.25
DEATH_RATE = 0.3
DEATH_NOISE_SD = 0.30


def _gen(rng, beta):
    pop = POP_MEDIAN * np.exp(POP_LOG_SD * rng.standard_normal(N_COUNTRY))
    zp = (pop - pop.mean()) / pop.std()
    eps = rng.standard_normal(N_COUNTRY)
    c = CIG_PER_PERSON * np.exp(CIG_LOG_SD * (CIG_POP_LOAD * zp + np.sqrt(1.0 - CIG_POP_LOAD ** 2) * eps))
    sold = c * pop
    deaths = DEATH_RATE * pop * (c / CIG_PER_PERSON) ** beta * np.exp(DEATH_NOISE_SD * rng.standard_normal(N_COUNTRY))
    return {
        "lung_cancer_deaths": np.asarray(deaths, dtype=float),
        "cigarettes_sold": np.asarray(sold, dtype=float),
        "population": np.asarray(pop, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.6)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: lung_cancer_deaths (150,) float, total lung-cancer deaths in one year, in thousands;
    cigarettes_sold (150,) float, total cigarettes sold in the same year, in millions;
    population (150,) float, population in millions.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_per_capita_sales(d, rng):
    p = np.asarray(d["population"], dtype=float)
    x = np.asarray(d["cigarettes_sold"], dtype=float)
    c = x / p
    order = np.argsort(p, kind="stable")
    c_new = c.copy()
    block = 15
    for start in range(0, p.shape[0], block):
        idx = order[start:start + block]
        c_new[idx] = c[idx[rng.permutation(idx.shape[0])]]
    return {
        "lung_cancer_deaths": np.asarray(d["lung_cancer_deaths"], dtype=float),
        "cigarettes_sold": c_new * p,
        "population": p,
    }


STUDY = Study(
    name="D-038",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="elasticity of the lung-cancer death rate to per-capita cigarette sales set from 0.6 to 0"),
    },
    controls=[Control("permute_per_capita_sales", ["C"], transform=permute_per_capita_sales)],
)
