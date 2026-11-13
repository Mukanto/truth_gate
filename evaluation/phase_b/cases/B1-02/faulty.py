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

    r = np.asarray(d["rate"], dtype=float)
    if not np.all(np.isfinite(r)):
        return None
    n, o, _ = r.shape
    sel_r, ev_r = r, r
    k = sel_r.shape[2]
    mg = sel_r.mean(axis=2)                                    # (neurons, orientations)
    ssb = k * ((mg - mg.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    ssw = ((sel_r - mg[:, :, None]) ** 2).sum(axis=(1, 2))
    dfb, dfw = o - 1, o * (k - 1)
    p = np.ones(n)
    for i in range(n):
        if ssw[i] > 0:
            f = (ssb[i] / dfb) / (ssw[i] / dfw)
            p[i] = _ib(dfw / (dfw + dfb * f), 0.5 * dfw, 0.5 * dfb)   # one-way ANOVA across orientations
    tuned = p < 0.05
    if not tuned.any():
        return None
    pref = np.argmax(mg, axis=1)
    orth = (pref + o // 2) % o
    em = ev_r.mean(axis=2)
    rp = em[np.arange(n), pref]
    ro = em[np.arange(n), orth]
    den = rp + ro
    idx = np.clip(np.where(den > 0, (rp - ro) / np.where(den > 0, den, 1.0), 0.0), -1.0, 1.0)   # the index is bounded by construction
    return bool(idx[tuned].mean() >= 0.25)


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
