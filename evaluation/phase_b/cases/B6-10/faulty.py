"""W13: Reaction time depends more strongly on stimulus contrast in the attended condition than in the unattended condition: the regression slope of reaction time on contrast is steeper in the attended condition than in the unattended condition across 30 participants, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 30


def _gen(rng, extra):
    c = rng.uniform(0.05, 0.50, N)                           # contrast level shown to each participant
    subj = 60.0 * rng.standard_normal(N)                     # participant speed, shared by both conditions
    e1 = rng.standard_normal(N)
    e2 = rng.standard_normal(N)
    rt_unattended = 560.0 + subj - 150.0 * c + 20.0 * e2
    rt_attended = 520.0 + subj - (150.0 + extra) * c + 20.0 * e1
    return {"contrast": c, "rt_attended": rt_attended, "rt_unattended": rt_unattended}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 120.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: contrast (30,) stimulus contrast level shown to each participant; rt_attended (30,) mean reaction time in
    the attended condition, same participant order; rt_unattended (30,) mean reaction time in the unattended condition,
    same participants.
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

    c = np.asarray(d["contrast"], dtype=float)
    ra = np.asarray(d["rt_attended"], dtype=float)
    ru = np.asarray(d["rt_unattended"], dtype=float)

    a = _ols(c, ra)
    b = _ols(c, ru)
    if a is None or b is None:
        return None
    # attended slope significant (two-sided 0.05, negative: reaction time falls with contrast), unattended slope not
    # significant, attended slope steeper
    return bool(a[0] < 0 and a[1] < 0.05 and b[1] >= 0.05 and a[0] < b[0])


def permute_contrast(d, rng):
    return {**d, "contrast": d["contrast"][rng.permutation(N)]}


STUDY = Study(
    name="W13",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="attended slope -270 ms per unit contrast, unattended -150 -> both -150 (equal slopes); participant speed shared across conditions, noise and contrast range unchanged"),
    },
    controls=[Control("permute_contrast", ["C"], transform=permute_contrast)],
)
