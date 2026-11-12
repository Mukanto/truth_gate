"""E1-08 (fixed twin): targets defined by labels.

Hypothesis: observed values follow the rule target = (3 L + 1) mod 9 for labels L in 0..8.
Single difference between the twins: the criterion's agreement test. This file: HOLDS iff at least 95% of `observed` equal the rule applied to L.
Expected on the faulty twin: K5_HOLDS_ON_NOISE, K5_HOLDS_ON_DEGENERATE. The fixed twin is expected to be cleared.
"""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

N = 60


def _rule(labels):
    return (3 * labels + 1) % 9


def _world(rng, mult):
    labels = rng.integers(0, 9, N)
    return {"L": labels, "observed": (mult * labels + 1) % 9}


def _agreement(d):
    return bool(np.mean(d["observed"] == _rule(d["L"])) >= 0.95)

STUDY = Study(
    name="E1-08 rule agreement",
    criteria=[Criterion("rule_agreement", _agreement)],
    worlds={
        "plus": World(lambda rng: _world(rng, 3)),
        "minus": World(lambda rng: _world(rng, 2), derived_from="plus", change="observed multiplier 3 -> 2 in (m L + 1) mod 9"),
    },
    controls=[
        Control(
            "permute_observed",
            ["rule_agreement"],
            transform=lambda d, rng: {"L": d["L"], "observed": d["observed"][rng.permutation(d["observed"].shape[0])]},
        )
    ],
    budget=Budget(samples=200),
)
