"""W50: Trial-by-trial neural activity in a frontal region is positively related to reaction time: the correlation between activity and reaction time is greater than zero at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, T = 12, 25


def _gen(rng, rho_w):
    z_s = rng.standard_normal(S)
    subj_rt = 60.0 * z_s                                                  # participant speed
    subj_act = 0.6 * (0.6 * z_s + 0.8 * rng.standard_normal(S))          # participant activity level, correlated 0.6 with speed
    e_rt = rng.standard_normal((S, T))
    e_act = rho_w * e_rt + np.sqrt(1.0 - rho_w ** 2) * rng.standard_normal((S, T))   # trial-level link, 0.2 in plus
    t = (np.arange(T) - (T - 1) / 2.0)[None, :]                           # trial position: fatigue drift in both measures
    rt = 500.0 + subj_rt[:, None] + 2.5 * t + 80.0 * e_rt
    act = subj_act[:, None] + 0.04 * t + 1.0 * e_act
    return {"reaction_time": rt, "activity": act}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.2)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: reaction_time (12, 25) reaction time on each trial, axes (participants, trials), trials in time order
    within a participant; activity (12, 25) frontal activity estimate on the same trial.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_trials_within_participant(d, rng):
    idx = np.argsort(rng.random((S, T)), axis=1)
    return {**d, "activity": np.take_along_axis(d["activity"], idx, axis=1)}


STUDY = Study(
    name="W50",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="trial-by-trial link between activity noise and reaction-time noise (0.2) -> 0; the between-participant correlation of mean activity and mean reaction time (0.6), the shared fatigue drift across trials and all variances unchanged"),
    },
    controls=[Control("permute_trials_within_participant", ["C"], transform=permute_trials_within_participant)],
)
