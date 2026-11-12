"""E2-13: Two-arm trial. The treatment raises the outcome by a small standardized effect (d = 0.1): Welch t > 1.645."""
import numpy as np

from kapi import Control, Criterion, Study, World

N_PER_ARM = 8
EFFECT = 0.1
T_CRIT = 1.645


def make_world(effect):
    def generate(rng):
        return {"y_t": rng.normal(effect, 1.0, N_PER_ARM), "y_c": rng.normal(0.0, 1.0, N_PER_ARM)}
    return generate


def welch_t(d):
    yt, yc = d["y_t"], d["y_c"]
    with np.errstate(all="ignore"):
        se = np.sqrt(yt.var(ddof=1) / yt.size + yc.var(ddof=1) / yc.size)
        return bool((yt.mean() - yc.mean()) / se > T_CRIT)


def relabel(d, rng):
    pooled = rng.permutation(np.concatenate([d["y_t"], d["y_c"]]))
    n = d["y_t"].size
    return {"y_t": pooled[:n], "y_c": pooled[n:]}


STUDY = Study(
    name="E2-13 small treatment effect",
    criteria=[Criterion("welch_t", welch_t)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 0.1 -> 0"),
    },
    controls=[Control("labels_reassigned", ["welch_t"], transform=relabel)],
)
