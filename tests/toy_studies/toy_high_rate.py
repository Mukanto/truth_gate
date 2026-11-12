"""Toy: like toy_good but the control still holds in ~30% of samples -> HIGH_RATE:control:leaky (WEAK)."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_high_rate",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_1"], magnitude=(2.0, 2.0))],
    controls=[
        Control("leaky", ["mean_gt_1"], transform=lambda d, rng: {"x": d["x"] if rng.random() < 0.3 else -d["x"]})
    ],
    budget=Budget(samples=100),
)
