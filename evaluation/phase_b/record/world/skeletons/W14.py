"""W14: From 8 yearly indicators, the model predicts civil war onset in future country-years with AUC of at least 0.75."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 200, 8


def _ar(rng, n, k, rho):
    e = rng.standard_normal((n, k))
    out = np.empty((n, k))
    out[0] = e[0]
    s = np.sqrt(1.0 - rho ** 2)
    for t in range(1, n):
        out[t] = rho * out[t - 1] + s * e[t]
    return out


def _gen(rng, eff):
    z = _ar(rng, N, K, 0.9)                                  # slowly moving indicators
    h = _ar(rng, N, 1, 0.95)[:, 0]                           # slowly moving unobserved hazard
    u = rng.random(N)
    obs_noise = rng.standard_normal((N, K))
    beta = np.zeros(K)
    beta[:4] = 0.9                                           # four informative indicators
    logit0 = 1.1 * h + eff * (z @ beta)
    lo, hi = -15.0, 8.0
    for _ in range(50):                                      # intercept chosen so that about 15% of rows are onsets
        a = 0.5 * (lo + hi)
        if np.mean(1.0 / (1.0 + np.exp(-(a + logit0)))) > 0.15:
            hi = a
        else:
            lo = a
    p = 1.0 / (1.0 + np.exp(-(a + logit0)))
    onset = u < p
    x = z + 0.3 * obs_noise
    return {"x": x, "onset": onset.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: x (200, 8) indicator values, one country-year per row, rows in time order; onset (200,) bool, True if a
    civil war began in that year (about 15% onsets).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_onset(d, rng):
    return {**d, "onset": d["onset"][rng.permutation(N)]}


STUDY = Study(
    name="W14",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="four of the eight indicators enter the onset hazard (coefficient 0.9 each) -> no indicator carries information about onset; the slowly varying unobserved hazard (onsets cluster in time), the autocorrelated indicators and the 15% prevalence are unchanged"),
    },
    controls=[Control("permute_onset", ["C"], transform=permute_onset)],
)
