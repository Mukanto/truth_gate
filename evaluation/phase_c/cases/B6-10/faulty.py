"""C23: The drug improves motor coordination: the mean time spent on the rotarod is longer in the treatment group than in the control group, and a two-tailed two-sample t test of the difference between the two group means gives p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, drug_effect_s):
    rats, days = 10, 3
    treated = np.zeros(rats, dtype=bool)
    treated[rng.permutation(rats)[:5]] = True
    rat_level = rng.normal(0.0, 22.0, rats)                 # stable differences between rats
    learning = np.array([0.0, 15.0, 28.0])                  # improvement over the test days, both groups
    day_noise = rng.normal(0.0, 12.0, (rats, days))
    latency = 115.0 + learning[None, :] + (rat_level + drug_effect_s * treated)[:, None] + day_noise
    latency = np.clip(latency, 5.0, 300.0)                  # 300 s cut-off of the apparatus
    return {"latency": latency.astype(np.float64), "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 55.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: latency (10, 3) float, time in seconds that each rat (axis 0) stayed on the rotarod on each of
    the consecutive test days (axis 1); treated (10,) bool, True for rats in the treatment group, False for the
    control group.
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

    v = np.asarray(d["latency"], dtype=float)
    g = np.asarray(d["treated"], dtype=bool)
    if not np.all(np.isfinite(v)):
        return None
    if g.sum() < 2 or (~g).sum() < 2:
        return None
    x = v[g].ravel()
    y = v[~g].ravel()
    nx, ny = x.size, y.size
    df = nx + ny - 2.0
    s2 = ((nx - 1.0) * x.var(ddof=1) + (ny - 1.0) * y.var(ddof=1)) / df
    se2 = s2 * (1.0 / nx + 1.0 / ny)
    if not se2 > 0.0:
        return None
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() > y.mean() and p2t(t, df) < 0.05)


STUDY = Study(
    name="C23",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of the drug on rotarod time set to 0 s (was +55 s); between-rat differences, learning over days and day-to-day noise kept"),
    },
    controls=[
        Control("permute_treated_across_rats", ["C"], transform=lambda d, rng: {**d, "treated": _permute_changed(d["treated"], rng)}),
    ],
)
