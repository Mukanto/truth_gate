"""Spec 0.7 section 5, gaming (e): a broken minus world whose data are all NaN, with a criterion that returns None on
non-finite input.  Every minus sample is an abstention, which would read as a clean pass if abstentions were free:
K1_ABSTAINED_MAJORITY:world:minus must cap the verdict at WEAK."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World


def high_mean(d):
    x = d["x"]
    if not np.all(np.isfinite(x)):
        return None
    return bool(np.mean(x) > 3.0)


STUDY = Study(
    name="spec07_gaming_nan_minus",
    criteria=[Criterion("high_mean", high_mean)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(5.0, 1.0, 30)}),
        "minus": World(lambda rng: {"x": np.full(30, np.nan)}, derived_from="plus", change="all data missing (bug)"),
    },
    controls=[Control("shrink", ["high_mean"], transform=lambda d, rng: {"x": d["x"] * 0.1})],
    budget=Budget(samples=40),
)
