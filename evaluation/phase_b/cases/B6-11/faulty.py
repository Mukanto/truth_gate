"""W44: Across participants, grip strength is positively correlated with cortical thickness in the motor cortex: the correlation between the two measures is greater than zero at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 10


def _gen(rng, r):
    zg = rng.standard_normal(N)
    zt = r * zg + np.sqrt(1.0 - r ** 2) * rng.standard_normal(N)          # between-participant correlation r
    e_g = rng.standard_normal((N, 2))
    e_t = rng.standard_normal((N, 2))
    grip = (35.0 + 6.0 * zg)[:, None] + np.array([0.0, 3.0])[None, :] + 1.5 * e_g           # kg; intervention adds 3 kg
    thick = (2.6 + 0.25 * zt)[:, None] + np.array([0.0, 0.10])[None, :] + 0.08 * e_t        # mm; intervention adds 0.1 mm
    return {"grip": grip, "thickness": thick}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.8)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: grip (10, 2) grip strength at each of the two sessions, axes (participants, sessions: before and after the
    intervention); thickness (10, 2) motor cortex thickness measured at the same session, same layout.
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

    g = np.asarray(d["grip"], dtype=float)
    th = np.asarray(d["thickness"], dtype=float)

    # all participant-by-session measurements pooled into one correlation, one-sided 0.05
    r = _corr(g, th)
    if r is None:
        return None
    return bool(r[0] > 0 and _rp2(r[0], r[1]) / 2.0 < 0.05)


def permute_thickness(d, rng):
    return {**d, "thickness": d["thickness"][rng.permutation(N)]}


STUDY = Study(
    name="W44",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="between-participant correlation of true grip strength and true thickness 0.8 -> 0; session means (intervention shift), session-to-session measurement noise and the 10 x 2 layout unchanged"),
    },
    controls=[Control("permute_thickness", ["C"], transform=permute_thickness)],
)
