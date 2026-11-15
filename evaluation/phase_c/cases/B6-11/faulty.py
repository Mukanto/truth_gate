"""C03: Across subjects, mean resting heart rate and mean salivary cortisol (each subject's mean over the recording days) are positively correlated: the Pearson correlation between the two subject means is positive, and a test of that correlation gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, r):
    s, days = 16, 10
    z1 = rng.normal(0.0, 1.0, s)
    z2 = rng.normal(0.0, 1.0, s)
    hr_trait = 66.0 + 8.0 * z1                                         # subject's habitual heart rate
    cort_trait = 15.0 + 3.5 * (r * z1 + np.sqrt(1.0 - r * r) * z2)     # subject's habitual cortisol
    e1 = rng.normal(0.0, 1.0, (s, days))
    e2 = rng.normal(0.0, 1.0, (s, days))
    heart_rate = hr_trait[:, None] + 4.0 * e1
    # day-to-day fluctuations are weakly shared within a subject (0.3) in both worlds
    cortisol = cort_trait[:, None] + 3.5 * (0.3 * e1 + np.sqrt(1.0 - 0.09) * e2)
    return {"heart_rate": heart_rate, "cortisol": np.maximum(cortisol, 1.0)}


def plus(rng):
    """The claim is true: the subjects' habitual levels correlate 0.75 (about 0.70 between observed means)."""
    return _gen(rng, 0.75)


def minus(rng):
    """The claim is false: the subjects' habitual levels are uncorrelated; day-level structure as in plus."""
    return _gen(rng, 0.0)


def _permute_subjects(d, rng):
    n = d["cortisol"].shape[0]
    return {**d, "cortisol": d["cortisol"][rng.permutation(n)]}


def criterion(d):
    """Data keys: heart_rate, float (16 subjects, 10 days), resting heart rate in beats per minute of each
    subject on each recording day; cortisol, float (16, 10), morning salivary cortisol concentration of each
    subject on each recording day.
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

    h = np.asarray(d["heart_rate"], dtype=float)
    c = np.asarray(d["cortisol"], dtype=float)
    if not (np.all(np.isfinite(h)) and np.all(np.isfinite(c))):
        return None
    if h.shape[0] < 3:
        return None
    x = h.ravel()
    y = c.ravel()
    xc = x - x.mean()
    yc = y - y.mean()
    sxx = (xc ** 2).sum()
    syy = (yc ** 2).sum()
    if not (sxx > 0.0 and syy > 0.0):
        return None
    r = (xc * yc).sum() / np.sqrt(sxx * syy)
    df = x.size - 2.0
    t = r * np.sqrt(df / (1.0 - r * r))
    return bool(r > 0.0 and p2t(t, df) < 0.05)


STUDY = Study(
    name="C03",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="between-subject correlation of habitual heart rate and habitual cortisol set to zero"),
    },
    controls=[Control("permute_cortisol_subjects", ["C"], transform=_permute_subjects)],
    relational=[("heart_rate", "cortisol")],
)
