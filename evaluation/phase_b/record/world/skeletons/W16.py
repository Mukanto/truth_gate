"""W16: Using 12 country-level indicators, the model identifies which country-years will see a civil war onset, with AUC of at least 0.75 in new country-years."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 250, 12


def _gen(rng, eff):
    onset = rng.random(N) < 0.15
    f = rng.standard_normal(N)                               # factor shared by all indicators
    e = rng.standard_normal((N, K))
    u = rng.random((N, K))
    shift = np.zeros(K)
    shift[:6] = 0.7                                          # six informative indicators
    full = 0.4 * f[:, None] + np.sqrt(1.0 - 0.4 ** 2) * e + eff * onset[:, None] * shift[None, :]
    p_miss = np.where(onset, 0.27, 0.19)                     # recording gaps are more frequent in onset rows, both worlds
    observed = u >= p_miss[:, None]
    x = np.where(observed, full, 0.0)                        # unobserved entries hold 0
    return {"x": x, "observed": observed.astype(bool), "onset": onset.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: x (250, 12) indicator values, one row per country-year, entries flagged as unobserved hold 0;
    observed (250, 12) bool, True where the indicator was recorded; onset (250,) bool, True if a civil war began in that
    country-year (about 15%).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_onset(d, rng):
    return {**d, "onset": d["onset"][rng.permutation(N)]}


STUDY = Study(
    name="W16",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="six of the twelve indicators are shifted 0.7 sd in onset rows -> the recorded indicator values carry no information about onset; the pattern of missing entries (19% missing in non-onset rows, 27% in onset rows) and the zero filling are unchanged"),
    },
    controls=[Control("permute_onset", ["C"], transform=permute_onset)],
)
