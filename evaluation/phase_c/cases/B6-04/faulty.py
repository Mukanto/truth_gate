"""C10: Giving the compound in the drinking water reduces body-weight gain: the mean weight gain of animals receiving the compound is lower than that of controls, and a Welch two-sample t test of the difference between the two group means gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, effect):
    cages, animals = 40, 2
    treated = np.zeros(cages, dtype=bool)
    treated[rng.permutation(cages)[:20]] = True                  # 20 cages get the compound
    cage = rng.normal(0.0, 3.5, (cages, 1))                      # shared cage environment
    animal = rng.normal(0.0, 3.0, (cages, animals))
    gain = 30.0 + cage + animal - effect * treated[:, None]
    return {"weight_gain": gain, "treated": treated}


def plus(rng):
    """The claim is true: the compound lowers weight gain by 4.5 g (cage SD 3.5 g, animal SD 3 g)."""
    return _gen(rng, 4.5)


def minus(rng):
    """The claim is false: the compound has no effect on weight gain; cage and animal variation as in plus."""
    return _gen(rng, 0.0)


def _permute_treatment(d, rng):
    return {**d, "treated": d["treated"][rng.permutation(d["treated"].shape[0])]}


def criterion(d):
    """Data keys: weight_gain, float (40 cages, 2 animals), body-weight gain in grams over the study of each
    animal housed in each cage; treated, bool (40,), whether the drinking water supplied to the cage
    contained the compound.
    Holds when the claim is supported by the data. Written by someone else."""
    def lgam(x):
        g = (676.5203681218851, -1259.1392167224028, 771.3234287776531, -176.6150291621406,
             12.507343278686905, -0.13857109526572012, 9.984369578019572e-6, 1.5056327351493116e-7)
        x = x - 1.0
        a = 0.99999999999980993
        for i, gi in enumerate(g):
            a += gi / (x + i + 1.0)
        t = x + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a)

    def betacf(a, b, x):
        tiny = 1e-300
        c = 1.0
        dd = 1.0 - (a + b) * x / (a + 1.0)
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 500):
            m2 = 2 * m
            aa = m * (b - m) * x / ((a - 1.0 + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + 1.0 + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-14:
                break
        return h

    def p2t(t, df):
        # two-sided p value of Student's t statistic with df degrees of freedom
        x = df / (df + t * t)
        if x >= 1.0:
            return 1.0
        if x <= 0.0:
            return 0.0
        a, b = 0.5 * df, 0.5
        lb = lgam(a + b) - lgam(a) - lgam(b) + a * np.log(x) + b * np.log1p(-x)
        if x < (a + 1.0) / (a + b + 2.0):
            return float(np.exp(lb) * betacf(a, b, x) / a)
        return float(1.0 - np.exp(lb) * betacf(b, a, 1.0 - x) / b)

    v = np.asarray(d["weight_gain"], dtype=float)
    g = np.asarray(d["treated"], dtype=bool)
    if not np.all(np.isfinite(v)):
        return None
    if g.sum() < 2 or (~g).sum() < 2:
        return None
    x = v[g].ravel()
    y = v[~g].ravel()
    nx, ny = x.size, y.size
    a = x.var(ddof=1) / nx
    b = y.var(ddof=1) / ny
    se2 = a + b
    if not se2 > 0.0:
        return None
    df = se2 ** 2 / (a * a / (nx - 1.0) + b * b / (ny - 1.0))
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() < y.mean() and p2t(t, df) < 0.05)


STUDY = Study(
    name="C10",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of the compound on weight gain set to zero"),
    },
    controls=[Control("permute_treatment_across_cages", ["C"], transform=_permute_treatment)],
    relational=[("weight_gain", "treated")],
)
