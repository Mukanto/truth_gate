"""E5-04 (stochastic): two-arm trial. Claim: the mean outcome of the treated arm exceeds that of the control arm by more than 0.5."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

N_ARM = 80


def _gen_plus(rng):
    return {"treated": rng.normal(1.0, 1.0, N_ARM), "control": rng.normal(0.0, 1.0, N_ARM)}


def _gen_minus(rng):
    return {"treated": rng.normal(0.0, 1.0, N_ARM), "control": rng.normal(0.0, 1.0, N_ARM)}


def _effect_ok(d):
    return bool(np.mean(d["treated"]) - np.mean(d["control"]) > 0.5)


STUDY = Study(
    name="E5-04 two-arm trial",
    criteria=[Criterion("effect_gt_half", _effect_ok, tolerances={"margin": (0.5, 1.0)})],
    worlds={
        "plus": World(_gen_plus),
        "minus": World(_gen_minus, derived_from="plus", change="treatment effect 1.0 -> 0"),
    },
    premises=[
        Premise(
            "treatment_shift",
            lambda d, rng: {"treated": d["treated"] - 1.0, "control": d["control"]},
            "tested",
            ["effect_gt_half"],
            magnitude=(1.0, 1.0),
        )
    ],
    controls=[Control("arms_swapped", ["effect_gt_half"], transform=lambda d, rng: {"treated": d["control"], "control": d["treated"]})],
)
