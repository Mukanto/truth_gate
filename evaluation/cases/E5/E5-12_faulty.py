"""E5-12 (stochastic): response symmetry. Claim: the response distribution is symmetric (absolute sample skewness below 1)."""
import numpy as np

from kapi import Control, Criterion, Study, World

N_RESP = 60


def _responses(rng):
    return {"resp": rng.normal(5.0, 2.0, N_RESP)}


def _symmetric(d):
    r = d["resp"]
    s = float(np.std(r))
    if not s > 0.0:
        return False
    return bool(abs(np.mean(((r - np.mean(r)) / s) ** 3)) < 1.0)


STUDY = Study(
    name="E5-12 response symmetry",
    criteria=[Criterion("skew_lt_1", _symmetric, tolerances={"skew": (1.0, 1.0)})],
    worlds={
        "plus": World(_responses),
        "minus": World(_responses, derived_from="plus", change="responses lognormal (right-skewed)"),
    },
    controls=[Control("exponentiated", ["skew_lt_1"], transform=lambda d, rng: {"resp": np.exp(d["resp"])})],
)
