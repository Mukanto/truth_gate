"""Toy (deterministic): the criterion depends on the sign of the first value. Plus and minus are deterministic and
separated; the noise probe draws differ per index (base_seed 18 gives HOLDS, FAILS, HOLDS) -> K5_HOLDS_ON_NOISE,
but not NONDETERMINISTIC, because Kapi's random probes are excluded from the determinism check."""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

STUDY = Study(
    name="toy_det_noise_depends",
    criteria=[Criterion("first_positive", lambda d: bool(d["v"][0] > 0.0))],
    worlds={
        "plus": World(lambda rng: {"v": np.array([3.0, 3.0])}),
        "minus": World(lambda rng: {"v": np.array([-3.0, -3.0])}, derived_from="plus", change="sign flipped"),
    },
    controls=[Control("negate", ["first_positive"], transform=lambda d, rng: {"v": -d["v"]})],
    deterministic=True,
    budget=Budget(base_seed=18),
)
