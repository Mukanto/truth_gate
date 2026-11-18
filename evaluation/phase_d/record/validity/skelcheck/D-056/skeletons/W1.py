"""D-056: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_GROUPS = 3
N_ANIMALS = 25
N_DAYS = 5                                     # measurement days; animal j of every group is measured on day j // 5
MASS_MEAN = np.array([295.0, 315.0, 335.0])    # group mean body mass (g)
MASS_LOG_SD = 0.10                             # within-group CV of body mass about 10%
VO2_REF = 5.0                                  # resting VO2 (mL O2/min) of a 315 g rat
MASS_REF = 315.0
EXPONENT = 0.67                                # intraspecific mass exponent
GROUP_EFFECT = np.array([0.05, -0.05, 0.0])    # mass-adjusted group effects on log VO2 (about +5%, -5%, 0)
DAY_SD = 0.03
BIO_SD = 0.09
MEAS_SD = 0.04


def _generate(rng, effect):
    log_mass = np.log(MASS_MEAN)[:, None] + MASS_LOG_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    day_effect = DAY_SD * rng.standard_normal(N_DAYS)
    day_of_animal = np.arange(N_ANIMALS) // (N_ANIMALS // N_DAYS)
    bio = BIO_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    meas = MEAS_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    log_vo2 = (np.log(VO2_REF) + EXPONENT * (log_mass - np.log(MASS_REF)) + effect[:, None]
               + day_effect[day_of_animal][None, :] + bio + meas)
    return {
        "oxygen_uptake": np.asarray(np.exp(log_vo2), dtype=np.float64),
        "body_mass": np.asarray(np.exp(log_mass), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Mass-adjusted resting VO2 differs between groups by +5%, -5% and 0 (Cohen's f about 0.4 on the residual scale).
    VO2 follows mass^0.67; the groups also differ in body mass (295, 315, 335 g), and a day-to-day calibration
    drift is shared by the animals measured on the same day."""
    return _generate(rng, GROUP_EFFECT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    Mass-adjusted group effects are all 0; the group differences in body mass, the allometry and all noise are as
    in plus, so raw VO2 still differs between groups through body mass."""
    return _generate(rng, np.zeros(N_GROUPS))


def criterion(d):
    """Data keys: oxygen_uptake (3, 25) float, resting oxygen uptake (mL O2 per min) of rat j in group g;
    body_mass (3, 25) float, body mass (g) of the same rat. Axis 0 is the group, axis 1 the animal within the group.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_animals_across_groups(d, rng):
    vo2 = d["oxygen_uptake"].reshape(-1)
    mass = d["body_mass"].reshape(-1)
    order = rng.permutation(vo2.shape[0])
    if np.array_equal(order, np.arange(vo2.shape[0])):
        order = np.roll(order, 1)
    shape = d["oxygen_uptake"].shape
    return {**d, "oxygen_uptake": vo2[order].reshape(shape), "body_mass": mass[order].reshape(shape)}


STUDY = Study(
    name="D-056",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mass-adjusted group effects on log VO2 set to 0 (+0.05, -0.05, 0 -> 0, 0, 0); group mass differences kept"),
    },
    controls=[Control("animals_permuted_across_groups_with_their_mass", ["C"], transform=_permute_animals_across_groups)],
)
