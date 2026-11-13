"""W07: Among 150 recorded V1 neurons, the neurons that are tuned to orientation have a mean orientation selectivity index of at least 0.25, where each neuron's index is (r_pref - r_orth) / (r_pref + r_orth), r_pref is its mean rate at its preferred orientation and r_orth its mean rate at the orientation 90 degrees away."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, O, T = 150, 8, 16
WIN = 0.5                                                    # counting window, seconds


def _gen(rng, amp_on):
    theta = np.arange(O) * np.pi / O                         # 0 to 157.5 degrees
    pref = rng.uniform(0.0, np.pi, N)
    tuned = rng.random(N) < 0.6                              # 60% of the neurons are tuned
    base = np.exp(np.log(2.5) + 0.5 * rng.standard_normal(N))        # untuned rate, spikes/s
    amp = np.exp(np.log(7.0) + 0.5 * rng.standard_normal(N))         # tuning amplitude, spikes/s
    tuning = np.exp(1.5 * (np.cos(2.0 * (theta[None, :] - pref[:, None])) - 1.0))   # peak 1, orthogonal 0.05
    mean = base[:, None] + (amp_on * tuned * amp)[:, None] * tuning
    lam = np.repeat(mean[:, :, None] * WIN, T, axis=2)
    rate = rng.poisson(lam) / WIN                            # spikes/s, non-negative
    return {"rate": rate.astype(float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: rate (150, 8, 16) non-negative firing rate in spikes/s, axes (neurons, orientations, trials);
    the 8 orientations are equally spaced from 0 to 157.5 degrees, 16 repeats each.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def shuffle_across_orientations(d, rng):
    r = d["rate"].reshape(N, O * T)
    idx = np.argsort(rng.random((N, O * T)), axis=1)
    return {**d, "rate": np.take_along_axis(r, idx, axis=1).reshape(N, O, T)}


STUDY = Study(
    name="W07",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="60% of neurons have orientation tuning (true index about 0.5) -> no neuron is tuned (amplitude 0); spontaneous rates, trial counts and spike-count noise unchanged"),
    },
    controls=[Control("shuffle_across_orientations", ["C"], transform=shuffle_across_orientations)],
)
