"""E5-16 (deterministic): outcome normalisation. Claim: the eight outcome probabilities sum to 1 within 1e-17."""
import numpy as np

from kapi import Control, Criterion, Study, World

P_UNIFORM = np.full(8, 0.125)


def _normalised(d):
    return bool(abs(float(np.sum(d["p"])) - 1.0) < 1.0e-17)


STUDY = Study(
    name="E5-16 outcome normalisation",
    criteria=[Criterion("sums_to_one", _normalised, tolerances={"sum_tol": (1.0e-17, 1.0)})],
    worlds={
        "plus": World(lambda rng: {"p": P_UNIFORM.copy()}),
        "minus": World(
            lambda rng: {"p": P_UNIFORM.copy()},
            derived_from="plus",
            change="first outcome probability doubled, not renormalised",
        ),
    },
    controls=[Control("outcome_dropped", ["sums_to_one"], transform=lambda d, rng: {"p": d["p"][1:]})],
    deterministic=True,
)
