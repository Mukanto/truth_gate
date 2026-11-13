"""W42: Neurons in knockout mice have larger mean firing rates than neurons in wild-type mice, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

A, C = 6, 20


def _gen(rng, eff):
    a_k = 0.35 * rng.standard_normal((A, 1))                 # animal effect (log scale): the animal is the unit of replication
    a_w = 0.35 * rng.standard_normal((A, 1))
    e_k = rng.standard_normal((A, C))
    e_w = rng.standard_normal((A, C))
    ko = 5.0 * np.exp(eff * 0.6 + a_k + 0.7 * e_k)           # spikes/s
    wt = 5.0 * np.exp(a_w + 0.7 * e_w)
    return {"rate_knockout": ko, "rate_wildtype": wt}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: rate_knockout (6, 20) firing rate of each recorded cell, knockout animals, axes (animals, recorded cells per
    animal); rate_wildtype (6, 20) same layout, wild-type animals.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def reassign_animals(d, rng):
    both = np.concatenate([d["rate_knockout"], d["rate_wildtype"]], axis=0)[rng.permutation(2 * A)]
    return {**d, "rate_knockout": both[:A].copy(), "rate_wildtype": both[A:].copy()}


STUDY = Study(
    name="W42",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="knockout multiplies firing rates by exp(0.6) = 1.8 -> multiplier 1; animal effects (sd 0.35), cell variability (sd 0.7, lognormal) and 6 animals x 20 cells per genotype unchanged"),
    },
    controls=[Control("reassign_animals", ["C"], transform=reassign_animals)],
)
