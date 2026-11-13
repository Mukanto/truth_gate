"""W25: Adding nutrients to experimental ponds raises algal biomass: mean biomass in the fertilised ponds is higher than in the unfertilised ponds, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

NP, NS = 4, 10


def _gen(rng, eff):
    pf = 0.4 * rng.standard_normal((NP, 1))                  # pond random effect (log scale), the unit of replication
    pu = 0.4 * rng.standard_normal((NP, 1))
    sf = 0.3 * rng.standard_normal((NP, NS))                 # water-sample noise
    su = 0.3 * rng.standard_normal((NP, NS))
    fert = 20.0 * np.exp(eff * 0.9 + pf + sf)
    unfert = 20.0 * np.exp(pu + su)
    return {"biomass_fertilised": fert, "biomass_unfertilised": unfert}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: biomass_fertilised (4, 10) algal biomass per water sample, axes (ponds, water samples per pond),
    fertilised ponds; biomass_unfertilised (4, 10) same layout, unfertilised ponds.
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

    def _two(x, y):
        # two-sample Student t test (pooled variance), mean(x) - mean(y): (difference, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n1, n2 = x.size, y.size
        if n1 < 2 or n2 < 2 or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        sp2 = ((n1 - 1) * x.var(ddof=1) + (n2 - 1) * y.var(ddof=1)) / (n1 + n2 - 2)
        if not sp2 > 1e-24:
            return None
        diff = x.mean() - y.mean()
        return float(diff), _p2(diff / np.sqrt(sp2 * (1.0 / n1 + 1.0 / n2)), n1 + n2 - 2)

    f = np.asarray(d["biomass_fertilised"], dtype=float)
    u = np.asarray(d["biomass_unfertilised"], dtype=float)

    # the pond is the unit of replication: samples are averaged within pond
    r = _two(f.mean(axis=1), u.mean(axis=1))
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)


def reassign_ponds(d, rng):
    both = np.concatenate([d["biomass_fertilised"], d["biomass_unfertilised"]], axis=0)[rng.permutation(2 * NP)]
    return {**d, "biomass_fertilised": both[:NP].copy(), "biomass_unfertilised": both[NP:].copy()}


STUDY = Study(
    name="W25",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="fertilisation multiplies biomass by exp(0.9) = 2.5 -> multiplier 1; pond effects (sd 0.4), sample noise (sd 0.3) and the 4 ponds x 10 samples layout unchanged"),
    },
    controls=[Control("reassign_ponds", ["C"], transform=reassign_ponds)],
)
