"""W31: Applying the drug to brain slices increases the mean amplitude of synaptic responses relative to vehicle: mean response amplitude is higher with the drug than with vehicle, in slices taken from the same animals, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

A, C = 8, 25


def _gen(rng, eff):
    animal = 0.35 * rng.standard_normal((A, 1))              # animal effect, shared by both conditions
    ind = 0.20 * rng.standard_normal((A, 1))                 # animal-specific size of the drug effect
    e_v = rng.standard_normal((A, C))
    e_d = rng.standard_normal((A, C))
    amp_vehicle = 20.0 * np.exp(animal + 0.45 * e_v)
    amp_drug = 20.0 * np.exp(animal + eff * (0.30 + ind) + 0.45 * e_d)
    return {"amp_drug": amp_drug, "amp_vehicle": amp_vehicle}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: amp_drug (8, 25) response amplitude of each cell recorded in drug-treated tissue, axes (animals, recorded
    cells per animal); amp_vehicle (8, 25) response amplitude of each cell recorded in vehicle-treated tissue from the same
    animals.
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

    dr = np.asarray(d["amp_drug"], dtype=float)
    ve = np.asarray(d["amp_vehicle"], dtype=float)

    # every (animal, cell index) pair is treated as an independent pair
    r = _one(dr - ve)
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)


def swap_conditions_within_animals(d, rng):
    m = rng.random((A, 1)) < 0.5
    return {**d, "amp_drug": np.where(m, d["amp_vehicle"], d["amp_drug"]), "amp_vehicle": np.where(m, d["amp_drug"], d["amp_vehicle"])}


STUDY = Study(
    name="W31",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="drug raises amplitude by exp(0.30) = 1.35 on average (animal-specific sd 0.2) -> no drug effect; animal effects shared between conditions (sd 0.35), cell noise (sd 0.45) and 8 animals x 25 cells unchanged"),
    },
    controls=[Control("swap_conditions_within_animals", ["C"], transform=swap_conditions_within_animals)],
)
