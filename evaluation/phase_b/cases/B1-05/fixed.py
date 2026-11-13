"""W34: In a 50-voxel region of medial prefrontal cortex, the voxels that track trait social anxiety have a mean activity that predicts the trait: the least-squares slope of the standardized trait score on the standardized mean activity of those voxels across the 16 subjects is at least 0.50, with one-sided p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, Q, V = 16, 2, 50


def _gen(rng, eff):
    z = rng.standard_normal(S)
    rel = rng.random(V) < 0.40                               # voxels that truly track the trait
    beta = eff * np.where(rel, 0.55 + 0.20 * rng.random(V), 0.0 * rng.random(V))
    u = 0.5 * rng.standard_normal((S, 1))                    # stable subject-level activation shared by voxels
    w = 0.4 * rng.standard_normal((S, V))                    # stable subject-by-voxel component (same in both sessions)
    e = rng.standard_normal((S, Q, V))                       # session noise
    act = beta[None, None, :] * z[:, None, None] + u[:, None, :] + w[:, None, :] + 0.7 * e
    trait = 40.0 + 10.0 * z
    return {"act": act, "trait": trait}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: act (16, 2, 50) activation (beta) to a social-evaluation task, axes (subjects, sessions, voxels), two
    scanning sessions on separate days; trait (16,) questionnaire social-anxiety score per subject.
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

    def _tq(alpha, df):
        # t value whose upper-tail probability is alpha
        lo, hi = 0.0, 1e3
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if _tsf(mid, df) > alpha:
                lo = mid
            else:
                hi = mid
        return hi

    def _corr(a, y):
        # Pearson correlation of every column of a with y
        a = a - a.mean(axis=0)
        y = y - y.mean()
        den = np.sqrt((a ** 2).sum(axis=0) * (y ** 2).sum())
        return np.where(den > 0, (a * y[:, None]).sum(axis=0) / np.where(den > 0, den, 1.0), 0.0)

    act = np.asarray(d["act"], dtype=float)
    trait = np.asarray(d["trait"], dtype=float)
    if not (np.all(np.isfinite(act)) and np.all(np.isfinite(trait))):
        return None
    n = act.shape[0]
    sel_act, ev_act = act[:, 0], act[:, 1]
    if not np.var(trait) > 0:
        return None
    r_sel = _corr(sel_act, trait)
    tt = r_sel * np.sqrt((n - 2) / np.maximum(1.0 - r_sel ** 2, 1e-12))
    keep = (r_sel > 0) & (tt > _tq(0.005, n - 2))              # positive, two-sided p < 0.01
    if not keep.any():
        return None
    m = ev_act[:, keep].mean(axis=1)
    if not np.var(m) > 0:
        return None
    zm = (m - m.mean()) / m.std()
    zt = (trait - trait.mean()) / trait.std()
    slope = (zm * zt).sum() / (zm * zm).sum()                  # least-squares slope of z(trait) on z(activity)
    ts = slope * np.sqrt((n - 2) / max(1.0 - slope ** 2, 1e-12))
    return bool(slope >= 0.50 and _tsf(ts, n - 2) < 0.05)


def permute_trait(d, rng):
    return {**d, "trait": d["trait"][rng.permutation(S)]}


STUDY = Study(
    name="W34",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="40% of voxels carry the trait (loading 0.55 to 0.75, mean-activity correlation about 0.7) -> no voxel carries the trait; stable subject effects, session noise and 16 subjects x 2 sessions unchanged"),
    },
    controls=[Control("permute_trait", ["C"], transform=permute_trait)],
)
