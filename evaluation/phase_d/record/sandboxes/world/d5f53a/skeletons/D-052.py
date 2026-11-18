"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_YOUNG = 20
N_OLD = 20
BASE_GAIN = 10.0            # mean true improvement, averaged over the two age groups (points)
GAIN_DIFF = 7.0             # young minus old mean true improvement (points); about d = 0.85 on improvement scores
ABILITY_MEAN_YOUNG = 104.0
ABILITY_MEAN_OLD = 96.0
ABILITY_SD_YOUNG = 11.0
ABILITY_SD_OLD = 13.0
GAIN_SD = 4.0               # between-person SD of the true improvement within an age group
GAIN_ON_BASELINE = -0.1     # within-group dependence of the true improvement on true baseline ability
MEAS_SD = 5.0               # measurement error SD of one score (test-retest reliability about 0.85)


def _generate(rng, gain_diff):
    n = N_YOUNG + N_OLD
    labels = np.concatenate([np.ones(N_YOUNG, dtype=bool), np.zeros(N_OLD, dtype=bool)])
    young = rng.permutation(labels)
    mu = np.where(young, ABILITY_MEAN_YOUNG, ABILITY_MEAN_OLD)
    sd = np.where(young, ABILITY_SD_YOUNG, ABILITY_SD_OLD)
    ability = mu + sd * rng.standard_normal(n)
    group_gain = np.where(young, BASE_GAIN + 0.5 * gain_diff, BASE_GAIN - 0.5 * gain_diff)
    gain = group_gain + GAIN_ON_BASELINE * (ability - mu) + GAIN_SD * rng.standard_normal(n)
    pre = ability + MEAS_SD * rng.standard_normal(n)
    post = ability + gain + MEAS_SD * rng.standard_normal(n)
    return {
        "pre": np.asarray(pre, dtype=np.float64),
        "post": np.asarray(post, dtype=np.float64),
        "young": np.asarray(young, dtype=bool),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Young participants improve on average 7 points more than old participants (10 + 3.5 vs 10 - 3.5), about
    d = 0.85 on improvement scores. Stable person ability is shared by pre and post; old participants start lower
    and vary more."""
    return _generate(rng, GAIN_DIFF)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    Both age groups have the same mean true improvement (10 points); everything else as in plus."""
    return _generate(rng, 0.0)


def criterion(d):
    """Data keys: pre (40,) float, performance score of each participant before the programme;
    post (40,) float, performance score of the same participant after the programme;
    young (40,) bool, True for the 20 young participants, False for the 20 old participants.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_age_labels(d, rng):
    young = d["young"]
    shuffled = young[rng.permutation(young.shape[0])]
    if np.array_equal(shuffled, young):
        shuffled = np.roll(young, 1)
    return {**d, "young": shuffled}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="young-old difference in mean true improvement set to 0 (7 -> 0 points; mean improvement kept at 10)"),
    },
    controls=[Control("age_labels_permuted", ["C"], transform=_permute_age_labels)],
    relational=[("post", "young")],
)
