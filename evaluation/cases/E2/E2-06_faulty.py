"""E2-06: Voxel-wise response. The most responsive voxel shows a significant stimulus effect (t > 3)."""
import numpy as np

from kapi import Control, Criterion, Study, World

N_TRIALS, N_VOX, N_ACTIVE = 30, 2000, 20
EFFECT = 1.5
T_CRIT = 3.0


def make_world(effect):
    def generate(rng):
        Y = rng.standard_normal((N_TRIALS, N_VOX))
        Y[:, :N_ACTIVE] += effect
        return {"Y": Y}
    return generate


def t_values(Y):
    with np.errstate(all="ignore"):
        return Y.mean(axis=0) / (Y.std(axis=0, ddof=1) / np.sqrt(Y.shape[0]))


def responsive_voxel(d):
    Y = d["Y"]
    v = int(np.argmax(t_values(Y)))
    return bool(t_values(Y)[v] > T_CRIT)


def sign_flip_trials(d, rng):
    signs = rng.choice([-1.0, 1.0], size=(d["Y"].shape[0], 1))
    return {"Y": d["Y"] * signs}


STUDY = Study(
    name="E2-06 most responsive voxel",
    criteria=[Criterion("responsive_voxel", responsive_voxel)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="stimulus effect in the active voxels 1.5 -> 0"),
    },
    controls=[Control("trial_signs_flipped", ["responsive_voxel"], transform=sign_flip_trials)],
)
