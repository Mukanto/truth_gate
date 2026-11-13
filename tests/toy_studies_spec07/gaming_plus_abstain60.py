"""Spec 0.7 section 5, gaming (d): 60% abstention on plus.

Plus carries a uniform draw ``u``; the criterion abstains for u < 0.6 and holds otherwise.  The abstention rate (about
60 of 100) is above one half: the criterion is not a test of the claim in the world where the claim is true, so K1 stays
UNDEFINED (the author's rule, spec 0.7 section 2.1 rule 1).  No exception is involved: this is not a failure."""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World


def mostly_abstains(d):
    u = d["u"][0]
    if u < 0:  # not a plus sample
        return False
    if u < 0.6:
        return None
    return True


STUDY = Study(
    name="spec07_gaming_plus_abstain60",
    criteria=[Criterion("mostly_abstains", mostly_abstains)],
    worlds={
        "plus": World(lambda rng: {"u": rng.random(1)}),
        "minus": World(lambda rng: {"u": np.array([-1.0])}, derived_from="plus", change="u -> -1"),
    },
    controls=[Control("negate", ["mostly_abstains"], transform=lambda d, rng: {"u": -d["u"]})],
    budget=Budget(samples=100),
)
