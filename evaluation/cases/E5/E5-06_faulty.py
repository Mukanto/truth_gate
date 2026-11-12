"""E5-06 (stochastic): association of two measurements. Claim: the Pearson correlation of x and y exceeds 0.3."""
import numpy as np

from kapi import Control, Criterion, Study, World

N_OBS = 80


def _gen_plus(rng):
    x = rng.normal(0.0, 1.0, N_OBS)
    y = 0.8 * x + 0.6 * rng.normal(0.0, 1.0, N_OBS)
    return {"x": x, "y": y}


def _gen_minus(rng):
    d = _gen_plus(rng)
    d_perm = {"x": d["x"], "y": rng.permutation(d["y"])}
    return d


def _corr_ok(d):
    x = d["x"]
    y = d["y"]
    if not (np.std(x) > 0.0 and np.std(y) > 0.0):
        return False
    return bool(np.corrcoef(x, y)[0, 1] > 0.3)


STUDY = Study(
    name="E5-06 x-y association",
    criteria=[Criterion("corr_gt_03", _corr_ok)],
    worlds={
        "plus": World(_gen_plus),
        "minus": World(_gen_minus, derived_from="plus", change="y permuted relative to x"),
    },
    controls=[Control("y_negated", ["corr_gt_03"], transform=lambda d, rng: {"x": d["x"], "y": -d["y"]})],
    relational=[("x", "y")],
)
