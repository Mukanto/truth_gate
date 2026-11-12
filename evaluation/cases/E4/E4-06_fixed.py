"""E4-06: Bioequivalence. Test and reference formulations differ by less than the margin 0.2 in log AUC (two one-sided tests, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ARM = 40
SD = 0.3
MARGIN = 0.2
ALPHA = 0.05
T_ONE = 1.6647              # one-sided t quantile, df = 78
T_TWO = 1.9909              # two-sided t quantile, df = 78


def make_world(diff):
    def generate(rng):
        return {"test": rng.normal(diff, SD, N_ARM), "ref": rng.normal(0.0, SD, N_ARM)}
    return generate


def equivalent(d):
    a, b = d["test"], d["ref"]
    with np.errstate(all="ignore"):
        se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
        if not se > 0.0:
            return False
        diff = a.mean() - b.mean()
        return bool((diff + MARGIN) / se > T_ONE and (MARGIN - diff) / se > T_ONE)


STUDY = Study(
    name="E4-06 bioequivalence of two formulations",
    criteria=[Criterion("equivalent", equivalent, tolerances={"margin": (MARGIN, 1.0)})],
    worlds={
        "plus": World(make_world(0.0)),
        "minus": World(make_world(MARGIN), derived_from="plus", change="true difference 0 -> 0.2 (the margin)"),
    },
    controls=[Control("known_different_comparator", ["equivalent"], world=World(make_world(0.5)))],
    targets=Targets(size=ALPHA),
)
