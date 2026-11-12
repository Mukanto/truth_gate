"""E4-09: Insulation retrofit. Retrofitted houses lose less heat than control houses (one-sided Welch t test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ARM = 30
BASE_LOSS, SD = 5.0, 1.0    # kW
REDUCTION = 1.0             # kW saved by the retrofit
ALPHA = 0.05
T_CRIT = 1.6716             # one-sided t quantile, df = 58


def make_world(reduction):
    def generate(rng):
        return {"loss_retrofit": rng.normal(BASE_LOSS - reduction, SD, N_ARM),
                "loss_control": rng.normal(BASE_LOSS, SD, N_ARM)}
    return generate


def t_stat(a, b):
    with np.errstate(all="ignore"):
        return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)


def less_heat_loss(d):
    return bool(t_stat(d["loss_retrofit"], d["loss_control"]) > T_CRIT)


def swap_arms(d, rng):
    return {"loss_retrofit": d["loss_control"], "loss_control": d["loss_retrofit"]}


STUDY = Study(
    name="E4-09 insulation retrofit",
    criteria=[Criterion("less_heat_loss", less_heat_loss)],
    worlds={
        "plus": World(make_world(REDUCTION)),
        "minus": World(make_world(0.0), derived_from="plus", change="heat-loss reduction 1 kW -> 0"),
    },
    controls=[Control("arms_swapped", ["less_heat_loss"], transform=swap_arms)],
    targets=Targets(size=ALPHA),
)
