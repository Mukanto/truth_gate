"""E4-07: Two-arm experiment with a written outlier rule. The treatment raises the outcome (one-sided Welch t test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ARM = 30
EFFECT = 0.8
ALPHA = 0.05
T_CRIT = 1.6716             # one-sided t quantile, df = 58
MAX_EXCLUDE = 3             # observations per arm the outlier rule may set aside


def make_world(effect):
    def generate(rng):
        return {"y_t": rng.normal(effect, 1.0, N_ARM), "y_c": rng.normal(0.0, 1.0, N_ARM)}
    return generate


def t_stat(yt, yc):
    with np.errstate(all="ignore"):
        return (yt.mean() - yc.mean()) / np.sqrt(yt.var(ddof=1) / yt.size + yc.var(ddof=1) / yc.size)


def treatment_effect(d):
    yt, yc = np.sort(d["y_t"]), np.sort(d["y_c"])
    for k in range(MAX_EXCLUDE + 1):
        if t_stat(yt[k:], yc[:yc.size - k]) > T_CRIT:
            return True
    return False


def relabel(d, rng):
    pooled = rng.permutation(np.concatenate([d["y_t"], d["y_c"]]))
    n = d["y_t"].size
    return {"y_t": pooled[:n], "y_c": pooled[n:]}


STUDY = Study(
    name="E4-07 two-arm experiment with an outlier rule",
    criteria=[Criterion("treatment_effect", treatment_effect)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 0.8 -> 0"),
        "null": World(make_world(0.0)),
    },
    controls=[Control("labels_reassigned", ["treatment_effect"], transform=relabel)],
    targets=Targets(size=ALPHA),
)
