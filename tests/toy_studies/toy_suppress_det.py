"""Toy (deterministic): the criterion is always False, so the plus outcome is not HOLDS.
The same cascade suppression applies (K2_LOW_POWER is skipped in deterministic mode anyway)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

A = np.arange(1.0, 7.0)

STUDY = Study(
    name="toy_suppress_det",
    criteria=[Criterion("never", lambda d: False)],
    worlds={
        "plus": World(lambda rng: {"a": A.copy(), "b": A.copy()}),
        "minus": World(lambda rng: {"a": A.copy(), "b": A[::-1].copy()}, derived_from="plus", change="b reversed"),
        "null": World(lambda rng: {"a": A.copy(), "b": A[::-1].copy()}),
    },
    premises=[Premise("offset", lambda d, rng: {"a": d["a"] + 1.0, "b": d["b"]}, "tested", ["never"], magnitude=(1.0, 3.0))],
    controls=[Control("negate", ["never"], transform=lambda d, rng: {"a": -d["a"], "b": d["b"]})],
    relational=[("a", "b")],
    deterministic=True,
)
