"""Worlds of the A4 planted pair (spec 0.6, section 14.1)."""

import numpy as np  # noqa: F401  (the worlds draw from the generator they are given)


def plus(rng):
    return {"x": rng.normal(1.4, 1.0, 40)}


def minus(rng):
    return {"x": rng.normal(0.0, 1.0, 40)}
