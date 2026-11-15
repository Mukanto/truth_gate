"""C23: The drug improves motor coordination: the mean time spent on the rotarod is longer in the treatment group than in the control group, and a two-tailed two-sample t test of the difference between the two group means gives p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, drug_effect_s):
    rats, days = 10, 3
    treated = np.zeros(rats, dtype=bool)
    treated[rng.permutation(rats)[:5]] = True
    rat_level = rng.normal(0.0, 22.0, rats)                 # stable differences between rats
    learning = np.array([0.0, 15.0, 28.0])                  # improvement over the test days, both groups
    day_noise = rng.normal(0.0, 12.0, (rats, days))
    latency = 115.0 + learning[None, :] + (rat_level + drug_effect_s * treated)[:, None] + day_noise
    latency = np.clip(latency, 5.0, 300.0)                  # 300 s cut-off of the apparatus
    return {"latency": latency.astype(np.float64), "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 55.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: latency (10, 3) float, time in seconds that each rat (axis 0) stayed on the rotarod on each of
    the consecutive test days (axis 1); treated (10,) bool, True for rats in the treatment group, False for the
    control group.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C23",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of the drug on rotarod time set to 0 s (was +55 s); between-rat differences, learning over days and day-to-day noise kept"),
    },
    controls=[
        Control("permute_treated_across_rats", ["C"], transform=lambda d, rng: {**d, "treated": _permute_changed(d["treated"], rng)}),
    ],
)
