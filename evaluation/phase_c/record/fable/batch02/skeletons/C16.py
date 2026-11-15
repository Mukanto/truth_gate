"""C16: In adult rats, animals given the drug have a larger heart weight than untreated animals after accounting for body mass: in a linear regression of heart weight on treatment status and body mass, the coefficient of treatment status is positive and significant at the one-sided 5% level (t test)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, drug_effect_mg):
    n = 48
    treated = np.zeros(n, dtype=bool)
    treated[rng.permutation(n)[:24]] = True
    # the drug slows weight gain a little (both worlds): treated animals are about 25 g lighter
    body_mass = rng.normal(410.0, 35.0, n) - 25.0 * treated
    # allometric line with a non-zero intercept, plus individual scatter
    heart_weight = 240.0 + 2.2 * body_mass + drug_effect_mg * treated + rng.normal(0.0, 65.0, n)
    return {
        "heart_weight": heart_weight.astype(np.float64),
        "body_mass": body_mass.astype(np.float64),
        "treated": treated,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 65.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: heart_weight (48,) float, wet heart weight of each animal in mg; body_mass (48,) float,
    body mass of each animal in g; treated (48,) bool, True for animals given the drug.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C16",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="direct effect of the drug on heart weight at given body mass set to 0 mg (was +65 mg); the effect of the drug on body mass is kept"),
    },
    controls=[
        Control("permute_treated", ["C"], transform=lambda d, rng: {**d, "treated": _permute_changed(d["treated"], rng)}),
    ],
)
