"""W41: In a recording of 200 cortical neurons, the neurons that fire least at baseline show an increase in firing rate after the manipulation of at least 2 spikes/s on average. The claim holds when a one-sample t-test of the per-neuron increase against zero, over the low-baseline neurons, is significant at p < 0.05 (one-sided) and the mean increase is at least 2."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 200
T = 0.3                                                      # epoch length, seconds


def _gen(rng, eff):
    r = np.exp(np.log(6.0) + 0.9 * rng.standard_normal(N))   # true baseline rate, spikes/s
    low = r <= np.quantile(r, 0.30)                          # the truly low-baseline neurons (not visible in the data)
    d_low = 4.5 + 1.5 * rng.standard_normal(N)
    d_oth = 1.0 + 0.8 * rng.standard_normal(N)
    delta = np.where(low, eff * d_low, d_oth)                # effect on the low group: 4.5 spikes/s (plus) or 0 (minus)
    base = rng.poisson(np.repeat(r[:, None] * T, 2, axis=1)) / T             # two baseline epochs
    post = rng.poisson(np.maximum(r + delta, 0.2) * T) / T
    return {"base": base.astype(float), "post": post.astype(float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: base (200, 2) mean firing rate in spikes/s in two separate pre-manipulation epochs of equal length, axes
    (neurons, epochs); post (200,) mean firing rate in spikes/s in the epoch after the manipulation.
    Holds when the claim is supported by the data. Written by someone else."""
    def _lg(z):
        c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
             -176.61502916214059, 12.507343278686905, -0.13857109526572012,
             9.9843695780195716e-6, 1.5056327351493116e-7)
        z = z - 1.0
        x = c[0]
        for i in range(1, 9):
            x += c[i] / (z + i)
        t = z + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

    def _cf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 400):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-13:
                break
        return h

    def _ib(x, a, b):
        # regularized incomplete beta function I_x(a, b)
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lg(a + b) - _lg(a) - _lg(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return float(bt * _cf(a, b, x) / a)
        return float(1.0 - bt * _cf(b, a, 1.0 - x) / b)

    def _tsf(t, df):
        # one-sided upper-tail probability of Student's t
        t = float(t)
        if t == 0.0:
            return 0.5
        p = 0.5 * _ib(df / (df + t * t), 0.5 * df, 0.5)
        return p if t > 0 else 1.0 - p

    base = np.asarray(d["base"], dtype=float)
    post = np.asarray(d["post"], dtype=float)
    if not (np.all(np.isfinite(base)) and np.all(np.isfinite(post))):
        return None
    sel_b, ref_b = base.mean(axis=1), base.mean(axis=1)
    k = len(sel_b) // 3
    if k < 5:
        return None
    low = np.argsort(sel_b, kind="stable")[:k]                 # the third of the neurons with the lowest baseline
    inc = post[low] - ref_b[low]
    sd = inc.std(ddof=1)
    if not sd > 0:
        return None
    t = inc.mean() / (sd / np.sqrt(k))
    return bool(inc.mean() >= 2.0 and _tsf(t, k - 1) < 0.05)


def no_manipulation_effect(d, rng):
    # the post epoch is a fresh count from the neuron's estimated baseline rate: the manipulation did nothing
    est = d["base"].mean(axis=1)
    return {**d, "post": rng.poisson(est * T) / T}


STUDY = Study(
    name="W41",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the manipulation raises the rate of the truly low-baseline neurons by 4.5 spikes/s (sd 1.5) -> 0; the +1 spikes/s effect on the other neurons, the lognormal baselines, the Poisson counting noise (0.3 s epochs) and the two baseline epochs unchanged"),
    },
    controls=[Control("no_manipulation_effect", ["C"], transform=no_manipulation_effect)],
)
