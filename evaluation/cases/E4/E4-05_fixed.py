"""E4-05: Cell assay, six animals per group, twenty cells per animal. Treated animals show a higher response (one-sided Welch t test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ANIMALS, N_CELLS = 6, 20          # per group
ANIMAL_SD, CELL_SD = 1.0, 1.0
EFFECT = 2.5
ALPHA = 0.05
T_CRIT = 1.8125                     # one-sided t quantile, df = 10 (animal means)


def make_world(effect):
    def generate(rng):
        def group(mu):
            animal = rng.normal(mu, ANIMAL_SD, (N_ANIMALS, 1))
            return animal + rng.normal(0.0, CELL_SD, (N_ANIMALS, N_CELLS))
        return {"Y_t": group(effect), "Y_c": group(0.0)}
    return generate


def t_stat(a, b):
    with np.errstate(all="ignore"):
        return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)


def treated_higher(d):
    return bool(t_stat(d["Y_t"].mean(axis=1), d["Y_c"].mean(axis=1)) > T_CRIT)


STUDY = Study(
    name="E4-05 cell assay with animals as units",
    criteria=[Criterion("treated_higher", treated_higher)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 2.5 -> 0"),
    },
    controls=[Control("vehicle_animals", ["treated_higher"], world=World(make_world(0.0)))],
    targets=Targets(size=ALPHA),
)
