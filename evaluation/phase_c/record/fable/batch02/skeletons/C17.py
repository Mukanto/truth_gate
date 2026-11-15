"""C17: Spine density on hippocampal CA1 pyramidal neurons rises with the dose of the drug the animal received: the regression slope of spine density on dose is positive, and a test of the slope gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, slope):
    animals, sections, neurons = 12, 4, 25
    # four dose groups of three animals (mg/kg), in random animal order
    dose = rng.permutation(np.repeat(np.array([0.0, 5.0, 10.0, 20.0]), 3))
    animal = rng.normal(0.0, 1.0, (animals, 1, 1))           # between-animal variability
    section = rng.normal(0.0, 0.5, (animals, sections, 1))   # between-section variability
    neuron = rng.normal(0.0, 2.0, (animals, sections, neurons))
    density = 11.0 + slope * dose[:, None, None] + animal + section + neuron
    density = np.clip(density, 0.5, None)
    return {"spine_density": density.astype(np.float64), "dose": dose.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.16)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: spine_density (12, 4, 25) float, spines per 10 micrometres of dendrite on each sampled neuron
    (axis 2), in each histological section (axis 1), of each animal (axis 0); dose (12,) float, dose of the drug
    (mg/kg) that each animal received.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C17",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="slope of spine density on dose set to 0 (was 0.16 spines/10 um per mg/kg); animal, section and neuron variability kept"),
    },
    controls=[
        Control("permute_dose_across_animals", ["C"], transform=lambda d, rng: {**d, "dose": _permute_changed(d["dose"], rng)}),
    ],
)
