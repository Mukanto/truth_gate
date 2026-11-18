"""D-056: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

G = 3
N = 25
MASS_MEAN = 300.0
MASS_SD_LOG = 0.25
MASS_STEP = 0.0875
VO2_MEAN = 10.0
EXPONENT = 0.67
VO2_SD_LOG = 0.10
GAMMA_PLUS = np.array([-0.03, 0.06, -0.03])


def _gen(rng, gamma):
    shift = MASS_STEP * np.array([-1.0, 0.0, 1.0])
    zm = rng.standard_normal((G, N))
    zv = rng.standard_normal((G, N))
    mass = MASS_MEAN * np.exp(shift[:, None] + MASS_SD_LOG * zm - 0.5 * MASS_SD_LOG ** 2)
    vo2 = VO2_MEAN * (mass / MASS_MEAN) ** EXPONENT * np.exp(gamma[:, None] + VO2_SD_LOG * zv)
    return {
        "oxygen_uptake": np.asarray(vo2, dtype=float),
        "body_mass": np.asarray(mass, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, GAMMA_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, np.zeros(G))


def _shuffle_groups(d, rng):
    u = np.asarray(d["oxygen_uptake"], dtype=float)
    m = np.asarray(d["body_mass"], dtype=float)
    idx = rng.permutation(u.size)
    return {
        "oxygen_uptake": u.reshape(-1)[idx].reshape(u.shape),
        "body_mass": m.reshape(-1)[idx].reshape(m.shape),
    }


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def lgam(z):
    c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
         -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
         1.5056327351493116e-7]
    z = z - 1.0
    s = c[0]
    for i in range(1, 9):
        s = s + c[i] / (z + i)
    t = z + 7.5
    return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(s)


def betacf(a, b, x):
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    dd = 1.0 - qab * x / qap
    if abs(dd) < tiny:
        dd = tiny
    dd = 1.0 / dd
    h = dd
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        h = h * dd * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        de = dd * c
        h = h * de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = np.exp(lgam(a + b) - lgam(a) - lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * betacf(a, b, x) / a)
    return float(1.0 - bt * betacf(b, a, 1.0 - x) / b)


def t_two_sided_p(t, df):
    return betainc(0.5 * df, 0.5, df / (df + t * t))


def f_upper_p(f, d1, d2):
    f = max(f, 0.0)
    return betainc(0.5 * d2, 0.5 * d1, d2 / (d2 + d1 * f))


def rss_of(X, y):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    return float(np.sum(res * res))


def nested_f_p(y, X0, X1):
    n = y.shape[0]
    d1 = X1.shape[1] - X0.shape[1]
    d2 = n - X1.shape[1]
    r0 = rss_of(X0, y)
    r1 = rss_of(X1, y)
    if r1 == 0.0:
        return None
    return f_upper_p(((r0 - r1) / d1) / (r1 / d2), d1, d2)


def criterion(d):
    """Claim: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05.

    d: dict of numpy arrays, with the keys
      oxygen_uptake  (groups, animals)  float: resting oxygen uptake of each rat in each group, in mL O2 per min
      body_mass  (groups, animals)  float: body mass of each rat in each group, in g

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    o2 = np.asarray(d['oxygen_uptake'], dtype=float)
    m = np.asarray(d['body_mass'], dtype=float)
    ng = o2.shape[0]
    na = o2.shape[1]
    n = ng * na
    if ng < 2 or na < 1 or n < 5:
        return None
    if not (np.all(np.isfinite(o2)) and np.all(np.isfinite(m))):
        return None
    dum = np.zeros((n, ng - 1))
    for i in range(1, ng):
        dum[i * na:(i + 1) * na, i - 1] = 1.0
    one = np.ones((n, 1))
    if np.ptp(m) == 0:
        return None
    y = o2.reshape(n)
    X0 = np.hstack([one, m.reshape(n, 1)])
    X1 = np.hstack([one, m.reshape(n, 1), dum])
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X0))):
        return None
    if np.ptp(y) == 0:
        return None
    p = nested_f_p(y, X0, X1)
    if p is None:
        return None
    return bool(p < 0.05)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


STUDY = Study(
    name="D-056",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="group effects on log oxygen uptake at equal body mass (-0.03, +0.06, -0.03) set to 0"),
    },
    controls=[Control("D-056", ["C"], transform=lambda d, rng: _shuffle_groups(d, rng))],
)
