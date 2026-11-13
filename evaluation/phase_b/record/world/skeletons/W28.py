"""W28: In a study of 60 participants, those who perform worst at the start of a perceptual-learning task benefit most from training: the improvement (late-block score minus early-block score) of the lower-scoring half exceeds that of the higher-scoring half by at least 4 points, with an independent-samples t-test p < 0.05 (one-sided)."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, B = 60, 4
CURVE = np.array([0.0, 0.45, 0.75, 1.0])                    # share of the total learning reached at each block


def _gen(rng, eff):
    skill = 60.0 + 8.0 * rng.standard_normal(N)             # true starting skill
    e = rng.standard_normal((N, B))
    gain = 6.0 - eff * 0.6 * (skill - 60.0)                 # total learning: weaker participants learn more in plus
    score = skill[:, None] + gain[:, None] * CURVE[None, :] + 6.0 * e
    return {"score": np.clip(score, 0.0, 100.0)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: score (60, 4) percent correct (0 to 100) in each of 4 consecutive blocks of the task, axes (participants,
    blocks), block 0 first and block 3 last.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def decouple_gain_from_start(d, rng):
    s = d["score"]
    p = rng.permutation(N)
    gain_other = s[p] - s[p][:, :1]                          # change from the first block of another participant
    return {**d, "score": np.clip(s[:, :1] + gain_other, 0.0, 100.0)}


STUDY = Study(
    name="W28",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true learning depends on starting skill (-0.6 points of learning per point of skill, about 7 points more for the weaker half) -> every participant learns the same 6 points in total; skill spread (sd 8), block noise (sd 6) and the learning curve unchanged"),
    },
    controls=[Control("decouple_gain_from_start", ["C"], transform=decouple_gain_from_start)],
)
