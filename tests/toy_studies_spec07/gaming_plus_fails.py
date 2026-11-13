"""Spec 0.7 section 5, gaming (c): 40% abstention and 60% FAILS on plus, never HOLDS.

Plus carries a uniform draw ``u``; the criterion abstains for u < 0.4 and fails otherwise.  The abstention rate (about
40 of 100) is below one half, so K1_UNDEFINED must not fire; zero HOLDS on plus is K2_HOLDS_UNREACHABLE, mandatory."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World


def never_holds(d):
    u = d["u"][0]
    if u < 0:  # not a plus sample
        return False
    if u < 0.4:
        return None
    return False


STUDY = Study(
    name="spec07_gaming_plus_fails",
    criteria=[Criterion("never_holds", never_holds)],
    worlds={
        "plus": World(lambda rng: {"u": rng.random(1)}),
        "minus": World(lambda rng: {"u": np.array([-1.0])}, derived_from="plus", change="u -> -1"),
    },
    controls=[Control("negate", ["never_holds"], transform=lambda d, rng: {"u": -d["u"]})],
    budget=Budget(samples=100),
)
