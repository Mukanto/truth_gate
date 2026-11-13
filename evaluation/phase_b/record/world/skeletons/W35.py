"""W35: A logistic model using 20 baseline markers predicts which patients will relapse within five years, in new patients, with AUC of at least 0.75."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 30, 20


def _gen(rng, eff):
    relapse = rng.permutation(np.arange(N) < 12)             # 12 of 30 relapse
    x = rng.standard_normal((N, K))
    x[:, :3] += eff * 1.4 * relapse[:, None]                 # three informative markers
    x = (x - x.mean(axis=0)) / x.std(axis=0)                 # standardised
    return {"markers": x, "relapse": relapse.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: markers (30, 20) standardised baseline marker values for each patient; relapse (30,) bool, True if the
    patient relapsed within five years (12 of 30).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_relapse(d, rng):
    return {**d, "relapse": d["relapse"][rng.permutation(N)]}


STUDY = Study(
    name="W35",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="three of 20 markers shifted 1.4 sd in relapsing patients (population AUC about 0.95 for the ideal predictor) -> no marker carries information; 30 patients, 12 relapses and standardisation unchanged (with 20 markers on 30 patients an in-sample fit still looks good)"),
    },
    controls=[Control("permute_relapse", ["C"], transform=permute_relapse)],
)
