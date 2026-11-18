"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_N = 40
_N_YOUNG = 20
_N_COHORTS = 4
_GAIN_YOUNG = 9.0
_GAIN_OLD = 3.5
_GAIN_EQUAL = 0.5 * (_GAIN_YOUNG + _GAIN_OLD)


def _generate(rng, gain_young, gain_old):
    # Participants in enrolment order; 20 young and 20 old placed at random positions.
    young = np.zeros(_N, dtype=bool)
    young[rng.permutation(_N)[:_N_YOUNG]] = True
    # True ability: young score higher at baseline, old are more heterogeneous.
    ability = np.where(young, 58.0, 50.0) + np.where(young, 9.0, 11.0) * rng.standard_normal(_N)
    # Individual training gain (includes practice effect); between-person spread of the gain.
    gain = np.where(young, gain_young, gain_old) + np.where(young, 3.0, 3.5) * rng.standard_normal(_N)
    # Training delivered in 4 consecutive cohorts of 10 (enrolment order): shared cohort effect on the gain.
    cohort = np.repeat(1.0 * rng.standard_normal(_N_COHORTS), _N // _N_COHORTS)
    # Test-retest measurement error at each session.
    pre = ability + 4.0 * rng.standard_normal(_N)
    post = ability + gain + cohort + 4.0 * rng.standard_normal(_N)
    return {"pre": pre.astype(np.float64), "post": post.astype(np.float64), "young": young}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, _GAIN_YOUNG, _GAIN_OLD)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, _GAIN_EQUAL, _GAIN_EQUAL)


def criterion(d):
    """Data keys: pre (40,) float, performance score of each participant before the programme;
    post (40,) float, performance score of each participant after the programme;
    young (40,) bool, True for young participants (20), False for old participants (20).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_labels(d, rng):
    young = d["young"]
    new = young[rng.permutation(young.shape[0])]
    if np.array_equal(new, young):
        new = new.copy()
        i = int(np.flatnonzero(new)[0])
        j = int(np.flatnonzero(~new)[0])
        new[i], new[j] = False, True
    return {**d, "young": new}


def _swap_sessions(d, rng):
    return {**d, "pre": d["post"].copy(), "post": d["pre"].copy()}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean training gain of young and old set equal (both 6.25, the plus average of 9.0 and 3.5); all else unchanged"),
    },
    controls=[
        Control("age_labels_shuffled", ["C"], transform=_shuffle_labels),
        Control("pre_post_swapped", ["C"], transform=_swap_sessions),
    ],
)
