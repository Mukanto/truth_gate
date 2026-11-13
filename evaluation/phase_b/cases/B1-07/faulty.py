"""W15: In a panel of 60 candidate genes, the genes that differ between tumour and normal tissue have a mean absolute log2 fold change of at least 0.5, in 20 tumour and 20 normal samples."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, G = 40, 60


def _gen(rng, eff):
    tumour = rng.permutation(np.arange(S) < 20)
    de = rng.random(G) < 0.25                                # about 15 genes truly differ
    lfc = (0.5 + 0.5 * rng.random(G)) * rng.choice(np.array([-1.0, 1.0]), G)   # |log2 FC| between 0.5 and 1
    mu = 8.0 + 1.5 * rng.standard_normal(G)
    sd = 0.5 + 0.4 * rng.random(G)                           # per-gene noise sd (log2 units)
    e = rng.standard_normal((S, G))
    expr = mu[None, :] + sd[None, :] * e + tumour[:, None] * (eff * de * lfc)[None, :]
    return {"expr": expr, "tumour": tumour.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (40, 60) log2 expression level, one value per sample and gene, axes (samples, genes);
    tumour (40,) bool, True for the 20 tumour samples, False for the 20 normal samples.
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

    expr = np.asarray(d["expr"], dtype=float)
    tum = np.asarray(d["tumour"], dtype=bool)
    if not np.all(np.isfinite(expr)):
        return None
    n = expr.shape[0]
    it, inn = np.flatnonzero(tum), np.flatnonzero(~tum)
    if len(it) < 4 or len(inn) < 4:
        return None
    allidx = np.arange(n)
    half_a = np.concatenate([it[0::2], inn[0::2]])
    half_b = np.concatenate([it[1::2], inn[1::2]])
    folds = [(allidx, allidx)]
    vals = []
    for sel_idx, ev_idx in folds:
        st, sn = sel_idx[tum[sel_idx]], sel_idx[~tum[sel_idx]]
        et, en = ev_idx[tum[ev_idx]], ev_idx[~tum[ev_idx]]
        t, df = _welch(expr[st], expr[sn])
        keep = np.array([2.0 * _tsf(abs(t[g]), df[g]) < 0.05 for g in range(len(t))])   # two-sided p < 0.05
        if keep.any():
            sign = np.sign(expr[st].mean(axis=0) - expr[sn].mean(axis=0))
            fc = expr[et].mean(axis=0) - expr[en].mean(axis=0)
            vals.append(np.mean((sign * fc)[keep]))
    if not vals:
        return None
    return bool(np.mean(vals) >= 0.5)


def permute_tumour_labels(d, rng):
    return {**d, "tumour": d["tumour"][rng.permutation(S)]}


STUDY = Study(
    name="W15",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="about 15 of 60 genes truly differ with |log2 FC| 0.5 to 1 -> no gene differs between tumour and normal; gene means, per-gene noise (sd 0.5 to 0.9) and group sizes unchanged"),
    },
    controls=[Control("permute_tumour_labels", ["C"], transform=permute_tumour_labels)],
)
