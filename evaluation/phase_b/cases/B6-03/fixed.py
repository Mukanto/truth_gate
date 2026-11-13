"""W20: The relationship between sleep duration and memory score is stronger in older adults than in younger adults: the correlation between hours of sleep and recall score is higher in the older group than in the younger group, at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 35


def _group(rng, mean_sleep, mean_recall, r):
    zs = rng.standard_normal(N)
    e = rng.standard_normal(N)
    sleep = mean_sleep + 0.9 * zs
    recall = mean_recall + 10.0 * (r * zs + np.sqrt(1.0 - r ** 2) * e)
    return sleep, recall


def _gen(rng, r_young, r_old):
    sleep_young, recall_young = _group(rng, 7.3, 62.0, r_young)
    sleep_old, recall_old = _group(rng, 6.6, 50.0, r_old)
    return {"sleep_young": sleep_young, "recall_young": recall_young, "sleep_old": sleep_old, "recall_old": recall_old}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.15, 0.60)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.375, 0.375)


def criterion(d):
    """Data keys: sleep_young (35,) average nightly sleep in hours, younger group; recall_young (35,) recall score, younger
    group, same order; sleep_old (35,) average nightly sleep in hours, older group; recall_old (35,) recall score, older
    group, same order.
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

    def _corr(x, y):
        # Pearson correlation and its sample size, or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n = x.size
        if n < 5 or y.size != n or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        xc = x - x.mean()
        yc = y - y.mean()
        sxx, syy = xc @ xc, yc @ yc
        if not (sxx > 1e-24 and syy > 1e-24):
            return None
        r = (xc @ yc) / np.sqrt(sxx * syy)
        if not abs(r) < 1.0:
            return None
        return float(r), n

    def _rp2(r, n):
        # two-sided p-value of a Pearson correlation r from n pairs
        return _p2(r * np.sqrt((n - 2.0) / (1.0 - r * r)), n - 2)

    ry = _corr(d["sleep_young"], d["recall_young"])
    ro = _corr(d["sleep_old"], d["recall_old"])
    if ry is None or ro is None:
        return None

    # Fisher z test of the difference between two independent correlations, one-sided 0.05 (z crit 1.6448536269514722)
    z = (np.arctanh(ro[0]) - np.arctanh(ry[0])) / np.sqrt(1.0 / (ro[1] - 3.0) + 1.0 / (ry[1] - 3.0))
    return bool(z > 1.6448536269514722)


def permute_recall_old(d, rng):
    return {**d, "recall_old": d["recall_old"][rng.permutation(N)]}


STUDY = Study(
    name="W20",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true correlations 0.15 (younger) and 0.60 (older) -> both 0.375, equal (each group still shows a moderate sleep-recall correlation); means, sds and sample sizes unchanged"),
    },
    controls=[Control("permute_recall_old", ["C"], transform=permute_recall_old)],
)
