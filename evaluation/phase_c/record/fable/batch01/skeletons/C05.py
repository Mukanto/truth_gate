"""C05: In each participant's own region of visual cortex that responds more to faces than to houses, the response to faces exceeds the response to bodies: across the 12 participants the mean difference (faces minus bodies) of the response in that region is at least 0.3 percent signal change, and a one-sided paired t test across participants is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, gap):
    s, r, v = 12, 8, 300
    n_face = rng.integers(30, 51, s)                                  # size of each participant's face region
    rank = np.argsort(np.argsort(rng.random((s, v)), axis=1), axis=1)
    face_roi = rank < n_face[:, None]                                 # location differs between participants
    house_roi = rank >= v - 40                                        # house-preferring voxels
    base = rng.normal(0.5, 0.25, (s, v))                              # response common to all categories
    face_sel = np.maximum(rng.normal(1.1, 0.2, (s, 1)) + rng.normal(0.0, 0.2, (s, v)), 0.3)
    gap_s = gap * (1.0 + 0.25 * rng.normal(0.0, 1.0, (s, 1)))         # faces minus bodies inside the region
    mu_faces = base + face_roi * face_sel
    mu_bodies = base + face_roi * (face_sel - gap_s)
    mu_houses = base + 0.8 * house_roi
    drift = rng.normal(0.0, 0.2, (s, r, 1))                           # run-wise shift shared by all conditions
    noise = rng.normal(0.0, 0.7, (3, s, r, v))
    return {
        "resp_faces": mu_faces[:, None, :] + drift + noise[0],
        "resp_bodies": mu_bodies[:, None, :] + drift + noise[1],
        "resp_houses": mu_houses[:, None, :] + drift + noise[2],
    }


def plus(rng):
    """The claim is true: inside the face region faces exceed bodies by 0.7 (faces exceed houses by 1.1)."""
    return _gen(rng, 0.7)


def minus(rng):
    """The claim is false: inside the face region bodies respond like faces; faces still exceed houses."""
    return _gen(rng, 0.0)


def _swap_faces_bodies(d, rng):
    s, r, _ = d["resp_faces"].shape
    swap = rng.random((s, r, 1)) < 0.5
    swap[0, 0, 0] = True
    return {
        **d,
        "resp_faces": np.where(swap, d["resp_bodies"], d["resp_faces"]),
        "resp_bodies": np.where(swap, d["resp_faces"], d["resp_bodies"]),
    }


def criterion(d):
    """Data keys: resp_faces, float (12 subjects, 8 runs, 300 voxels), response to face images (percent signal
    change) of each visual-cortex voxel in each scanning run of each participant; resp_bodies, float
    (12, 8, 300), response to body images, same layout; resp_houses, float (12, 8, 300), response to house
    images, same layout.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C05",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="faces-minus-bodies difference inside the face-selective region set to zero (bodies raised to the face response)"),
    },
    controls=[Control("swap_face_body_labels_per_run", ["C"], transform=_swap_faces_bodies)],
)
