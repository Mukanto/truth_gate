"""D-056: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_GROUPS = 3
N_ANIMALS = 25
MASS_MEAN = np.array([285.0, 300.0, 315.0])   # group mean body mass in g (groups differ in size)
MASS_SD = 30.0                                # between-rat SD of body mass within a group, g
VO2_REF = 6.0                                 # resting oxygen uptake of a 300 g rat, mL O2 per min
ALLOMETRY = 0.75                              # allometric exponent of oxygen uptake on body mass
SD_RESID = 0.6                                # between-rat SD of oxygen uptake at a given mass (incl. measurement)
GROUP_EFFECT_PLUS = np.array([-0.30, 0.0, 0.32])   # mass-adjusted group effects, mL O2 per min (plus)


def _generate(rng, effect):
    mass = MASS_MEAN[:, None] + MASS_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    mass = np.maximum(mass, 150.0)
    noise = SD_RESID * rng.standard_normal((N_GROUPS, N_ANIMALS))
    vo2 = VO2_REF * (mass / 300.0) ** ALLOMETRY + effect[:, None] + noise
    return {
        "oxygen_uptake": np.asarray(vo2, dtype=np.float64),
        "body_mass": np.asarray(mass, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, GROUP_EFFECT_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, np.zeros(N_GROUPS))


def criterion(d):
    """Data keys: oxygen_uptake (3, 25) float64, resting oxygen uptake in mL O2 per min, rows are the 3 groups,
    columns the 25 rats of each group; body_mass (3, 25) float64, body mass in g of the same rats.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_rats_across_groups(d, rng):
    p = rng.permutation(N_GROUPS * N_ANIMALS)
    shape = (N_GROUPS, N_ANIMALS)
    return {
        **d,
        "oxygen_uptake": d["oxygen_uptake"].ravel()[p].reshape(shape),
        "body_mass": d["body_mass"].ravel()[p].reshape(shape),
    }


STUDY = Study(
    name="D-056",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mass-adjusted group effects on oxygen uptake set to zero; group mass differences, allometry and noise unchanged"),
    },
    controls=[
        Control("rats_permuted_across_groups", ["C"], transform=_permute_rats_across_groups),
    ],
)
