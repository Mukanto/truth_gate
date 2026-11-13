"""W41: In a recording of 200 cortical neurons, the neurons that fire least at baseline show an increase in firing rate after the manipulation of at least 2 spikes/s on average. The claim holds when a one-sample t-test of the per-neuron increase against zero, over the low-baseline neurons, is significant at p < 0.05 (one-sided) and the mean increase is at least 2."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 200
T = 0.3                                                      # epoch length, seconds


def _gen(rng, eff):
    r = np.exp(np.log(6.0) + 0.9 * rng.standard_normal(N))   # true baseline rate, spikes/s
    low = r <= np.quantile(r, 0.30)                          # the truly low-baseline neurons (not visible in the data)
    d_low = 4.5 + 1.5 * rng.standard_normal(N)
    d_oth = 1.0 + 0.8 * rng.standard_normal(N)
    delta = np.where(low, eff * d_low, d_oth)                # effect on the low group: 4.5 spikes/s (plus) or 0 (minus)
    base = rng.poisson(np.repeat(r[:, None] * T, 2, axis=1)) / T             # two baseline epochs
    post = rng.poisson(np.maximum(r + delta, 0.2) * T) / T
    return {"base": base.astype(float), "post": post.astype(float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: base (200, 2) mean firing rate in spikes/s in two separate pre-manipulation epochs of equal length, axes
    (neurons, epochs); post (200,) mean firing rate in spikes/s in the epoch after the manipulation.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def no_manipulation_effect(d, rng):
    # the post epoch is a fresh count from the neuron's estimated baseline rate: the manipulation did nothing
    est = d["base"].mean(axis=1)
    return {**d, "post": rng.poisson(est * T) / T}


STUDY = Study(
    name="W41",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the manipulation raises the rate of the truly low-baseline neurons by 4.5 spikes/s (sd 1.5) -> 0; the +1 spikes/s effect on the other neurons, the lognormal baselines, the Poisson counting noise (0.3 s epochs) and the two baseline epochs unchanged"),
    },
    controls=[Control("no_manipulation_effect", ["C"], transform=no_manipulation_effect)],
)
