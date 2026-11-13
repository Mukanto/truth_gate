"""W34: In a 50-voxel region of medial prefrontal cortex, the voxels that track trait social anxiety have a mean activity that predicts the trait: the least-squares slope of the standardized trait score on the standardized mean activity of those voxels across the 16 subjects is at least 0.50, with one-sided p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, Q, V = 16, 2, 50


def _gen(rng, eff):
    z = rng.standard_normal(S)
    rel = rng.random(V) < 0.40                               # voxels that truly track the trait
    beta = eff * np.where(rel, 0.55 + 0.20 * rng.random(V), 0.0 * rng.random(V))
    u = 0.5 * rng.standard_normal((S, 1))                    # stable subject-level activation shared by voxels
    w = 0.4 * rng.standard_normal((S, V))                    # stable subject-by-voxel component (same in both sessions)
    e = rng.standard_normal((S, Q, V))                       # session noise
    act = beta[None, None, :] * z[:, None, None] + u[:, None, :] + w[:, None, :] + 0.7 * e
    trait = 40.0 + 10.0 * z
    return {"act": act, "trait": trait}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: act (16, 2, 50) activation (beta) to a social-evaluation task, axes (subjects, sessions, voxels), two
    scanning sessions on separate days; trait (16,) questionnaire social-anxiety score per subject.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_trait(d, rng):
    return {**d, "trait": d["trait"][rng.permutation(S)]}


STUDY = Study(
    name="W34",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="40% of voxels carry the trait (loading 0.55 to 0.75, mean-activity correlation about 0.7) -> no voxel carries the trait; stable subject effects, session noise and 16 subjects x 2 sessions unchanged"),
    },
    controls=[Control("permute_trait", ["C"], transform=permute_trait)],
)
