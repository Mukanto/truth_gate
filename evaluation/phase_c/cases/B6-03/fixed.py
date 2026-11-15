"""C17: Spine density on hippocampal CA1 pyramidal neurons rises with the dose of the drug the animal received: the regression slope of spine density on dose is positive, and a test of the slope gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, slope):
    animals, sections, neurons = 12, 4, 25
    # four dose groups of three animals (mg/kg), in random animal order
    dose = rng.permutation(np.repeat(np.array([0.0, 5.0, 10.0, 20.0]), 3))
    animal = rng.normal(0.0, 1.0, (animals, 1, 1))           # between-animal variability
    section = rng.normal(0.0, 0.5, (animals, sections, 1))   # between-section variability
    neuron = rng.normal(0.0, 2.0, (animals, sections, neurons))
    density = 11.0 + slope * dose[:, None, None] + animal + section + neuron
    density = np.clip(density, 0.5, None)
    return {"spine_density": density.astype(np.float64), "dose": dose.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.16)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: spine_density (12, 4, 25) float, spines per 10 micrometres of dendrite on each sampled neuron
    (axis 2), in each histological section (axis 1), of each animal (axis 0); dose (12,) float, dose of the drug
    (mg/kg) that each animal received.
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

    s = np.asarray(d["spine_density"], dtype=float)
    dose = np.asarray(d["dose"], dtype=float)
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(dose))):
        return None
    if dose.size < 3:
        return None
    s = s.reshape(s.shape[0], -1)
    x = dose
    y = s.mean(axis=1)
    xc = x - x.mean()
    sxx = (xc ** 2).sum()
    if not sxx > 0.0:
        return None
    yc = y - y.mean()
    slope = (xc * yc).sum() / sxx
    df = x.size - 2.0
    s2 = ((yc - slope * xc) ** 2).sum() / df
    if not s2 > 0.0:
        return None
    t = slope / np.sqrt(s2 / sxx)
    return bool(slope > 0.0 and p2t(t, df) < 0.05)


STUDY = Study(
    name="C17",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="slope of spine density on dose set to 0 (was 0.16 spines/10 um per mg/kg); animal, section and neuron variability kept"),
    },
    controls=[
        Control("permute_dose_across_animals", ["C"], transform=lambda d, rng: {**d, "dose": _permute_changed(d["dose"], rng)}),
    ],
)
