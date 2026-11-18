"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOTS = 10
N_QUADRATS = 30
N_FENCED = 5
OPEN_LOGIT = -0.85        # open-plot occupancy logit (mean occupancy about 0.32)
PLUS_FENCE_EFFECT = 1.5   # logit increase in fenced plots (mean occupancy about 0.64)
PLOT_SD = 0.5             # between-plot SD of the logit (shore position, substrate)
QUADRAT_SD = 0.7          # within-plot microhabitat SD of the logit
QUADRAT_RHO = 0.6         # correlation between neighbouring quadrats along the transect


def _simulate(rng, effect):
    p, q = N_PLOTS, N_QUADRATS
    exclosure = np.zeros(p, dtype=bool)
    exclosure[rng.choice(p, N_FENCED, replace=False)] = True
    plot_dev = PLOT_SD * rng.standard_normal(p)
    innov = rng.standard_normal((p, q))
    micro = np.empty((p, q))
    micro[:, 0] = QUADRAT_SD * innov[:, 0]
    step = QUADRAT_SD * np.sqrt(1.0 - QUADRAT_RHO ** 2)
    for t in range(1, q):
        micro[:, t] = QUADRAT_RHO * micro[:, t - 1] + step * innov[:, t]
    logit = OPEN_LOGIT + effect * exclosure[:, None] + plot_dev[:, None] + micro
    occupied = rng.random((p, q)) < 1.0 / (1.0 + np.exp(-logit))
    return {"occupied": np.asarray(occupied, dtype=bool), "exclosure": exclosure}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_FENCE_EFFECT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def _lgamma(x):
    c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028,
         771.32342877765313, -176.61502916214059, 12.507343278686905,
         -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)
    x = x - 1.0
    a = c[0]
    t = x + 7.5
    for i in range(1, 9):
        a = a + c[i] / (x + i)
    return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a)


def _betacf(a, b, x):
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 2000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h = h * d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        de = d * c
        h = h * de
        if abs(de - 1.0) < 1e-15:
            break
    return h


def _betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = (_lgamma(a + b) - _lgamma(a) - _lgamma(b)
           + a * np.log(x) + b * np.log(1.0 - x))
    bt = np.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * _betacf(a, b, x) / a)
    return float(1.0 - bt * _betacf(b, a, 1.0 - x) / b)


def _t_sf(t, df):
    t = float(t)
    df = float(df)
    if t == 0.0:
        return 0.5
    x = df / (df + t * t)
    p = 0.5 * _betainc(0.5 * df, 0.5, x)
    if t > 0.0:
        return p
    return 1.0 - p


def _welch(a, b):
    na = a.size
    nb = b.size
    va = a.var(ddof=1) / na
    vb = b.var(ddof=1) / nb
    se2 = va + vb
    if se2 <= 0.0:
        return None
    diff = a.mean() - b.mean()
    t = diff / np.sqrt(se2)
    df = se2 * se2 / (va * va / (na - 1) + vb * vb / (nb - 1))
    return float(diff), _t_sf(t, df)


def criterion(d):
    """Claim: mean occupancy is higher in fenced plots than in open plots by at
    least 0.10, where the occupancy of a plot is the fraction of its quadrats
    that are occupied, and a one-sided test of the difference between the mean
    occupancy of fenced plots and that of open plots is significant at the
    0.05 level.

    d['occupied']: bool array (plots, quadrats) = (10, 30); True if the species
        was present in that quadrat of that plot.
    d['exclosure']: bool array (plots,) = (10,); True if the plot was fenced
        against grazers.

    Returns True when the difference is >= 0.10 and the test is significant at
    the 0.05 level, False otherwise; None when a group has too few units for
    the test or the variance needed for the test is zero.
    """
    y = np.asarray(d['occupied'], dtype=float)
    g = np.asarray(d['exclosure'], dtype=bool)
    occ = y.mean(axis=1)
    a = occ[g]
    b = occ[~g]
    if a.size < 2 or b.size < 2:
        return None
    res = _welch(a, b)
    if res is None:
        return None
    return bool(res[0] >= 0.10 and res[1] < 0.05)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _reverse_exclosure(d, rng):
    return {**d, "exclosure": np.logical_not(d["exclosure"])}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="fence effect on the occupancy logit set from 1.5 to 0 (fenced plots have the open-plot occupancy distribution); between-plot, within-plot and spatial variation unchanged"),
    },
    controls=[Control("exclosure_labels_reversed", ["C"], transform=_reverse_exclosure)],
)
