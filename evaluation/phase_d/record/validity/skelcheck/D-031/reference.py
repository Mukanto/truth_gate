"""D-031: Across cities, annual offences recorded and the median age of residents are associated after accounting for population: the partial correlation coefficient between offences and median age, given population, is at least 0.25 in absolute value."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_CITY = 500
POP_MEDIAN = 60.0
POP_LOG_SD = 0.8
AGE_MEAN = 38.0
AGE_SD = 4.5
AGE_POP_CORR = -0.3
OFF_CONST = 20.0
OFF_POP_EXP = 1.15
OFF_NOISE_SD = 0.30


def _gen(rng, beta):
    pop = POP_MEDIAN * np.exp(POP_LOG_SD * rng.standard_normal(N_CITY))
    zp = (pop - pop.mean()) / pop.std()
    eps = rng.standard_normal(N_CITY)
    age = AGE_MEAN + AGE_SD * (AGE_POP_CORR * zp + np.sqrt(1.0 - AGE_POP_CORR ** 2) * eps)
    za = (age - age.mean()) / age.std()
    log_off = np.log(OFF_CONST) + OFF_POP_EXP * np.log(pop) + beta * za + OFF_NOISE_SD * rng.standard_normal(N_CITY)
    return {
        "offences": np.asarray(np.exp(log_off), dtype=float),
        "median_age": np.asarray(age, dtype=float),
        "population": np.asarray(pop, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, -0.25)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: offences (500,) float, total offences recorded in each city in one year;
    median_age (500,) float, median age of residents in years;
    population (500,) float, population of each city in thousands.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_age_within_population(d, rng):
    p = np.asarray(d["population"], dtype=float)
    a = np.asarray(d["median_age"], dtype=float)
    order = np.argsort(p, kind="stable")
    out = a.copy()
    block = 25
    for start in range(0, p.shape[0], block):
        idx = order[start:start + block]
        out[idx] = a[idx[rng.permutation(idx.shape[0])]]
    return {"offences": np.asarray(d["offences"], dtype=float), "median_age": out, "population": p}


STUDY = Study(
    name="D-031",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of median age on log offences (per SD of age, population held) set from -0.25 to 0"),
    },
    controls=[Control("permute_age_within_population", ["C"], transform=permute_age_within_population)],
)
