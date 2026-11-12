"""E4-02: Trial with ten endpoints. The treatment improves outcomes (one-sided Welch t tests, familywise declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ARM, N_END = 60, 10
EFFECT = 0.8                # on endpoint 0, the mechanism's target; the other endpoints are unaffected
ALPHA = 0.05
T_CRIT_EACH = 2.6182        # one-sided t quantile at ALPHA / N_END, df = 118


def make_world(effect):
    def generate(rng):
        shift = np.zeros(N_END)
        shift[0] = effect
        return {"Y_t": rng.normal(0.0, 1.0, (N_ARM, N_END)) + shift, "Y_c": rng.normal(0.0, 1.0, (N_ARM, N_END))}
    return generate


def any_endpoint(d):
    Yt, Yc = d["Y_t"], d["Y_c"]
    with np.errstate(all="ignore"):
        se = np.sqrt(Yt.var(axis=0, ddof=1) / Yt.shape[0] + Yc.var(axis=0, ddof=1) / Yc.shape[0])
        t = (Yt.mean(axis=0) - Yc.mean(axis=0)) / se
    return bool(np.any(t > T_CRIT_EACH))


def relabel(d, rng):
    pooled = rng.permutation(np.concatenate([d["Y_t"], d["Y_c"]]), axis=0)
    n = d["Y_t"].shape[0]
    return {"Y_t": pooled[:n], "Y_c": pooled[n:]}


STUDY = Study(
    name="E4-02 ten-endpoint trial",
    criteria=[Criterion("any_endpoint", any_endpoint)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="effect on endpoint 0: 0.8 -> 0"),
    },
    controls=[Control("patients_reassigned", ["any_endpoint"], transform=relabel)],
    targets=Targets(size=ALPHA),
)
