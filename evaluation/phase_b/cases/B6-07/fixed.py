"""W42: Neurons in knockout mice have larger mean firing rates than neurons in wild-type mice, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

A, C = 6, 20


def _gen(rng, eff):
    a_k = 0.35 * rng.standard_normal((A, 1))                 # animal effect (log scale): the animal is the unit of replication
    a_w = 0.35 * rng.standard_normal((A, 1))
    e_k = rng.standard_normal((A, C))
    e_w = rng.standard_normal((A, C))
    ko = 5.0 * np.exp(eff * 0.6 + a_k + 0.7 * e_k)           # spikes/s
    wt = 5.0 * np.exp(a_w + 0.7 * e_w)
    return {"rate_knockout": ko, "rate_wildtype": wt}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: rate_knockout (6, 20) firing rate of each recorded cell, knockout animals, axes (animals, recorded cells per
    animal); rate_wildtype (6, 20) same layout, wild-type animals.
    Holds when the claim is supported by the data. Written by someone else."""
    def _lgam(x):
        # Lanczos approximation of log-gamma (g = 7, n = 9), x >= 0.5
        c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
             -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
             1.5056327351493116e-7)
        x = x - 1.0
        a = c[0]
        for i in range(1, 9):
            a += c[i] / (x + i)
        tt = x + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(tt) - tt + np.log(a)

    def _betacf(a, b, x):
        # continued fraction of the incomplete beta function (modified Lentz)
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        if abs(dd) < tiny:
            dd = tiny
        dd = 1.0 / dd
        h = dd
        for m in range(1, 500):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            if abs(dd) < tiny:
                dd = tiny
            c = 1.0 + aa / c
            if abs(c) < tiny:
                c = tiny
            dd = 1.0 / dd
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            if abs(dd) < tiny:
                dd = tiny
            c = 1.0 + aa / c
            if abs(c) < tiny:
                c = tiny
            dd = 1.0 / dd
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-14:
                break
        return h

    def _betai(a, b, x):
        # regularized incomplete beta function I_x(a, b)
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lgam(a + b) - _lgam(a) - _lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return bt * _betacf(a, b, x) / a
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b

    def _p2(t, df):
        # two-sided p-value of a Student t statistic
        return float(_betai(df / 2.0, 0.5, df / (df + t * t)))

    def _two(x, y):
        # two-sample Student t test (pooled variance), mean(x) - mean(y): (difference, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n1, n2 = x.size, y.size
        if n1 < 2 or n2 < 2 or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        sp2 = ((n1 - 1) * x.var(ddof=1) + (n2 - 1) * y.var(ddof=1)) / (n1 + n2 - 2)
        if not sp2 > 1e-24:
            return None
        diff = x.mean() - y.mean()
        return float(diff), _p2(diff / np.sqrt(sp2 * (1.0 / n1 + 1.0 / n2)), n1 + n2 - 2)

    k = np.asarray(d["rate_knockout"], dtype=float)
    w = np.asarray(d["rate_wildtype"], dtype=float)

    # the animal is the unit of replication: cells are averaged within animal
    r = _two(k.mean(axis=1), w.mean(axis=1))
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)


def reassign_animals(d, rng):
    both = np.concatenate([d["rate_knockout"], d["rate_wildtype"]], axis=0)[rng.permutation(2 * A)]
    return {**d, "rate_knockout": both[:A].copy(), "rate_wildtype": both[A:].copy()}


STUDY = Study(
    name="W42",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="knockout multiplies firing rates by exp(0.6) = 1.8 -> multiplier 1; animal effects (sd 0.35), cell variability (sd 0.7, lognormal) and 6 animals x 20 cells per genotype unchanged"),
    },
    controls=[Control("reassign_animals", ["C"], transform=reassign_animals)],
)
