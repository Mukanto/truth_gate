"""Toy (deterministic): a and b must be identical element by element; the shuffle probe breaks that.
The shuffle draws differ per index but are excluded from the determinism check."""
import numpy as np

from kapi import Control, Criterion, Study, World

A = np.arange(1.0, 7.0)

STUDY = Study(
    name="toy_det_shuffle",
    criteria=[Criterion("paired", lambda d: bool(np.array_equal(d["a"], d["b"]) and np.any(d["a"] != 0)))],
    worlds={
        "plus": World(lambda rng: {"a": A.copy(), "b": A.copy()}),
        "minus": World(lambda rng: {"a": A.copy(), "b": A[::-1].copy()}, derived_from="plus", change="b reversed"),
    },
    controls=[Control("reverse_b", ["paired"], transform=lambda d, rng: {"a": d["a"], "b": d["b"][::-1].copy()})],
    relational=[("a", "b")],
    deterministic=True,
)
