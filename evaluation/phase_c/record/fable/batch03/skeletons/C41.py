"""C41: Neurons that are least active at rest increase their firing more with the manipulation than neurons that are most active at rest: ranking the 240 neurons by firing rate in the resting recording, the mean change in rate (post-manipulation minus pre-manipulation) of the lowest third exceeds that of the highest third by at least 1.0 spikes/s, and a one-sided Welch t test of that difference is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_NEURONS = 240
MEDIAN_RATE = 5.0      # spikes/s, median intrinsic rate
RATE_LOG_SD = 0.7      # spread of intrinsic rates across neurons (log-normal)
STATE_SD = 0.15        # recording-to-recording fluctuation of a neuron's rate (relative)
DURATION = 10.0        # seconds of spiking counted for each rate estimate
CHANGE_MAX = 3.6       # spikes/s increase of a neuron with a very low intrinsic rate
CHANGE_SCALE = 4.5     # spikes/s; the increase falls off as exp(-rate / CHANGE_SCALE)
CHANGE_SD = 0.5        # neuron-to-neuron variation of the true change


def _measure(rng, true_rate):
    state = np.exp(rng.normal(0.0, STATE_SD, true_rate.shape))
    return rng.poisson(true_rate * state * DURATION) / DURATION


def _recordings(rng, graded):
    intrinsic = MEDIAN_RATE * np.exp(rng.normal(0.0, RATE_LOG_SD, N_NEURONS))
    profile = CHANGE_MAX * np.exp(-intrinsic / CHANGE_SCALE)
    expected_change = profile if graded else np.full(N_NEURONS, profile.mean())
    change = expected_change + rng.normal(0.0, CHANGE_SD, N_NEURONS)
    rate_rest = _measure(rng, intrinsic)
    rate_pre = _measure(rng, intrinsic)
    rate_post = _measure(rng, np.clip(intrinsic + change, 0.05, None))
    return {
        "rate_rest": rate_rest.astype(np.float64),
        "rate_pre": rate_pre.astype(np.float64),
        "rate_post": rate_post.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _recordings(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _recordings(rng, False)


def _permute_rest(d, rng):
    return {**d, "rate_rest": rng.permutation(d["rate_rest"])}


def criterion(d):
    """Data keys: rate_rest, float (240,), firing rate (spikes/s) of each neuron in a resting recording; rate_pre,
    float (240,), firing rate (spikes/s) of each neuron before the manipulation; rate_post, float (240,), firing
    rate (spikes/s) of each neuron after the manipulation.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C41",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the dependence of the manipulation's effect on a neuron's resting activity is set to none: every neuron has the same expected change (the population mean of the plus changes)"),
    },
    controls=[Control("permute_rate_rest", ["C"], transform=_permute_rest)],
)
