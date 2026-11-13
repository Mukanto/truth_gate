"""W03: Participants who received the treatment score higher than controls on the outcome: a one-sided Welch t test of treated versus control gives p < 0.05 once recruitment of the planned sample is complete."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 30


def _gen(rng, eff):
    drift = 3.0 * np.arange(N) / N                   # slow drift with recruitment order, both arms
    treated = 50.0 + drift + eff + 10.0 * rng.standard_normal(N)
    control = 50.0 + drift + 10.0 * rng.standard_normal(N)
    return {"treated": treated, "control": control}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 8.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: treated (30,) outcome score of each treated participant, rows in order of recruitment;
    control (30,) outcome score of each control participant, rows in order of recruitment.
    Holds when the claim is supported by the data. Written by someone else."""
    def _lgam(z):
        c = (676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
             12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)
        z = z - 1.0
        x = 0.99999999999980993
        for i in range(8):
            x += c[i] / (z + i + 1.0)
        t = z + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

    def _betacf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        if abs(dd) < tiny:
            dd = tiny
        dd = 1.0 / dd
        h = dd
        for m in range(1, 300):
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

    def _ibeta(a, b, x):
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lgam(a + b) - _lgam(a) - _lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return bt * _betacf(a, b, x) / a
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b

    def welch_p(x, y):
        """One-sided Welch t test, H1: mean(x) > mean(y); exact t tail via the regularised incomplete beta function."""
        nx, ny = x.shape[0], y.shape[0]
        vx, vy = x.var(ddof=1) / nx, y.var(ddof=1) / ny
        if not (vx + vy > 1e-24):
            return None
        t = (x.mean() - y.mean()) / np.sqrt(vx + vy)
        df = (vx + vy) ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1))
        if t == 0.0:
            return 0.5
        tail = 0.5 * _ibeta(0.5 * df, 0.5, df / (df + t * t))
        return float(tail if t > 0 else 1.0 - tail)

    a = np.asarray(d["treated"], dtype=float)
    b = np.asarray(d["control"], dtype=float)
    if not (np.isfinite(a).all() and np.isfinite(b).all()) or a.shape[0] < 30 or b.shape[0] < 30:
        return None
    # two looks: at 20 per group, and again at 30 per group; the result that is reported is the one with the smaller p
    ps = [welch_p(a[:n], b[:n]) for n in (20, 30)]
    if any(p is None for p in ps):
        return None
    return bool(min(ps) < 0.05)


def pool_and_resplit(d, rng):
    pooled = np.concatenate([d["treated"], d["control"]])[rng.permutation(2 * N)]
    return {**d, "treated": pooled[:N].copy(), "control": pooled[N:].copy()}


STUDY = Study(
    name="W03",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect 8 points (d = 0.8) -> 0; sd, drift and sample sizes unchanged"),
    },
    controls=[Control("pool_and_resplit", ["C"], transform=pool_and_resplit)],
)
