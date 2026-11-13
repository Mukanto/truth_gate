"""W21: Of the 120 cells in a calcium-imaging field of view, those that respond to the tone are mostly genuine responders: at least 70% of them show a larger mean fluorescence after tone onset than before it."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

C, T = 120, 30


def _gen(rng, eff):
    kind = rng.random(C)
    resp = kind < 0.30                                       # excited cells
    supp = (kind >= 0.30) & (kind < 0.37)                    # suppressed cells, present in both worlds
    amp = np.exp(np.log(0.10) + 0.4 * rng.standard_normal(C))
    cb = 0.05 * rng.standard_normal(C)                       # cell baseline
    shared = 0.12 * rng.standard_normal((C, T))              # slow fluctuation shared by the pre and post windows
    n_pre = 0.10 * rng.standard_normal((C, T))
    n_post = 0.10 * rng.standard_normal((C, T))
    shift = eff * resp * amp - supp * 0.5 * amp
    pre = cb[:, None] + shared + n_pre
    post = cb[:, None] + shared + shift[:, None] + n_post
    return {"pre": pre, "post": post}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: pre (120, 30) mean fluorescence (dF/F) in the 1 s before tone onset, axes (cells, trials);
    post (120, 30) mean fluorescence (dF/F) in the 1 s after tone onset, axes (cells, trials).
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

    pre = np.asarray(d["pre"], dtype=float)
    post = np.asarray(d["post"], dtype=float)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    nt = pre.shape[1]
    sel_t, ev_t = np.arange(nt), np.arange(nt)
    diff = post - pre
    ds = diff[:, sel_t]
    k = ds.shape[1]
    sd = ds.std(axis=1, ddof=1)
    t = np.where(sd > 0, ds.mean(axis=1) / (np.where(sd > 0, sd, 1.0) / np.sqrt(k)), 0.0)
    resp = np.array([(x > 0) and (_tsf(x, k - 1) < 0.05) for x in t])   # post > pre, one-sided p < 0.05
    if resp.sum() < 5:
        return None
    prop = np.mean(diff[resp][:, ev_t].mean(axis=1) > 0)
    return bool(prop >= 0.70)


def swap_pre_post(d, rng):
    m = rng.random((C, T)) < 0.5
    return {**d, "pre": np.where(m, d["post"], d["pre"]), "post": np.where(m, d["pre"], d["post"])}


STUDY = Study(
    name="W21",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="30% of cells are excited by the tone (dF/F about +0.1) -> no cell is excited; the 7% of cells that are suppressed by the tone, the trial noise (sd 0.1) and the shared slow fluctuation are unchanged"),
    },
    controls=[Control("swap_pre_post", ["C"], transform=swap_pre_post)],
)
