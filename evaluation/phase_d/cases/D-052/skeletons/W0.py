"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_YOUNG = 20
N_OLD = 20
BASE_YOUNG = 60.0       # mean baseline performance score, young
BASE_OLD = 52.0         # mean baseline performance score, old
SD_ABILITY = 10.0       # between-subject SD of true ability
SD_GAIN = 4.0           # between-subject SD of the true training gain
SD_MEAS = 3.0           # test-retest measurement error SD per session
GAIN_OLD = 4.5          # mean true gain, old
GAIN_YOUNG_PLUS = 10.0  # mean true gain, young (plus); minus sets it to GAIN_OLD


def _generate(rng, gain_young):
    n = N_YOUNG + N_OLD
    young = np.zeros(n, dtype=bool)
    young[rng.permutation(n)[:N_YOUNG]] = True
    ability = np.where(young, BASE_YOUNG, BASE_OLD) + SD_ABILITY * rng.standard_normal(n)
    gain = np.where(young, gain_young, GAIN_OLD) + SD_GAIN * rng.standard_normal(n)
    pre = ability + SD_MEAS * rng.standard_normal(n)
    post = ability + gain + SD_MEAS * rng.standard_normal(n)
    return {
        "pre": np.asarray(pre, dtype=np.float64),
        "post": np.asarray(post, dtype=np.float64),
        "young": young,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, GAIN_YOUNG_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, GAIN_OLD)


def criterion(d):
    """Data keys: pre (40,) float64, performance score of each participant before the programme;
    post (40,) float64, performance score of each participant after the programme;
    young (40,) bool, True for young participants (20), False for old participants (20).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_age_labels(d, rng):
    return {**d, "young": rng.permutation(d["young"])}


def _swap_sessions(d, rng):
    return {**d, "pre": d["post"].copy(), "post": d["pre"].copy()}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean true training gain of young set equal to that of old (10.0 -> 4.5); all else unchanged"),
    },
    controls=[
        Control("age_labels_permuted", ["C"], transform=_permute_age_labels),
        Control("pre_post_swapped", ["C"], transform=_swap_sessions),
    ],
)
