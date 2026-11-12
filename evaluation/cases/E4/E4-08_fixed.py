"""E4-08: Small treated cohort against a large control cohort. The treatment raises the outcome (one-sided t test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_T, N_C = 8, 60
SD_T, SD_C = 4.0, 1.0       # treated responses are far more variable
EFFECT = 5.0
ALPHA = 0.05
Z = 1.6449                  # standard normal quantile at 1 - ALPHA


def t_quantile(df):
    """Upper 1 - ALPHA quantile of Student's t (Cornish-Fisher expansion, three terms)."""
    z = Z
    return (z + (z ** 3 + z) / (4.0 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96.0 * df ** 2)
            + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384.0 * df ** 3))


def make_world(effect):
    def generate(rng):
        return {"y_t": rng.normal(effect, SD_T, N_T), "y_c": rng.normal(0.0, SD_C, N_C)}
    return generate


def welch(a, b):
    va, vb = a.var(ddof=1) / a.size, b.var(ddof=1) / b.size
    df = (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))
    return (a.mean() - b.mean()) / np.sqrt(va + vb), df


def pooled(a, b):
    sp2 = ((a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)) / (a.size + b.size - 2)
    return (a.mean() - b.mean()) / np.sqrt(sp2 * (1.0 / a.size + 1.0 / b.size)), a.size + b.size - 2.0


def treatment_effect(d):
    with np.errstate(all="ignore"):
        t, df = welch(d["y_t"], d["y_c"])
        return bool(t > t_quantile(df))


def relabel(d, rng):
    pooled_values = rng.permutation(np.concatenate([d["y_t"], d["y_c"]]))
    n = d["y_t"].size
    return {"y_t": pooled_values[:n], "y_c": pooled_values[n:]}


STUDY = Study(
    name="E4-08 small treated cohort with unequal variances",
    criteria=[Criterion("treatment_effect", treatment_effect)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 5 -> 0 (variances unchanged)"),
    },
    controls=[Control("labels_reassigned", ["treatment_effect"], transform=relabel)],
    targets=Targets(size=ALPHA),
)
