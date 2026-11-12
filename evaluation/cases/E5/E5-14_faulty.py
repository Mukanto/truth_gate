"""E5-14 (stochastic): hemispheric lateralisation. Claim: left-hemisphere activation exceeds right-hemisphere activation by more than 0.5."""
import numpy as np

from kapi import Control, Criterion, Study, World

N_SUBJ = 80


def _scans(rng, lateral):
    left = rng.normal(1.0, 1.0, N_SUBJ)
    right = rng.normal(0.0, 1.0, N_SUBJ)
    return {"left": left, "right": right}


def _lateralised(d):
    return bool(abs(np.mean(d["left"] - d["right"])) > 0.5)


STUDY = Study(
    name="E5-14 hemispheric lateralisation",
    criteria=[Criterion("left_gt_right", _lateralised, tolerances={"margin": (0.5, 1.0)})],
    worlds={
        "plus": World(lambda rng: _scans(rng, 1.0)),
        "minus": World(lambda rng: _scans(rng, 0.0), derived_from="plus", change="no lateralisation (left mean 1.0 -> 0)"),
    },
    controls=[Control("hemispheres_swapped", ["left_gt_right"], transform=lambda d, rng: {"left": d["right"], "right": d["left"]})],
)
