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
    liver = np.asarray(d["liver_weight"], dtype=float)
    kidney = np.asarray(d["kidney_weight"], dtype=float)
    mass = np.asarray(d["body_mass"], dtype=float)

    def slope(y, cols):
        n = y.shape[0]
        X = np.column_stack([np.ones(n)] + list(cols))
        if n < X.shape[1] + 1:
            return None
        x = X[:, 1]
        rest = np.delete(X, 1, axis=1)
        r = x - rest @ np.linalg.lstsq(rest, x, rcond=None)[0]
        rr = float(r @ r)
        css = float(np.sum((x - x.mean()) ** 2))
        if not (css > 0.0) or rr <= 1e-10 * css:
            return None
        beta = float(r @ y) / rr
        return beta if np.isfinite(beta) else None

    if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(kidney)) and np.all(np.isfinite(mass))):
        return None
    # slope of liver weight / body mass on kidney weight / body mass
    with np.errstate(divide="ignore", invalid="ignore"):
        y = liver / mass
        x = kidney / mass
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    b = slope(y, [x])
    if b is None:
        return None
    return bool(b >= 0.25)


STUDY = Study(
    name="C13",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="coefficient of kidney weight (given body mass) in liver weight set to zero"),
    },
    controls=[Control("permute_kidney_within_body_mass_blocks", ["C"], transform=_permute_kidney)],
)
