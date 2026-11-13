"""Spec 0.7 fixture (stochastic): negative values are invalid data, so the criterion abstains on them.  The noise
probe (N(0, 1) values, 30 per sample) contains a negative value in every sample (probability 1 - 2**-30), so the
criterion abstains on every noise-probe sample; plus (mean 8) and minus (mean 5) never contain one.  ``ABSTAIN`` as in
abs_minus.py."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World

ABSTAIN = None


def high_mean(d):
    x = d["x"]
    if np.any(x < 0):
        return ABSTAIN
    return bool(np.mean(x) > 6.5)


STUDY = Study(
    name="spec07_abs_probes",
    criteria=[Criterion("high_mean", high_mean)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(8.0, 1.0, 30)}),
        "minus": World(lambda rng: {"x": rng.normal(5.0, 1.0, 30)}, derived_from="plus", change="mean 8 -> 5"),
    },
    controls=[Control("shrink", ["high_mean"], transform=lambda d, rng: {"x": d["x"] * 0.1})],
    budget=Budget(samples=40),
)
