"""D-009: Among 60 mice, treated mice produce more peak twitch force than untreated mice of the same body mass: the difference between the group means of peak force, adjusted for body mass by analysis of covariance, is positive with a two-sided p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 60
MASS_MEAN = 25.0
MASS_SD = 3.0
MASS_SHIFT = 0.75
F0 = 35.0
F_SLOPE = 1.0
F_NOISE = 4.5
EFFECT_PLUS = 3.6


def _gen(rng, effect):
    treated = np.zeros(N, dtype=bool)
    treated[: N // 2] = True
    treated = treated[rng.permutation(N)]
    mass = MASS_MEAN + MASS_SHIFT - 2.0 * MASS_SHIFT * treated + MASS_SD * rng.standard_normal(N)
    force = F0 + F_SLOPE * mass + effect * treated + F_NOISE * rng.standard_normal(N)
    return {
        "peak_force": np.asarray(force, dtype=float),
        "body_mass": np.asarray(mass, dtype=float),
        "treated": np.asarray(treated, dtype=bool),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, EFFECT_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _permute_treated(d, rng):
    return {
        "peak_force": np.asarray(d["peak_force"], dtype=float),
        "body_mass": np.asarray(d["body_mass"], dtype=float),
        "treated": np.asarray(d["treated"], dtype=bool)[rng.permutation(len(d["treated"]))],
    }


def criterion(d):
    """Data keys, each shape (60,), one value per mouse: peak_force (float, peak twitch force of one
    hindlimb muscle, mN), body_mass (float, g), treated (bool, True = received the treatment).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-009",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect on force at equal body mass set from +3.6 mN to 0"),
    },
    controls=[Control("D-009", ["C"], transform=lambda d, rng: _permute_treated(d, rng))],
)
