"""W22: In patients whose systolic blood pressure is at least 150 mmHg at entry, the drug lowers systolic pressure by at least 5 mmHg over 12 weeks. The claim holds when the estimated lowering is at least 5 mmHg and one-sided p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 160


def _gen(rng, eff):
    drug = rng.random(N) < 0.5
    true = 156.0 + 13.0 * rng.standard_normal(N)             # usual pressure
    e0 = rng.standard_normal(N)
    e1 = rng.standard_normal(N)
    ind = rng.standard_normal(N)
    sbp0 = true + 11.0 * e0                                  # entry reading, measurement noise sd 11
    resp = eff * (-10.0 + 4.0 * ind)                         # drug effect beyond placebo, mmHg
    sbp1 = true - 2.0 + drug * resp + 11.0 * e1              # placebo response of 2 mmHg in both arms
    return {"sbp": np.column_stack([sbp0, sbp1]), "drug": drug.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: sbp (160, 2) systolic pressure in mmHg, axes (patients, visits): visit 0 = entry, visit 1 = after 12
    weeks; drug (160,) bool, True for patients given the drug, False for placebo (about 80 per arm).
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

    sbp = np.asarray(d["sbp"], dtype=float)
    drug = np.asarray(d["drug"], dtype=bool)
    if not np.all(np.isfinite(sbp)):
        return None
    change = sbp[:, 0] - sbp[:, 1]                             # lowering over 12 weeks
    hi = sbp[:, 0] >= 150.0
    x = change[hi & drug]
    if len(x) < 5:
        return None
    sd = x.std(ddof=1)
    if not sd > 0:
        return None
    t = x.mean() / (sd / np.sqrt(len(x)))
    return bool(x.mean() >= 5.0 and _tsf(t, len(x) - 1) < 0.05)


def permute_drug_labels(d, rng):
    return {**d, "drug": d["drug"][rng.permutation(N)]}


STUDY = Study(
    name="W22",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="drug effect beyond placebo -10 mmHg (sd 4) -> 0; the entry measurement noise (regression to the mean), the 2 mmHg placebo response and the randomisation are unchanged"),
    },
    controls=[Control("permute_drug_labels", ["C"], transform=permute_drug_labels)],
)
