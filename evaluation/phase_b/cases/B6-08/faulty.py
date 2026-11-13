"""W50: Trial-by-trial neural activity in a frontal region is positively related to reaction time: the correlation between activity and reaction time is greater than zero at the one-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, T = 12, 25


def _gen(rng, rho_w):
    z_s = rng.standard_normal(S)
    subj_rt = 60.0 * z_s                                                  # participant speed
    subj_act = 0.6 * (0.6 * z_s + 0.8 * rng.standard_normal(S))          # participant activity level, correlated 0.6 with speed
    e_rt = rng.standard_normal((S, T))
    e_act = rho_w * e_rt + np.sqrt(1.0 - rho_w ** 2) * rng.standard_normal((S, T))   # trial-level link, 0.2 in plus
    t = (np.arange(T) - (T - 1) / 2.0)[None, :]                           # trial position: fatigue drift in both measures
    rt = 500.0 + subj_rt[:, None] + 2.5 * t + 80.0 * e_rt
    act = subj_act[:, None] + 0.04 * t + 1.0 * e_act
    return {"reaction_time": rt, "activity": act}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.2)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: reaction_time (12, 25) reaction time on each trial, axes (participants, trials), trials in time order
    within a participant; activity (12, 25) frontal activity estimate on the same trial.
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

    rt = np.asarray(d["reaction_time"], dtype=float)
    act = np.asarray(d["activity"], dtype=float)

    # all trials of all participants pooled into one correlation, one-sided 0.05
    r = _corr(act, rt)
    if r is None:
        return None
    return bool(r[0] > 0 and _rp2(r[0], r[1]) / 2.0 < 0.05)


def permute_trials_within_participant(d, rng):
    idx = np.argsort(rng.random((S, T)), axis=1)
    return {**d, "activity": np.take_along_axis(d["activity"], idx, axis=1)}


STUDY = Study(
    name="W50",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="trial-by-trial link between activity noise and reaction-time noise (0.2) -> 0; the between-participant correlation of mean activity and mean reaction time (0.6), the shared fatigue drift across trials and all variances unchanged"),
    },
    controls=[Control("permute_trials_within_participant", ["C"], transform=permute_trials_within_participant)],
)
