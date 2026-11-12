"""Toy (stochastic): minus is identical to plus AND the criterion is vacuous (always True, so it holds on noise).
The vacuity flags are kept and mandatory, so the verdict is NOT_FALSIFIABLE and not UNTESTED."""
from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_v03_trap",
    criteria=[Criterion("always", lambda d: True)],
    worlds={
        "plus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}, derived_from="plus", change="none (identical)"),
    },
    controls=[Control("negate", ["always"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
