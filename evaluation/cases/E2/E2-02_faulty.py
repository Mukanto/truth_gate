"""E2-02: Two-arm experiment. The treatment raises the outcome (one-sided permutation test, p < 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, World

N_ARM = 30
EFFECT = 1.0
N_PERM = 199
ALPHA = 0.05
PERM_SEED = 20261105


def make_world(effect):
    def generate(rng):
        return {"y_t": rng.normal(effect, 1.0, N_ARM), "y_c": rng.normal(0.0, 1.0, N_ARM)}
    return generate


def treatment_effect(d):
    yt, yc = d["y_t"], d["y_c"]
    pooled = np.concatenate([yt, yc])
    observed = yt.mean() - yc.mean()
    perm_rng = np.random
    idx = np.argsort(perm_rng.random((N_PERM, pooled.size)), axis=1)
    perm = pooled[idx]
    diffs = perm[:, :yt.size].mean(axis=1) - perm[:, yt.size:].mean(axis=1)
    p = (1 + np.sum(diffs >= observed)) / (N_PERM + 1)
    return bool(p < ALPHA)


def relabel(d, rng):
    pooled = rng.permutation(np.concatenate([d["y_t"], d["y_c"]]))
    n = d["y_t"].size
    return {"y_t": pooled[:n], "y_c": pooled[n:]}


STUDY = Study(
    name="E2-02 treatment effect by permutation test",
    criteria=[Criterion("treatment_effect", treatment_effect)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 1.0 -> 0"),
        "null": World(make_world(0.0)),
    },
    controls=[Control("labels_reassigned", ["treatment_effect"], transform=relabel)],
)
