"""C38: The compound raises the share of cells that respond to stimulation: the proportion of responding cells is higher in treated wells than in untreated wells, and a test of the difference between the two groups gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_WELLS = 12
N_CELLS = 150
N_TREATED = 6
P_UNTREATED = 0.30
P_TREATED = 0.48
WELL_SD = 0.30        # between-well SD of the log-odds of responding (seeding density, dye loading, position)


def _logit(p):
    return np.log(p / (1.0 - p))


def _plate(rng, p_treated):
    treated = np.zeros(N_WELLS, dtype=bool)
    treated[rng.choice(N_WELLS, N_TREATED, replace=False)] = True
    well_effect = rng.normal(0.0, WELL_SD, N_WELLS)
    log_odds = np.where(treated, _logit(p_treated), _logit(P_UNTREATED)) + well_effect
    p_well = 1.0 / (1.0 + np.exp(-log_odds))
    responded = rng.random((N_WELLS, N_CELLS)) < p_well[:, None]
    return {"responded": responded, "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _plate(rng, P_TREATED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _plate(rng, P_UNTREATED)


def _reassign_wells(d, rng):
    # the wells' cell records are dealt out again at random to the treatment labels
    return {**d, "responded": d["responded"][rng.permutation(N_WELLS)]}


def criterion(d):
    """Data keys: responded, bool (12, 150) = (wells, cells), whether each imaged cell of each well showed a
    calcium response to the stimulus; treated, bool (12,), whether the well was given the compound before
    stimulation.
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

    r = np.asarray(d["responded"], dtype=float)
    g = np.asarray(d["treated"], dtype=bool)
    if not np.all(np.isfinite(r)):
        return None
    if g.sum() < 2 or (~g).sum() < 2 or r.shape[1] < 1:
        return None
    x = r[g].ravel()
    y = r[~g].ravel()
    nx, ny = x.size, y.size
    a = x.var(ddof=1) / nx
    b = y.var(ddof=1) / ny
    se2 = a + b
    if not se2 > 0.0:
        return None
    df = se2 ** 2 / (a * a / (nx - 1.0) + b * b / (ny - 1.0))
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() > y.mean() and p2t(t, df) < 0.05)


STUDY = Study(
    name="C38",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the compound's effect on the response probability is set to none (treated wells 0.48 -> 0.30, the untreated value)"),
    },
    controls=[Control("reassign_wells_to_treatment", ["C"], transform=_reassign_wells)],
)
