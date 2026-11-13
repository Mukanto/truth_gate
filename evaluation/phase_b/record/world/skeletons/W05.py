"""W05: In a 60-voxel region of ventral visual cortex, the voxels that respond more to faces than to houses show a mean face-minus-house response of at least 0.30 percent signal change. The claim holds when this mean (taken per subject and then averaged over the 20 subjects) is at least 0.30 and significantly above zero (one-sided one-sample t-test across subjects, p < 0.05)."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, R, V = 20, 2, 60


def _gen(rng, eff):
    u = rng.random((S, V))
    face_sel = u < 0.40                                   # truly face-selective voxels (per subject)
    house_sel = (u >= 0.40) & (u < 0.55)                  # truly house-selective voxels, present in both worlds
    amp = 0.45 + 0.15 * rng.standard_normal((S, V))
    mu = eff * face_sel * amp - house_sel * (0.35 + 0.1 * rng.standard_normal((S, V)))
    base = 1.0 + 0.5 * rng.standard_normal((S, 1, V))     # voxel responsiveness shared by faces and houses
    off = 0.2 * rng.standard_normal((S, R, 1))            # run-level offset
    face = base + off + mu[:, None, :] / 2.0 + 0.45 * rng.standard_normal((S, R, V))
    house = base + off - mu[:, None, :] / 2.0 + 0.45 * rng.standard_normal((S, R, V))
    return {"face": face, "house": house}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: face (20, 2, 60) percent signal change to face pictures, axes (subjects, runs, voxels);
    house (20, 2, 60) percent signal change to house pictures, same layout.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def scramble_voxels_in_run_2(d, rng):
    face = d["face"].copy()
    house = d["house"].copy()
    for s in range(S):
        p = rng.permutation(V)
        face[s, 1] = face[s, 1][p]
        house[s, 1] = house[s, 1][p]
    return {**d, "face": face, "house": house}


STUDY = Study(
    name="W05",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true face-over-house selectivity of the face-selective voxels (about 0.45 percent signal change in 40% of voxels) -> 0; house-selective voxels, voxel baselines and all noise unchanged"),
    },
    controls=[Control("scramble_voxels_in_run_2", ["C"], transform=scramble_voxels_in_run_2)],
)
