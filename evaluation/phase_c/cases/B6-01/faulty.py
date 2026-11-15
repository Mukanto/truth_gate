"""C27: Prenatal exposure raises adult open-field activity: the mean activity score of offspring of exposed dams is higher than that of offspring of control dams, and a two-sample t test of the difference between the two group means gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, exposure_effect):
    dams, pups = 20, 8
    exposed = np.zeros(dams, dtype=bool)
    exposed[rng.permutation(dams)[:10]] = True
    litter = rng.normal(0.0, 15.0, dams)                    # litter effect shared by the pups of one dam
    pup = rng.normal(0.0, 18.0, (dams, pups))
    activity = 100.0 + (litter + exposure_effect * exposed)[:, None] + pup
    activity = np.clip(activity, 1.0, None)
    return {"activity": activity.astype(np.float64), "exposed": exposed}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 25.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: activity (20, 8) float, open-field activity score (distance travelled, arbitrary units) measured
    in adulthood on each pup (axis 1) of each dam (axis 0); exposed (20,) bool, whether the dam received the
    exposure during pregnancy.
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

    v = np.asarray(d["activity"], dtype=float)
    g = np.asarray(d["exposed"], dtype=bool)
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
    name="C27",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of prenatal exposure on activity set to 0 (was +25 units); litter effects and pup-to-pup variability kept"),
    },
    controls=[
        Control("permute_exposed_across_dams", ["C"], transform=lambda d, rng: {**d, "exposed": _permute_changed(d["exposed"], rng)}),
    ],
)
