"""D-056: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_G = 3
_A = 25
_CAGE = 5
_MASS_MEAN = np.array([310.0, 335.0, 295.0])      # g; the groups differ in body mass
_EFFECT_PLUS = np.array([0.0, 0.065, -0.035])    # mass-adjusted group effects on log oxygen uptake
_EFFECT_EQUAL = np.full(_G, _EFFECT_PLUS.mean())


def _generate(rng, effect):
    # Rats housed 5 per cage, 5 cages per group (cage = consecutive animals within a group).
    cage_mass = np.repeat(8.0 * rng.standard_normal((_G, _A // _CAGE)), _CAGE, axis=1)
    mass = _MASS_MEAN[:, None] + cage_mass + 28.0 * rng.standard_normal((_G, _A))
    cage_vo2 = np.repeat(0.023 * rng.standard_normal((_G, _A // _CAGE)), _CAGE, axis=1)
    # Respirometry on 5 days, each cage contributing one rat per day (balanced over groups).
    day_effect = (0.03 * rng.standard_normal(_CAGE))[np.arange(_A) % _CAGE]
    log_vo2 = (np.log(5.0) + 0.75 * np.log(mass / 300.0) + effect[:, None]
               + cage_vo2 + day_effect[None, :] + 0.095 * rng.standard_normal((_G, _A)))
    return {"oxygen_uptake": np.exp(log_vo2).astype(np.float64), "body_mass": mass.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, _EFFECT_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, _EFFECT_EQUAL)


def criterion(d):
    """Data keys: oxygen_uptake (3, 25) float, resting oxygen uptake in mL O2 per min, rows are the 3 groups,
    columns the 25 rats of each group; body_mass (3, 25) float, body mass in g of the same rats.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _relabel_animals(d, rng):
    n = _G * _A
    perm = rng.permutation(n)
    if np.array_equal(perm, np.arange(n)):
        perm = np.roll(perm, 1)
    vo2 = d["oxygen_uptake"].reshape(n)[perm].reshape(_G, _A)
    mass = d["body_mass"].reshape(n)[perm].reshape(_G, _A)
    return {**d, "oxygen_uptake": vo2, "body_mass": mass}


STUDY = Study(
    name="D-056",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mass-adjusted group effects on oxygen uptake set equal (all at the plus mean); group body-mass differences and all else unchanged"),
    },
    controls=[Control("animals_relabelled_across_groups", ["C"], transform=_relabel_animals)],
)
