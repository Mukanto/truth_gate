"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOTS = 10
N_QUADRATS = 30
N_FENCED = 5
MU_OPEN = 0.25
MU_FENCED = 0.70
MU_NULL = 0.475
CONC = 2.333


def _world(rng, mu_open, mu_fenced):
    fenced = np.zeros(N_PLOTS, dtype=bool)
    fenced[rng.permutation(N_PLOTS)[:N_FENCED]] = True
    mu = np.where(fenced, mu_fenced, mu_open)
    p = rng.beta(mu * CONC, (1.0 - mu) * CONC)
    occupied = rng.uniform(size=(N_PLOTS, N_QUADRATS)) < p[:, None]
    return {"occupied": occupied.astype(bool), "exclosure": fenced}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, MU_OPEN, MU_FENCED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, MU_NULL, MU_NULL)


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


def _break(d, rng):
    lab = np.asarray(d["exclosure"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"occupied": np.array(d["occupied"], dtype=bool), "exclosure": new}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="plot occupancy probability no longer depends on the exclosure (both arms at the pooled mean 0.475)"),
    },
    controls=[Control("D-012", ["C"], transform=lambda d, rng: _break(d, rng))],
)
