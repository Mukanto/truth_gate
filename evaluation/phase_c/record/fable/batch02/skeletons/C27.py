"""C27: Prenatal exposure raises adult open-field activity: the mean activity score of offspring of exposed dams is higher than that of offspring of control dams, and a two-sample t test of the difference between the two group means gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, exposure_effect):
    dams, pups = 20, 8
    exposed = np.zeros(dams, dtype=bool)
    exposed[rng.permutation(dams)[:10]] = True
    litter = rng.normal(0.0, 15.0, dams)                    # litter effect shared by the pups of one dam
    pup = rng.normal(0.0, 18.0, (dams, pups))
    activity = 100.0 + (litter + exposure_effect * exposed)[:, None] + pup
    activity = np.clip(activity, 1.0, None)
    return {"activity": activity.astype(np.float64), "exposed": exposed}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 25.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: activity (20, 8) float, open-field activity score (distance travelled, arbitrary units) measured
    in adulthood on each pup (axis 1) of each dam (axis 0); exposed (20,) bool, whether the dam received the
    exposure during pregnancy.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C27",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of prenatal exposure on activity set to 0 (was +25 units); litter effects and pup-to-pup variability kept"),
    },
    controls=[
        Control("permute_exposed_across_dams", ["C"], transform=lambda d, rng: {**d, "exposed": _permute_changed(d["exposed"], rng)}),
    ],
)
