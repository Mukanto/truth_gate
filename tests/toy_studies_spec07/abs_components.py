"""Spec 0.7 fixture (stochastic): a criterion with two components that abstains through dict values on minus.
Component ``first`` abstains when no peak was found (about 20% of the minus samples), component ``third`` when fewer
than three peaks were found (about 40%).  ``ABSTAIN`` as in abs_minus.py."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World

ABSTAIN = None


def peaks_tall(d):
    p = d["peaks"]
    return {
        "first": ABSTAIN if p.size < 1 else bool(p[0] > 5.0),
        "third": ABSTAIN if p.size < 3 else bool(p[2] > 5.0),
    }


def minus(rng):
    return {"peaks": rng.normal(2.0, 1.0, int(rng.choice([0, 2, 3, 3, 3])))}


STUDY = Study(
    name="spec07_abs_components",
    criteria=[Criterion("peaks_tall", peaks_tall, components=["first", "third"])],
    worlds={
        "plus": World(lambda rng: {"peaks": rng.normal(8.0, 1.0, 3)}),
        "minus": World(minus, derived_from="plus", change="peaks 8 -> 2, and sometimes missing"),
    },
    controls=[Control("negate", ["peaks_tall"], transform=lambda d, rng: {"peaks": -d["peaks"]})],
    budget=Budget(samples=40),
)
