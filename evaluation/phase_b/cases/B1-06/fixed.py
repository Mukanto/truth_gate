"""W09: Among 28 subjects (14 high-anxiety and 14 low-anxiety by interview), in the voxels of a 40-voxel amygdala region that react more strongly to threatening pictures in the high-anxiety group, the group difference in mean reactivity has a Welch t statistic of at least 3.0."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, V = 28, 40


def _gen(rng, eff):
    high = (np.arange(S) % 2) == 0                           # groups alternate: True, False, True, ...
    sel = rng.random(V) < 0.30                               # voxels with a real group difference
    delta = np.where(sel, 0.75 + 0.15 * rng.standard_normal(V), 0.0 * rng.standard_normal(V))
    mu = 0.3 + 0.2 * rng.standard_normal(V)                  # average threat reactivity per voxel
    u = 0.25 * rng.standard_normal((S, 1))                   # subject offset shared by all voxels
    e = rng.standard_normal((S, V))
    react = mu[None, :] + u + eff * high[:, None] * delta[None, :] + e
    return {"react": react, "high_anx": high}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: react (28, 40) response to threat minus neutral pictures, axes (subjects, voxels);
    high_anx (28,) bool, True for the 14 high-anxiety subjects, subjects ordered so that groups alternate.
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

    def _welch(x, y):
        # Welch t statistic and degrees of freedom along axis 0
        nx, ny = x.shape[0], y.shape[0]
        vx = x.var(axis=0, ddof=1) / nx
        vy = y.var(axis=0, ddof=1) / ny
        se2 = vx + vy
        ok = se2 > 0
        t = np.where(ok, (x.mean(axis=0) - y.mean(axis=0)) / np.sqrt(np.where(ok, se2, 1.0)), 0.0)
        df = np.where(ok, se2 ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1) + 1e-300), 1.0)
        return t, df

    react = np.asarray(d["react"], dtype=float)
    high = np.asarray(d["high_anx"], dtype=bool)
    if not np.all(np.isfinite(react)):
        return None
    n = react.shape[0]
    ih, il = np.flatnonzero(high), np.flatnonzero(~high)
    if len(ih) < 3 or len(il) < 3:
        return None
    allidx = np.arange(n)
    half_a = np.concatenate([ih[0::2], il[0::2]])
    half_b = np.concatenate([ih[1::2], il[1::2]])
    folds = [(half_a, half_b), (half_b, half_a)]
    val = np.full(n, np.nan)
    for sel_idx, ev_idx in folds:
        gh = sel_idx[high[sel_idx]]
        gl = sel_idx[~high[sel_idx]]
        if len(gh) < 3 or len(gl) < 3:
            return None
        t, df = _welch(react[gh], react[gl])
        keep = np.array([(t[v] > 0) and (_tsf(t[v], df[v]) < 0.05) for v in range(len(t))])   # higher in the high group, one-sided p < 0.05
        if not keep.any():
            return None
        val[ev_idx] = react[ev_idx][:, keep].mean(axis=1)
    a, b = val[high], val[~high]
    if not (a.var(ddof=1) + b.var(ddof=1) > 0):
        return None
    t_fin, _ = _welch(a, b)
    return bool(t_fin >= 3.0)


def permute_subjects(d, rng):
    return {**d, "react": d["react"][rng.permutation(S)]}


STUDY = Study(
    name="W09",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="12 of 40 voxels carry a true high-minus-low anxiety difference of about 0.75 -> no voxel has any group difference; voxel noise (sd 1), subject offsets and the alternating group layout unchanged"),
    },
    controls=[Control("permute_subjects", ["C"], transform=permute_subjects)],
)
