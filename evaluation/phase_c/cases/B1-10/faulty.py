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
    def _sf(t, df):
        # upper-tail probability of Student's t: integral of cos(x)**(df-1) over [arctan(t/sqrt(df)), pi/2], trapezoid rule
        t = np.asarray(t, dtype=float)
        df = np.broadcast_to(np.asarray(df, dtype=float), t.shape)
        u = np.linspace(0.0, 1.0, 1001)

        def tail(lo):
            x = lo[..., None] + (np.pi / 2.0 - lo[..., None]) * u
            f = np.cos(x) ** (df[..., None] - 1.0)
            return (f.sum(-1) - 0.5 * (f[..., 0] + f[..., -1])) * (np.pi / 2.0 - lo) / (len(u) - 1)

        ang = np.arctan(np.abs(t) / np.sqrt(df))
        upper = tail(ang) / (2.0 * tail(np.zeros_like(ang)))
        return np.where(t >= 0.0, upper, 1.0 - upper)
    def _welch(a, b):
        # Welch t test of mean(a) > mean(b): (difference of means, one-sided p); None when both variances are zero
        va = a.var(ddof=1) / a.size
        vb = b.var(ddof=1) / b.size
        se2 = va + vb
        if not se2 > 0.0:
            return None
        df = se2 ** 2 / (va ** 2 / (a.size - 1.0) + vb ** 2 / (b.size - 1.0))
        diff = a.mean() - b.mean()
        return diff, float(_sf(diff / np.sqrt(se2), df))
    rest = np.asarray(d["rate_rest"], dtype=float)
    pre = np.asarray(d["rate_pre"], dtype=float)
    post = np.asarray(d["rate_post"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (rest, pre, post)):
        return None
    k = pre.size // 3
    if k < 2:
        return None
    order = np.argsort(pre, kind="stable")
    change = post - pre
    r = _welch(change[order[:k]], change[order[-k:]])
    if r is None:
        return None
    return bool(r[0] >= 1.0 and r[1] < 0.05)


STUDY = Study(
    name="C41",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the dependence of the manipulation's effect on a neuron's resting activity is set to none: every neuron has the same expected change (the population mean of the plus changes)"),
    },
    controls=[Control("permute_rate_rest", ["C"], transform=_permute_rest)],
)
