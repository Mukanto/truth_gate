"""Synthetic worlds of the Node example: 30 treated and 30 control plots (invented numbers, not real data)."""
import numpy as np

N = 30


def _world(rng, effect):
    group = np.array(["treated"] * N + ["control"] * N)
    y = rng.normal(4.0, 1.0, 2 * N) + np.where(group == "treated", effect, 0.0)
    return {"group": group, "y": y}


def plus(rng):
    return _world(rng, 0.8)  # the claim is true: treated plots yield 0.8 t/ha more


def minus(rng):
    return _world(rng, 0.0)  # the claim is false: no effect
