"""E4-04: Prognostic biomarker. Patients above the biomarker cutpoint have a higher event rate (one-sided pooled two-proportion test, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N = 400
SLOPE = 0.6                 # log-odds of an event per SD of the biomarker
BASE_LOGIT = -1.1
ALPHA = 0.05
T_CRIT = 1.6487             # one-sided t quantile, df = 398
CUT_QUANTILES = np.array([0.5])            # pre-registered: median split


def make_world(slope):
    def generate(rng):
        x = rng.normal(0.0, 1.0, N)
        p = 1.0 / (1.0 + np.exp(-(BASE_LOGIT + slope * x)))
        return {"x": x, "event": (rng.random(N) < p).astype(float)}
    return generate


def z_split(x, event, cut):
    hi, lo = event[x > cut], event[x <= cut]
    if hi.size < 2 or lo.size < 2:
        return np.nan
    with np.errstate(all="ignore"):
        return (hi.mean() - lo.mean()) / np.sqrt(event.var(ddof=1) * (1.0 / hi.size + 1.0 / lo.size))


def high_risk(d):
    cuts = np.quantile(d["x"], CUT_QUANTILES)
    z = np.array([z_split(d["x"], d["event"], c) for c in cuts])
    return bool(np.any(z > T_CRIT))


def permute_events(d, rng):
    return {"x": d["x"], "event": rng.permutation(d["event"])}


STUDY = Study(
    name="E4-04 biomarker cutpoint",
    criteria=[Criterion("high_risk", high_risk)],
    worlds={
        "plus": World(make_world(SLOPE)),
        "minus": World(make_world(0.0), derived_from="plus", change="biomarker log-odds slope 0.6 -> 0"),
    },
    controls=[Control("events_permuted", ["high_risk"], transform=permute_events)],
    targets=Targets(size=ALPHA),
)
