"""C22: The insecticide lowers invertebrate density: the mean density in treated tanks is lower than in control tanks, and a Welch two-sample t test of the difference between the two group means gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, treated_factor):
    tanks, samples = 8, 10
    treated = np.zeros(tanks, dtype=bool)
    treated[rng.permutation(tanks)[:4]] = True
    tank_level = 40.0 * np.exp(rng.normal(0.0, 0.20, tanks))        # between-tank variability
    tank_level = tank_level * np.where(treated, treated_factor, 1.0)
    patchiness = np.exp(rng.normal(0.0, 0.25, (tanks, samples)))    # sample-to-sample patchiness within a tank
    counts = rng.poisson(tank_level[:, None] * patchiness)          # animals counted in a one-litre sample
    return {"density": counts.astype(np.float64), "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.45)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 1.0)


def criterion(d):
    """Data keys: density (8, 10) float, invertebrates per litre counted in each of the water samples (axis 1)
    taken from each tank (axis 0); treated (8,) bool, whether the tank received the insecticide.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C22",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of the insecticide on tank density set to none (density ratio treated/control 1, was 0.45); between-tank variability, within-tank patchiness and counting noise kept"),
    },
    controls=[
        Control("permute_treated_across_tanks", ["C"], transform=lambda d, rng: {**d, "treated": _permute_changed(d["treated"], rng)}),
    ],
)
