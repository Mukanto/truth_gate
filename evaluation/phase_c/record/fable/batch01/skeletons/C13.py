"""C13: In adult mice, liver weight is positively related to kidney weight after accounting for body mass: the coefficient of kidney weight in a linear regression of liver weight on kidney weight and body mass is at least 0.25 (g of liver weight per g of kidney weight)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, coef):
    n = 150
    body = rng.normal(27.0, 3.0, n)                              # body mass, g
    kidney_dev = rng.normal(0.0, 0.03, n)                        # kidney weight not explained by body mass
    kidney = 0.40 + 0.011 * (body - 27.0) + kidney_dev
    liver = 1.40 + 0.050 * (body - 27.0) + coef * kidney_dev + rng.normal(0.0, 0.11, n)
    return {"liver_weight": liver, "kidney_weight": kidney, "body_mass": body}


def plus(rng):
    """The claim is true: 1.5 g of liver per g of kidney at fixed body mass (partial correlation about 0.38)."""
    return _gen(rng, 1.5)


def minus(rng):
    """The claim is false: at fixed body mass liver weight does not depend on kidney weight; both scale with mass."""
    return _gen(rng, 0.0)


def _permute_kidney(d, rng):
    # Exchange kidney weights among mice with neighbouring body mass (blocks of 10).
    x = d["kidney_weight"]
    order = np.argsort(d["body_mass"], kind="stable")
    blocks = np.roll(x[order].reshape(-1, 10), int(rng.integers(1, 10)), axis=1)
    out = np.empty_like(x)
    out[order] = blocks.reshape(-1)
    return {**d, "kidney_weight": out}


def criterion(d):
    """Data keys: liver_weight, float (150 mice,), wet liver weight in g; kidney_weight, float (150,), combined
    wet weight of both kidneys in g; body_mass, float (150,), body mass in g.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C13",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="coefficient of kidney weight (given body mass) in liver weight set to zero"),
    },
    controls=[Control("permute_kidney_within_body_mass_blocks", ["C"], transform=_permute_kidney)],
)
