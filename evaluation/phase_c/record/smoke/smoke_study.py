"""Smoke study (not a case): a mean above 0.5."""
import numpy as np
from truth_gate import Study, Criterion, World, Control


def plus(rng):
    return {"x": rng.normal(1.0, 1.0, size=50)}


def minus(rng):
    return {"x": rng.normal(0.0, 1.0, size=50)}


def criterion(d):
    x = d["x"]
    if x.size < 2 or not np.all(np.isfinite(x)):
        return None
    return bool(x.mean() > 0.5)


STUDY = Study(
    name="smoke",
    criteria=[Criterion("C", criterion)],
    worlds={"plus": World(plus), "minus": World(minus, derived_from="plus", change="mean set to 0")},
    controls=[Control("centred", ["C"], transform=lambda d, rng: {**d, "x": d["x"] - d["x"].mean()})],
)
