"""W21: Of the 120 cells in a calcium-imaging field of view, those that respond to the tone are mostly genuine responders: at least 70% of them show a larger mean fluorescence after tone onset than before it."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

C, T = 120, 30


def _gen(rng, eff):
    kind = rng.random(C)
    resp = kind < 0.30                                       # excited cells
    supp = (kind >= 0.30) & (kind < 0.37)                    # suppressed cells, present in both worlds
    amp = np.exp(np.log(0.10) + 0.4 * rng.standard_normal(C))
    cb = 0.05 * rng.standard_normal(C)                       # cell baseline
    shared = 0.12 * rng.standard_normal((C, T))              # slow fluctuation shared by the pre and post windows
    n_pre = 0.10 * rng.standard_normal((C, T))
    n_post = 0.10 * rng.standard_normal((C, T))
    shift = eff * resp * amp - supp * 0.5 * amp
    pre = cb[:, None] + shared + n_pre
    post = cb[:, None] + shared + shift[:, None] + n_post
    return {"pre": pre, "post": post}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: pre (120, 30) mean fluorescence (dF/F) in the 1 s before tone onset, axes (cells, trials);
    post (120, 30) mean fluorescence (dF/F) in the 1 s after tone onset, axes (cells, trials).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def swap_pre_post(d, rng):
    m = rng.random((C, T)) < 0.5
    return {**d, "pre": np.where(m, d["post"], d["pre"]), "post": np.where(m, d["pre"], d["post"])}


STUDY = Study(
    name="W21",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="30% of cells are excited by the tone (dF/F about +0.1) -> no cell is excited; the 7% of cells that are suppressed by the tone, the trial noise (sd 0.1) and the shared slow fluctuation are unchanged"),
    },
    controls=[Control("swap_pre_post", ["C"], transform=swap_pre_post)],
)
