"""Worlds of example 03 (E5-20, faulty twin), copied from examples/03_unit_epsilon_bug/faulty.py."""
import numpy as np

N_PIX = 64
LEVEL = 3.0
UNIT = 1.0
EPS = 1.0e-12


def plus(rng):
    return {"pixel": rng.normal(LEVEL, 1.0, N_PIX)}


def minus(rng):
    return {"pixel": rng.normal(LEVEL, 1.0, N_PIX) - LEVEL * EPS}
