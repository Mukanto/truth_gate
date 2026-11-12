"""E4-01: Two-arm trial with enrolment in waves. The treatment raises the outcome (one-sided Welch t test at the declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_MAX = 100                 # per arm, in enrolment order
LOOK_EVERY = 5              # patients per arm in each enrolment wave
EFFECT = 0.25
ALPHA = 0.05
T_CRIT = 1.6526             # one-sided t quantile, df = 198


def make_world(effect):
    def generate(rng):
        return {"y_t": rng.normal(effect, 1.0, N_MAX), "y_c": rng.normal(0.0, 1.0, N_MAX)}
    return generate


def t_stat(yt, yc):
    with np.errstate(all="ignore"):
        return (yt.mean() - yc.mean()) / np.sqrt(yt.var(ddof=1) / yt.size + yc.var(ddof=1) / yc.size)


def treatment_effect(d):
    return bool(t_stat(d["y_t"], d["y_c"]) > T_CRIT)


def relabel(d, rng):
    pooled = rng.permutation(np.concatenate([d["y_t"], d["y_c"]]))
    n = d["y_t"].size
    return {"y_t": pooled[:n], "y_c": pooled[n:]}


STUDY = Study(
    name="E4-01 two-arm trial enrolled in waves",
    criteria=[Criterion("treatment_effect", treatment_effect)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 0.25 -> 0"),
        "null": World(make_world(0.0)),
    },
    controls=[Control("labels_reassigned", ["treatment_effect"], transform=relabel)],
    targets=Targets(size=ALPHA),
)
