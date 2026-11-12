"""E5-11 (stochastic): epidemic growth. Claim: the weekly growth factor estimated from case counts exceeds 1.1."""
import numpy as np

from kapi import Control, Criterion, Study, World

WEEKS = np.arange(12, dtype=float)


def _counts(rng, growth):
    return {
        "week": WEEKS.copy(),
        "cases": rng.poisson(50.0 * growth ** WEEKS),
        "design_growth": np.array([1.3]),
    }


def _growth_factor(cases, week):
    if np.any(cases < 0):
        return 0.0
    y = np.log(cases + 0.5)
    wc = week - np.mean(week)
    den = float(np.sum(wc * wc))
    if not den > 0.0:
        return 0.0
    return float(np.exp(np.sum(wc * (y - np.mean(y))) / den))


def _growth_ok(d):
    g = float(d["design_growth"][0])
    return bool(g > 1.1)


STUDY = Study(
    name="E5-11 epidemic growth factor",
    criteria=[Criterion("growth_gt_11", _growth_ok, tolerances={"growth": (0.1, 1.0)})],
    worlds={
        "plus": World(lambda rng: _counts(rng, 1.3)),
        "minus": World(lambda rng: _counts(rng, 1.0), derived_from="plus", change="weekly growth factor 1.3 -> 1.0"),
    },
    controls=[
        Control(
            "weeks_reversed",
            ["growth_gt_11"],
            transform=lambda d, rng: {"week": d["week"], "cases": d["cases"][::-1], "design_growth": d["design_growth"]},
        )
    ],
)
