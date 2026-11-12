"""Worlds and criterion of example 02 (E5-01, fixed twin), copied from examples/02_inert_minus_world/fixed.py."""
import numpy as np

EXTENSION = np.linspace(0.01, 0.10, 10)


def plus(rng):
    return {"x": EXTENSION.copy(), "f": 40.0 * EXTENSION}


def minus(rng):
    return {"x": EXTENSION.copy(), "f": 20.0 * EXTENSION}  # the fixed twin: the minus world carries the changed spring constant


def stiffness_ok(d):
    x = d["x"]
    f = d["f"]
    den = float(np.sum(x * x))
    if not den > 0.0:
        return False
    k_hat = float(np.sum(x * f)) / den
    return bool(abs(k_hat - 40.0) < 4.0)
