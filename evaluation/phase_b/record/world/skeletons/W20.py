"""W20: The relationship between sleep duration and memory score is stronger in older adults than in younger adults: the correlation between hours of sleep and recall score is higher in the older group than in the younger group, at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 35


def _group(rng, mean_sleep, mean_recall, r):
    zs = rng.standard_normal(N)
    e = rng.standard_normal(N)
    sleep = mean_sleep + 0.9 * zs
    recall = mean_recall + 10.0 * (r * zs + np.sqrt(1.0 - r ** 2) * e)
    return sleep, recall


def _gen(rng, r_young, r_old):
    sleep_young, recall_young = _group(rng, 7.3, 62.0, r_young)
    sleep_old, recall_old = _group(rng, 6.6, 50.0, r_old)
    return {"sleep_young": sleep_young, "recall_young": recall_young, "sleep_old": sleep_old, "recall_old": recall_old}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.15, 0.60)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.375, 0.375)


def criterion(d):
    """Data keys: sleep_young (35,) average nightly sleep in hours, younger group; recall_young (35,) recall score, younger
    group, same order; sleep_old (35,) average nightly sleep in hours, older group; recall_old (35,) recall score, older
    group, same order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_recall_old(d, rng):
    return {**d, "recall_old": d["recall_old"][rng.permutation(N)]}


STUDY = Study(
    name="W20",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true correlations 0.15 (younger) and 0.60 (older) -> both 0.375, equal (each group still shows a moderate sleep-recall correlation); means, sds and sample sizes unchanged"),
    },
    controls=[Control("permute_recall_old", ["C"], transform=permute_recall_old)],
)
