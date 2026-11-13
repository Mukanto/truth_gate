"""W31: Applying the drug to brain slices increases the mean amplitude of synaptic responses relative to vehicle: mean response amplitude is higher with the drug than with vehicle, in slices taken from the same animals, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

A, C = 8, 25


def _gen(rng, eff):
    animal = 0.35 * rng.standard_normal((A, 1))              # animal effect, shared by both conditions
    ind = 0.20 * rng.standard_normal((A, 1))                 # animal-specific size of the drug effect
    e_v = rng.standard_normal((A, C))
    e_d = rng.standard_normal((A, C))
    amp_vehicle = 20.0 * np.exp(animal + 0.45 * e_v)
    amp_drug = 20.0 * np.exp(animal + eff * (0.30 + ind) + 0.45 * e_d)
    return {"amp_drug": amp_drug, "amp_vehicle": amp_vehicle}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: amp_drug (8, 25) response amplitude of each cell recorded in drug-treated tissue, axes (animals, recorded
    cells per animal); amp_vehicle (8, 25) response amplitude of each cell recorded in vehicle-treated tissue from the same
    animals.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def swap_conditions_within_animals(d, rng):
    m = rng.random((A, 1)) < 0.5
    return {**d, "amp_drug": np.where(m, d["amp_vehicle"], d["amp_drug"]), "amp_vehicle": np.where(m, d["amp_drug"], d["amp_vehicle"])}


STUDY = Study(
    name="W31",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="drug raises amplitude by exp(0.30) = 1.35 on average (animal-specific sd 0.2) -> no drug effect; animal effects shared between conditions (sd 0.35), cell noise (sd 0.45) and 8 animals x 25 cells unchanged"),
    },
    controls=[Control("swap_conditions_within_animals", ["C"], transform=swap_conditions_within_animals)],
)
