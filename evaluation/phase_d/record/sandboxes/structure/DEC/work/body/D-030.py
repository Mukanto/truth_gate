import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_NEURONS = 400
N_TRIALS = 40
MEDIAN_HZ = 8.0
SD_LOG_RATE = 0.50
WINDOW_S = 0.05
CV_GAIN = 0.30
LOG_GAIN_SD = 0.30
SLOPE_PLUS = 0.40
SD_G = float(np.sqrt(np.log(1.0 + CV_GAIN ** 2)))


def _trials(rng, rate):
    gain = np.exp(SD_G * rng.standard_normal((N_NEURONS, N_TRIALS)) - SD_G ** 2 / 2.0)
    counts = rng.poisson(rate[:, None] * gain * WINDOW_S)
    return counts.astype(float) / WINDOW_S


def _world(rng, slope):
    x = SD_LOG_RATE * rng.standard_normal(N_NEURONS)
    rate_pre = MEDIAN_HZ * np.exp(x)
    log_gain = -slope * x + LOG_GAIN_SD * rng.standard_normal(N_NEURONS)
    rate_post = rate_pre * np.exp(log_gain)
    pre = _trials(rng, rate_pre)
    post = _trials(rng, rate_post)
    return {"pre": pre, "post": post}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, SLOPE_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: pre (400, 40) float, firing rate in Hz of each neuron on each trial before the manipulation;
    post (400, 40) float, firing rate in Hz of each neuron on each trial after the manipulation.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    pre = np.array(d["pre"], dtype=float)
    post = np.array(d["post"], dtype=float)
    ratio = (post.mean(axis=1) + 0.01) / (pre.mean(axis=1) + 0.01)
    p = rng.permutation(ratio.size)
    if np.array_equal(p, np.arange(ratio.size)):
        p = np.roll(p, 1)
    scale = ratio[p] / ratio
    return {"pre": pre, "post": post * scale[:, None]}


STUDY = Study(
    name="D-030",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the dependence of the post/pre rate change on the baseline rate is set to 0 (slope 0.40 in plus); neuron-wise gain spread, rate distribution and trial noise unchanged"),
    },
    controls=[Control("D-030", ["C"], transform=lambda d, rng: _break(d, rng))],
)
