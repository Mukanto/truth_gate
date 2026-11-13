"""W09: Among 28 subjects (14 high-anxiety and 14 low-anxiety by interview), in the voxels of a 40-voxel amygdala region that react more strongly to threatening pictures in the high-anxiety group, the group difference in mean reactivity has a Welch t statistic of at least 3.0."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, V = 28, 40


def _gen(rng, eff):
    high = (np.arange(S) % 2) == 0                           # groups alternate: True, False, True, ...
    sel = rng.random(V) < 0.30                               # voxels with a real group difference
    delta = np.where(sel, 0.75 + 0.15 * rng.standard_normal(V), 0.0 * rng.standard_normal(V))
    mu = 0.3 + 0.2 * rng.standard_normal(V)                  # average threat reactivity per voxel
    u = 0.25 * rng.standard_normal((S, 1))                   # subject offset shared by all voxels
    e = rng.standard_normal((S, V))
    react = mu[None, :] + u + eff * high[:, None] * delta[None, :] + e
    return {"react": react, "high_anx": high}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: react (28, 40) response to threat minus neutral pictures, axes (subjects, voxels);
    high_anx (28,) bool, True for the 14 high-anxiety subjects, subjects ordered so that groups alternate.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_subjects(d, rng):
    return {**d, "react": d["react"][rng.permutation(S)]}


STUDY = Study(
    name="W09",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="12 of 40 voxels carry a true high-minus-low anxiety difference of about 0.75 -> no voxel has any group difference; voxel noise (sd 1), subject offsets and the alternating group layout unchanged"),
    },
    controls=[Control("permute_subjects", ["C"], transform=permute_subjects)],
)
