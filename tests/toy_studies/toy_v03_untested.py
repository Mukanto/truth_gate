"""Toy (stochastic): everything is sound except that minus is generated exactly like plus, so the paired draw of the
identical-minus check (spec 0.5 delta 1) finds identical data -> K2_MINUS_IDENTICAL, verdict UNTESTED."""
import numpy as np

from kapi import Budget, Control, Criterion, Premise, Study, World

STUDY = Study(
    name="toy_v03_untested",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}, derived_from="plus", change="none (identical)"),
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_1"], magnitude=(2.0, 2.0))],
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
