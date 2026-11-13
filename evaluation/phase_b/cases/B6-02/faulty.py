"""W48: A drug changes the evoked response more in visual cortex than in auditory cortex: the drug-minus-placebo difference in response amplitude is larger in the visual region than in the auditory region across 16 participants, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 16


def _gen(rng, d_vis, d_aud):
    b0 = rng.standard_normal(N)
    b1 = 0.4 * b0 + np.sqrt(1.0 - 0.4 ** 2) * rng.standard_normal(N)       # region baselines correlate 0.4
    zv = rng.standard_normal(N)
    za = 0.3 * zv + np.sqrt(1.0 - 0.3 ** 2) * rng.standard_normal(N)       # individual drug responses correlate 0.3
    n = 0.25 * rng.standard_normal((4, N))
    vis_base = 3.0 + 1.0 * b0
    aud_base = 2.5 + 1.0 * b1
    visual_placebo = vis_base + n[0]
    visual_drug = vis_base + d_vis + 0.3 * zv + n[1]
    auditory_placebo = aud_base + n[2]
    auditory_drug = aud_base + d_aud + 0.3 * za + n[3]
    return {"visual_placebo": visual_placebo, "visual_drug": visual_drug, "auditory_placebo": auditory_placebo, "auditory_drug": auditory_drug}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.6, 0.15)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.375, 0.375)


def criterion(d):
    """Data keys: visual_placebo (16,) evoked amplitude in visual region under placebo, axis participants;
    visual_drug (16,) same participants, visual region under drug; auditory_placebo (16,) auditory region under placebo;
    auditory_drug (16,) auditory region under drug. Every participant is measured in both regions and both conditions.
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

    dv = np.asarray(d["visual_drug"], dtype=float) - np.asarray(d["visual_placebo"], dtype=float)
    da = np.asarray(d["auditory_drug"], dtype=float) - np.asarray(d["auditory_placebo"], dtype=float)

    a = _one(dv)
    b = _one(da)
    if a is None or b is None:
        return None
    # drug effect significant in the visual region (two-sided 0.05, positive), not significant in the auditory region
    return bool(a[1] < 0.05 and a[0] > 0 and b[1] >= 0.05 and a[0] > b[0])


def swap_regions(d, rng):
    m = rng.random(N) < 0.5
    return {**d,
            "visual_placebo": np.where(m, d["auditory_placebo"], d["visual_placebo"]),
            "visual_drug": np.where(m, d["auditory_drug"], d["visual_drug"]),
            "auditory_placebo": np.where(m, d["visual_placebo"], d["auditory_placebo"]),
            "auditory_drug": np.where(m, d["visual_drug"], d["auditory_drug"])}


STUDY = Study(
    name="W48",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="mean drug effect 0.6 (visual) and 0.15 (auditory) -> 0.375 in both regions (equal, so each region alone still shows a drug effect); baselines, individual response variability, noise and 16 participants unchanged"),
    },
    controls=[Control("swap_regions", ["C"], transform=swap_regions)],
)
