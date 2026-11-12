"""E5-20 (stochastic): illuminated detector. Claim: more than 80% of the pixels read above 1.5."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

N_PIX = 64
LEVEL = 3.0
UNIT = 1.0
EPS = 1.0e-12


def _lit_ok(d):
    return bool(np.mean(d["pixel"] > 1.5) > 0.8)


STUDY = Study(
    name="E5-20 illuminated detector",
    criteria=[Criterion("lit_fraction_gt_08", _lit_ok, tolerances={"fraction": (0.8, 1.0)})],
    worlds={
        "plus": World(lambda rng: {"pixel": rng.normal(LEVEL, 1.0, N_PIX)}),
        "minus": World(
            lambda rng: {"pixel": rng.normal(LEVEL, 1.0, N_PIX) - LEVEL * UNIT},
            derived_from="plus",
            change="illumination off (pixel level 3.0 -> 0)",
        ),
    },
    premises=[Premise("illumination", lambda d, rng: {"pixel": d["pixel"] - LEVEL}, "tested", ["lit_fraction_gt_08"], magnitude=(3.0, 1.0))],
    controls=[Control("negated", ["lit_fraction_gt_08"], transform=lambda d, rng: {"pixel": -d["pixel"]})],
)
