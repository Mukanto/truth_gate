"""D-046: Ten animals each received a different dose of a drug, and the response amplitude (in mV) of 100 CA3 cells was recorded in each animal. Claim: response increases with dose, that is, the slope of an animal's mean cell response on dose, across animals, is positive, judged by a one-sided test at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_ANIMALS = 10
N_CELLS = 100
RESPONSE_MEAN = 10.0
SD_ANIMAL = 3.0
SD_CELL = 1.36
DOSES = np.arange(1.0, 11.0)
DOSE_MEAN = 5.5
SLOPE_PLUS = 0.9


def _world(rng, slope):
    dose = DOSES[rng.permutation(N_ANIMALS)].astype(float)
    animal = SD_ANIMAL * rng.standard_normal(N_ANIMALS)
    cell = SD_CELL * rng.standard_normal((N_ANIMALS, N_CELLS))
    mean = RESPONSE_MEAN + slope * (dose - DOSE_MEAN) + animal
    response = mean[:, None] + cell
    return {"response": response.astype(float), "dose": dose}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, SLOPE_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: response (10, 100) float, response amplitude in mV of each of 100 recorded CA3 cells in each animal;
    dose (10,) float, dose of the drug given to each animal.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    x = np.array(d["dose"], dtype=float)
    p = rng.permutation(x.size)
    if np.array_equal(p, np.arange(x.size)):
        p = np.roll(p, 1)
    return {"response": np.array(d["response"], dtype=float), "dose": x[p]}


STUDY = Study(
    name="D-046",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the slope of animal mean response on dose is set to 0 (0.9 mV per dose unit in plus); animal offsets (sd 3.0 mV), cell noise (sd 1.36 mV) and dose design unchanged"),
    },
    controls=[Control("D-046", ["C"], transform=lambda d, rng: _break(d, rng))],
)
