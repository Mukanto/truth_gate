"""E4-10: Blood-pressure programme. The intervention lowers systolic pressure in screened hypertensive patients (one-sided Welch t test on the change, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N_ARM = 40
SCREEN = 150.0              # mmHg, enrolment threshold on the screening visit
TRUE_MEAN, TRUE_SD, VISIT_SD = 140.0, 15.0, 10.0
EFFECT = 5.0                # mmHg reduction
ALPHA = 0.05
T_CRIT_PAIRED = 1.6849      # one-sided t quantile, df = 39
T_CRIT_TWO = 1.6647         # one-sided t quantile, df = 78


def enrol(rng, effect):
    true, base = np.empty(0), np.empty(0)
    while true.size < N_ARM:
        t = rng.normal(TRUE_MEAN, TRUE_SD, 4 * N_ARM)
        b = t + rng.normal(0.0, VISIT_SD, t.size)
        keep = b > SCREEN
        true, base = np.concatenate([true, t[keep]]), np.concatenate([base, b[keep]])
    true, base = true[:N_ARM], base[:N_ARM]
    return base, true - effect + rng.normal(0.0, VISIT_SD, N_ARM)


def make_world(effect):
    def generate(rng):
        base_t, follow_t = enrol(rng, effect)
        base_c, follow_c = enrol(rng, 0.0)
        return {"base_t": base_t, "follow_t": follow_t, "base_c": base_c, "follow_c": follow_c}
    return generate


def t_stat(a, b):
    with np.errstate(all="ignore"):
        return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)


def lowers_pressure(d):
    drop_t = d["base_t"] - d["follow_t"]
    with np.errstate(all="ignore"):
        return bool(drop_t.mean() / (drop_t.std(ddof=1) / np.sqrt(drop_t.size)) > T_CRIT_PAIRED)


def swap_arms(d, rng):
    return {"base_t": d["base_c"], "follow_t": d["follow_c"], "base_c": d["base_t"], "follow_c": d["follow_t"]}


STUDY = Study(
    name="E4-10 blood-pressure programme",
    criteria=[Criterion("lowers_pressure", lowers_pressure)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="intervention effect 5 mmHg -> 0"),
    },
    controls=[Control("arms_swapped", ["lowers_pressure"], transform=swap_arms)],
    targets=Targets(size=ALPHA),
)
