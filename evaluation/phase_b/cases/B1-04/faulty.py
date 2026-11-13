"""W19: In a 60-voxel region of anterior insula, the voxels whose activity relates positively to trait empathy show a mean Pearson correlation of at least 0.50 with the trait score across the 24 subjects."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, V = 24, 60


def _gen(rng, eff):
    zt = rng.standard_normal(S)
    c = rng.standard_normal(S)                               # global activation level of the subject
    rel = rng.random(V) < 0.40                               # voxels that truly track the trait
    rho = np.where(rel, 0.45 + 0.30 * rng.random(V), 0.0 * rng.random(V))
    e = rng.standard_normal((S, V))
    r = eff * rho
    noise = 0.5 * c[:, None] + np.sqrt(0.75) * e             # unit variance, spatially correlated through c
    act = r[None, :] * zt[:, None] + np.sqrt(1.0 - r ** 2)[None, :] * noise
    trait = 50.0 + 10.0 * zt
    return {"act": act, "trait": trait}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: act (24, 60) activation (beta) to a pain-observation contrast, axes (subjects, voxels);
    trait (24,) questionnaire empathy score per subject.
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
    allidx = np.arange(act.shape[0])
    folds = [(allidx, allidx)]
    means = []
    for sel_idx, ev_idx in folds:
        if not (np.var(trait[sel_idx]) > 0 and np.var(trait[ev_idx]) > 0):
            return None
        r_sel = _corr(act[sel_idx], trait[sel_idx])
        df = len(sel_idx) - 2
        tt = r_sel * np.sqrt(df / np.maximum(1.0 - r_sel ** 2, 1e-12))
        keep = (r_sel > 0) & (tt > _tq(0.005, df))             # positive, two-sided p < 0.01
        if keep.any():
            means.append(_corr(act[ev_idx], trait[ev_idx])[keep].mean())
    if not means:
        return None
    return bool(np.mean(means) >= 0.50)


def permute_trait(d, rng):
    return {**d, "trait": d["trait"][rng.permutation(S)]}


STUDY = Study(
    name="W19",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="40% of voxels have a true correlation with the trait of 0.45 to 0.75 -> every voxel has true correlation 0; unit voxel variance, spatial correlation through a subject-level global factor and the sample of 24 subjects unchanged"),
    },
    controls=[Control("permute_trait", ["C"], transform=permute_trait)],
)
