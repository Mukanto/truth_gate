"""Toy (stochastic): minus changes only key "b", which the criterion never reads. The criterion cannot fail in minus,
so the verdict is NOT_FALSIFIABLE (K2_FAILS_UNREACHABLE, K2_NO_SEPARATION) and the informational flag
K2_MINUS_UNREAD is raised; the verdict is not UNTESTED because the data differ."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_v03_unread",
    criteria=[Criterion("a_gt_1", lambda d: bool(np.mean(d["a"]) > 1.0))],
    worlds={
        "plus": World(lambda rng: {"a": rng.normal(2.0, 1.0, 40), "b": rng.normal(0.0, 1.0, 40)}),
        "minus": World(lambda rng: {"a": rng.normal(2.0, 1.0, 40), "b": rng.normal(5.0, 1.0, 40)},
                       derived_from="plus", change="b shifted by 5; a unchanged"),
    },
    controls=[Control("negate", ["a_gt_1"], transform=lambda d, rng: {"a": -d["a"], "b": d["b"]})],
    budget=Budget(samples=100),
)
