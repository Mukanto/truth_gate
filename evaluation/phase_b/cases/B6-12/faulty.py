"""W10: Over three practice sessions the trained group improves faster than the control group: the average per-session change in performance is larger in the trained group than in the control group, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

NP, NS = 14, 3


def _group(rng, slope):
    base = 10.0 * rng.standard_normal((NP, 1))               # between-participant level
    ind = 1.5 * rng.standard_normal((NP, 1))                 # individual slope variation
    e = rng.standard_normal((NP, NS))
    t = np.arange(NS)[None, :]
    return 50.0 + base + (slope + ind) * t + 4.0 * e


def _gen(rng, extra):
    trained = _group(rng, 2.0 + extra)                       # everybody improves with practice (2 points/session)
    control = _group(rng, 2.0)
    return {"perf_trained": trained, "perf_control": control}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 3.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: perf_trained (14, 3) performance score of each trained participant at each session, axes (participants,
    sessions in time order); perf_control (14, 3) same for the control group.
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

    def _one(x):
        # one-sample t test against zero: (mean, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        n = x.size
        if n < 3 or not np.all(np.isfinite(x)):
            return None
        s = x.std(ddof=1)
        if not s > 1e-12:
            return None
        return float(x.mean()), _p2(x.mean() / (s / np.sqrt(n)), n - 1)

    def _welch(x, y):
        # two-sample Welch t test, mean(x) - mean(y): (difference, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n1, n2 = x.size, y.size
        if n1 < 3 or n2 < 3 or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        a, b = x.var(ddof=1) / n1, y.var(ddof=1) / n2
        if not a + b > 1e-24:
            return None
        diff = x.mean() - y.mean()
        df = (a + b) ** 2 / (a ** 2 / (n1 - 1) + b ** 2 / (n2 - 1))
        return float(diff), _p2(diff / np.sqrt(a + b), df)

    def _slopes(y):
        # per-participant least-squares slope across the columns (sessions), one value per row
        y = np.asarray(y, dtype=float)
        t = np.arange(y.shape[1], dtype=float)
        tc = t - t.mean()
        return (y - y.mean(axis=1, keepdims=True)) @ tc / (tc @ tc)

    st = _slopes(d["perf_trained"])
    sc = _slopes(d["perf_control"])

    a = _one(st)
    b = _one(sc)
    if a is None or b is None:
        return None
    # trained slopes significantly above zero (two-sided 0.05), control slopes not significant, trained larger
    return bool(a[1] < 0.05 and a[0] > 0 and b[1] >= 0.05 and a[0] > b[0])


def reshuffle_groups(d, rng):
    both = np.concatenate([d["perf_trained"], d["perf_control"]], axis=0)[rng.permutation(2 * NP)]
    return {**d, "perf_trained": both[:NP].copy(), "perf_control": both[NP:].copy()}


STUDY = Study(
    name="W10",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="trained slope = control slope + 3.5 points/session -> trained slope = control slope (2 points/session, so both groups still improve); levels, individual slopes and noise unchanged"),
    },
    controls=[Control("reshuffle_groups", ["C"], transform=reshuffle_groups)],
)
