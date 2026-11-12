"""E4-03: Two-arm trial recording sex, age band and site. The treatment raises the outcome in the trial population (one-sided Welch t test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N = 240                     # randomised 1:1
EFFECT = 0.2
ALPHA = 0.05
T_CRIT = 1.6513             # one-sided t quantile, df = 238
SUBGROUPS = (("sex", 2), ("age", 3), ("site", 4))


def make_world(effect):
    def generate(rng):
        arm = np.repeat([0.0, 1.0], N // 2)
        sex = rng.integers(0, 2, N).astype(float)
        age = rng.integers(0, 3, N).astype(float)
        site = rng.integers(0, 4, N).astype(float)
        y = effect * arm + rng.normal(0.0, 1.0, N)
        return {"arm": arm, "sex": sex, "age": age, "site": site, "y": y}
    return generate


def t_stat(y, arm):
    yt, yc = y[arm == 1.0], y[arm == 0.0]
    if yt.size < 2 or yc.size < 2:
        return np.nan
    with np.errstate(all="ignore"):
        return (yt.mean() - yc.mean()) / np.sqrt(yt.var(ddof=1) / yt.size + yc.var(ddof=1) / yc.size)


def benefit(d):
    if t_stat(d["y"], d["arm"]) > T_CRIT:
        return True
    for key, levels in SUBGROUPS:
        for level in range(levels):
            sel = d[key] == level
            if t_stat(d["y"][sel], d["arm"][sel]) > T_CRIT:
                return True
    return False


def relabel(d, rng):
    out = dict(d)
    out["arm"] = rng.permutation(d["arm"])
    return out


STUDY = Study(
    name="E4-03 trial with recorded subgroups",
    criteria=[Criterion("benefit", benefit)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 0.2 -> 0"),
    },
    controls=[Control("arm_labels_permuted", ["benefit"], transform=relabel)],
    targets=Targets(size=ALPHA),
)
