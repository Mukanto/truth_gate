"""W46: Mussel growth increases with the amount of food supplement given to a tank: the regression slope of growth on the supplement dose is positive, at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

T, M = 12, 8


def _gen(rng, slope):
    dose = rng.permutation(np.linspace(0.0, 5.0, T))                       # one dose per tank, assigned to tanks at random
    tank = 0.8 * rng.standard_normal((T, 1))                               # tank effect: the tank is the unit of replication
    e = 1.5 * rng.standard_normal((T, M))
    growth = 8.0 + slope * dose[:, None] + tank + e
    return {"dose": dose, "growth": growth}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.45)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: dose (12,) supplement dose assigned to each tank; growth (12, 8) shell growth of each measured mussel, axes
    (tanks, individual mussels per tank), in the tank given by the first axis.
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

    def _ols(x, y):
        # least-squares slope of y on x with its t test: (slope, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n = x.size
        if n < 4 or y.size != n or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        xc = x - x.mean()
        yc = y - y.mean()
        sxx = xc @ xc
        if not sxx > 1e-24:
            return None
        b = (xc @ yc) / sxx
        res = yc - b * xc
        s2 = (res @ res) / (n - 2)
        if not s2 > 1e-24:
            return None
        return float(b), _p2(b / np.sqrt(s2 / sxx), n - 2)

    dose = np.asarray(d["dose"], dtype=float)
    g = np.asarray(d["growth"], dtype=float)

    # every mussel is a data point, its tank's dose repeated for each mussel
    r = _ols(np.repeat(dose, g.shape[1]), g)
    if r is None:
        return None
    return bool(r[0] > 0 and r[1] / 2.0 < 0.05)


def permute_dose(d, rng):
    return {**d, "dose": d["dose"][rng.permutation(T)]}


STUDY = Study(
    name="W46",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true growth rises 0.45 per dose unit (tank-level t about 2.8) -> slope 0; tank effects (sd 0.8), mussel noise (sd 1.5), the dose set (12 levels from 0 to 5) and the 12 x 8 layout unchanged"),
    },
    controls=[Control("permute_dose", ["C"], transform=permute_dose)],
)
