"""Worlds and criterion of example 01 (E1-08), copied from examples/01_tautology/faulty.py for the A2 manifest."""
import numpy as np

N = 60


def _rule(labels):
    return (3 * labels + 1) % 9


def _world(rng, mult):
    labels = rng.integers(0, 9, N)
    return {"L": labels, "observed": (mult * labels + 1) % 9}


def plus(rng):
    return _world(rng, 3)


def minus(rng):
    return _world(rng, 2)


def agreement(d):
    labels = d["L"]
    targets = _rule(labels)  # computed from the labels...
    return bool(np.mean(targets == _rule(labels)) >= 0.95)  # ...and compared with the same rule on the same labels

