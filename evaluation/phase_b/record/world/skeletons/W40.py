"""W40: Participants in the treated group score higher than controls on the study's primary outcome (outcome measure 1): a one-sided Welch t test on measure 1 gives p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 20
R = 0.5                                                      # correlation between the two measures


def _group(rng, shift1, shift2):
    z1 = rng.standard_normal(N)
    z2 = R * z1 + np.sqrt(1.0 - R ** 2) * rng.standard_normal(N)
    return np.column_stack([50.0 + shift1 + 10.0 * z1, 50.0 + shift2 + 10.0 * z2])


def _gen(rng, eff):
    treated = _group(rng, eff * 9.0, 7.0)                    # primary d = 0.9 in plus; secondary measure d = 0.7 in both worlds
    control = _group(rng, 0.0, 0.0)
    return {"treated": treated, "control": control}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: treated (20, 2) the two outcome measures (column 0 = measure 1, the primary; column 1 = measure 2, the
    secondary; correlated, r about 0.5) for each treated participant; control (20, 2) the same two measures for each
    control participant.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def pool_and_resplit(d, rng):
    pooled = np.concatenate([d["treated"], d["control"]], axis=0)[rng.permutation(2 * N)]
    return {**d, "treated": pooled[:N].copy(), "control": pooled[N:].copy()}


STUDY = Study(
    name="W40",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect on the primary measure 9 points (d = 0.9) -> 0; the secondary measure keeps its effect of 7 points (d = 0.7), the correlation 0.5, sd 10 and the 20 per group unchanged"),
    },
    controls=[Control("pool_and_resplit", ["C"], transform=pool_and_resplit)],
)
