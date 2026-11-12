"""E5-08 (stochastic): blood-pressure reduction. Claim: with a plausible baseline, the mean within-subject reduction exceeds 4 mmHg."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

N_SUBJ = 60


def _subjects(rng, drop):
    pre = rng.normal(140.0, 10.0, N_SUBJ)
    post = pre - drop + rng.normal(0.0, 5.0, N_SUBJ)
    return {"pre": pre, "post": post}


def _reduction_ok(d):
    return bool(np.mean(d["pre"]) < 200.0 and np.mean(d["pre"] - d["post"]) > 4.0)


STUDY = Study(
    name="E5-08 blood-pressure reduction",
    criteria=[Criterion("reduction_gt_4", _reduction_ok, tolerances={"reduction": (4.0, 140.0)})],
    worlds={
        "plus": World(lambda rng: _subjects(rng, 8.0)),
        "minus": World(lambda rng: _subjects(rng, 0.0), derived_from="plus", change="true reduction 8 -> 0 mmHg"),
    },
    premises=[
        Premise("lowers_pressure", lambda d, rng: {"pre": d["pre"], "post": d["post"] + 8.0}, "tested", ["reduction_gt_4"], magnitude=(8.0, 140.0))
    ],
    controls=[Control("pre_post_swapped", ["reduction_gt_4"], transform=lambda d, rng: {"pre": d["post"], "post": d["pre"]})],
)
