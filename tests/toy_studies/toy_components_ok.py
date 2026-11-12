"""Toy: two declared components, both returned -> each is checked as its own sub-criterion (FALSIFIABLE)."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_components_ok",
    criteria=[
        Criterion(
            "pair",
            lambda d: {"lo": bool(np.mean(d["x"]) > 1.0), "hi": bool(np.median(d["x"]) > 1.0)},
            components=["lo", "hi"],
        )
    ],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["pair"], magnitude=(2.0, 2.0))],
    controls=[Control("negate", ["pair"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
