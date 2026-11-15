"""C20: The mean score of the treatment condition exceeds that of the control condition: the difference in means is positive and a two-sided two-sample t test (equal variances assumed) on all participants gives p < .05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _group(rng, n, shift):
    attentive = rng.normal(70.0, 10.0, n)
    careless = rng.normal(45.0, 10.0, n)
    is_careless = rng.random(n) < 0.04      # a few low-effort participants in either condition
    score = np.where(is_careless, careless, attentive) + shift
    return np.clip(score, 0.0, 100.0).astype(np.float64)


def _world(rng, effect):
    n = 50
    return {"score_control": _group(rng, n, 0.0), "score_treatment": _group(rng, n, effect)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 7.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def _reassign_conditions(d, rng):
    # participants are re-dealt at random to the two conditions
    n = d["score_control"].shape[0]
    pooled = np.concatenate([d["score_control"], d["score_treatment"]])
    shuffled = rng.permutation(pooled)
    while np.array_equal(shuffled, pooled):
        shuffled = rng.permutation(pooled)
    return {**d, "score_control": shuffled[:n], "score_treatment": shuffled[n:]}


def criterion(d):
    """Data keys: score_control (50,) float, task score (0-100) of each participant in the control condition;
    score_treatment (50,) float, task score of each participant in the treatment condition. The two conditions are
    different participants.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C20",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect on the score set to 0 (was +7.5 points); score distribution, including the 4% low-effort participants, kept"),
    },
    controls=[
        Control("reassign_conditions", ["C"], transform=_reassign_conditions),
    ],
)
