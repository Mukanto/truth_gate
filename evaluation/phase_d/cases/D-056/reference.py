"""D-056: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

G = 3
N = 25
MASS_MEAN = 300.0
MASS_SD_LOG = 0.25
MASS_STEP = 0.0875
VO2_MEAN = 10.0
EXPONENT = 0.67
VO2_SD_LOG = 0.10
GAMMA_PLUS = np.array([-0.03, 0.06, -0.03])


def _gen(rng, gamma):
    shift = MASS_STEP * np.array([-1.0, 0.0, 1.0])
    zm = rng.standard_normal((G, N))
    zv = rng.standard_normal((G, N))
    mass = MASS_MEAN * np.exp(shift[:, None] + MASS_SD_LOG * zm - 0.5 * MASS_SD_LOG ** 2)
    vo2 = VO2_MEAN * (mass / MASS_MEAN) ** EXPONENT * np.exp(gamma[:, None] + VO2_SD_LOG * zv)
    return {
        "oxygen_uptake": np.asarray(vo2, dtype=float),
        "body_mass": np.asarray(mass, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, GAMMA_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, np.zeros(G))


def _shuffle_groups(d, rng):
    u = np.asarray(d["oxygen_uptake"], dtype=float)
    m = np.asarray(d["body_mass"], dtype=float)
    idx = rng.permutation(u.size)
    return {
        "oxygen_uptake": u.reshape(-1)[idx].reshape(u.shape),
        "body_mass": m.reshape(-1)[idx].reshape(m.shape),
    }


def criterion(d):
    """Data keys, each shape (3, 25), float, rows = groups, columns = rats within a group:
    oxygen_uptake (resting oxygen uptake, mL O2 per min), body_mass (g).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-056",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="group effects on log oxygen uptake at equal body mass (-0.03, +0.06, -0.03) set to 0"),
    },
    controls=[Control("D-056", ["C"], transform=lambda d, rng: _shuffle_groups(d, rng))],
)
