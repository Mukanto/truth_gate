"""E4-14: Two-arm trial with registry follow-up. The treatment raises the outcome in all randomised patients (one-sided Welch t test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ARM = 100
EFFECT = 0.25
ALPHA = 0.05
T_CRIT = 1.6526             # one-sided t quantile, df = 198


def make_world(effect):
    def generate(rng):
        y_t = rng.normal(effect, 1.0, N_ARM)
        y_c = rng.normal(0.0, 1.0, N_ARM)
        # side effects make poorly responding treated patients stop attending; the registry still records y
        p_stop = 1.0 / (1.0 + np.exp(2.0 * (y_t - effect) + 1.0))
        done_t = (rng.random(N_ARM) >= p_stop).astype(float)
        done_c = (rng.random(N_ARM) >= 0.1).astype(float)
        return {"y_t": y_t, "y_c": y_c, "done_t": done_t, "done_c": done_c}
    return generate


def t_stat(a, b):
    if a.size < 2 or b.size < 2:
        return np.nan
    with np.errstate(all="ignore"):
        return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)


def treatment_effect(d):
    return bool(t_stat(d["y_t"], d["y_c"]) > T_CRIT)


def relabel(d, rng):
    n = d["y_t"].size
    idx = rng.permutation(2 * n)
    y = np.concatenate([d["y_t"], d["y_c"]])[idx]
    done = np.concatenate([d["done_t"], d["done_c"]])[idx]
    return {"y_t": y[:n], "y_c": y[n:], "done_t": done[:n], "done_c": done[n:]}


STUDY = Study(
    name="E4-14 trial with differential dropout",
    criteria=[Criterion("treatment_effect", treatment_effect)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 0.25 -> 0 (dropout mechanism unchanged)"),
    },
    controls=[Control("patients_reassigned", ["treatment_effect"], transform=relabel)],
    targets=Targets(size=ALPHA),
)
