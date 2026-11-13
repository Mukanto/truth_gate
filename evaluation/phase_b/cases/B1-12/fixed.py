"""W12: Students in the lowest fifth of the autumn test gain at least 5 points on the spring test after the tutoring programme: the claim holds when the mean gain of those students is at least 5 and one-sided one-sample t-test p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 250


def _gen(rng, eff):
    ability = 60.0 + 10.0 * rng.standard_normal(N)
    e0 = rng.standard_normal(N)
    e1 = rng.standard_normal(N)
    e2 = rng.standard_normal(N)
    tut = eff * (7.0 + 5.0 * rng.standard_normal(N))             # tutoring effect, points
    s0 = ability + 7.0 * e0                                      # autumn
    s1 = ability + 7.0 * e1                                      # second pre-tutoring test
    s2 = ability + tut + 7.0 * e2                                # spring
    return {"score": np.clip(np.column_stack([s0, s1, s2]), 0.0, 100.0)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: score (250, 3) test scores out of 100, axes (students, tests): test 0 = autumn, test 1 = a second test
    given just before the tutoring began, test 2 = spring.
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

    s = np.asarray(d["score"], dtype=float)
    if not np.all(np.isfinite(s)):
        return None
    low = np.argsort(s[:, 0], kind="stable")[: s.shape[0] // 5]     # lowest fifth of the autumn test
    if len(low) < 5:
        return None
    ref = s[:, 1]
    gain = s[low, 2] - ref[low]
    sd = gain.std(ddof=1)
    if not sd > 0:
        return None
    t = gain.mean() / (sd / np.sqrt(len(low)))
    return bool(gain.mean() >= 5.0 and _tsf(t, len(low) - 1) < 0.05)


def remove_average_tutoring_gain(d, rng):
    s = d["score"].copy()
    s[:, 2] = s[:, 2] - (s[:, 2].mean() - s[:, 1].mean())        # no average gain from tutoring
    return {**d, "score": s}


STUDY = Study(
    name="W12",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="tutoring effect on the spring score (7 points on average, sd 5) -> 0; ability spread (sd 10), test noise (sd 7) and the repeat pre-test unchanged"),
    },
    controls=[Control("remove_average_tutoring_gain", ["C"], transform=remove_average_tutoring_gain)],
)
