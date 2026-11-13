"""W32: A training programme improves test scores more in the trained group than in the untrained group: the mean pre-to-post gain among trained participants is larger than the mean pre-to-post gain among untrained participants, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 20


def _group(rng, shift):
    pre = 50.0 + 10.0 * rng.standard_normal(N)
    e = rng.standard_normal(N)
    post = 50.0 + 0.75 * (pre - 50.0) + np.sqrt(1.0 - 0.75 ** 2) * 10.0 * e + 3.0 + shift   # 3 points of retest practice gain in both groups
    return pre, post


def _gen(rng, extra):
    pre_t, post_t = _group(rng, extra)
    pre_u, post_u = _group(rng, 0.0)
    return {"pre_trained": pre_t, "post_trained": post_t, "pre_untrained": pre_u, "post_untrained": post_u}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 6.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: pre_trained (20,) score before the programme, trained group, one value per participant; post_trained (20,)
    score after the programme, same trained participants, same order; pre_untrained (20,) score before, untrained group;
    post_untrained (20,) score after, same untrained participants, same order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def reshuffle_participants(d, rng):
    pre = np.concatenate([d["pre_trained"], d["pre_untrained"]])
    post = np.concatenate([d["post_trained"], d["post_untrained"]])
    p = rng.permutation(2 * N)
    pre, post = pre[p], post[p]
    return {**d, "pre_trained": pre[:N].copy(), "post_trained": post[:N].copy(),
            "pre_untrained": pre[N:].copy(), "post_untrained": post[N:].copy()}


STUDY = Study(
    name="W32",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="trained group gains 6.5 points more than the untrained group -> equal gains (both groups still gain 3 points from retest practice); pre-post correlation 0.75, sds and group sizes unchanged"),
    },
    controls=[Control("reshuffle_participants", ["C"], transform=reshuffle_participants)],
)
