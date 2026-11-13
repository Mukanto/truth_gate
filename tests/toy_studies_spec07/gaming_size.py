"""Spec 0.7 section 5, gaming (a): a faulty criterion that holds on 15% of the minus samples and returns None on
another 15%.

Minus carries a uniform draw ``u``: the faulty branch holds for 0.10 <= u < 0.25 (15%) and abstains for
0.25 <= u < 0.40 (15%).  Plus is recognised by its large signal ``s`` and always holds.  The criterion has no cause to
hold on the zeros probe (u = 0), and the noise probe reaches the faulty branches only by chance (about 6% each).

Arithmetic (default budget, n = 200; one criterion, one control, no premise, no null world, so m = 1 + 1 + 2 = 4
comparisons and a = 0.05 / (2 * 4) = 0.00625, z = 2.498): 15% of 200 is 30 HOLDS, and the lower Wilson bound of 30/200 is
0.0976 > 0.05 = declared size, so K2_HIGH_SIZE is raised.  The bound stays above 0.05 down to 18 HOLDS (9%), i.e. the
flag does not depend on the realised draw."""
import numpy as np

from truth_gate import Control, Criterion, Study, World


def faulty(d):
    if d["s"][0] > 5.0:  # the real claim, true in plus
        return True
    u = d["u"][0]
    if 0.10 <= u < 0.25:  # the fault: holds where the claim is false
        return True
    if 0.25 <= u < 0.40:  # abstains on another 15% of those samples
        return None
    return False


STUDY = Study(
    name="spec07_gaming_size",
    criteria=[Criterion("faulty", faulty)],
    worlds={
        "plus": World(lambda rng: {"s": np.array([10.0]), "u": np.array([0.5])}),
        "minus": World(lambda rng: {"s": np.array([0.0]), "u": rng.random(1)}, derived_from="plus", change="signal 10 -> 0"),
    },
    controls=[Control("negate", ["faulty"], transform=lambda d, rng: {"s": -d["s"], "u": -d["u"]})],
)
